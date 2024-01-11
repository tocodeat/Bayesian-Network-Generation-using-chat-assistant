import json
import os
from io import StringIO

import pandas as pd
import numpy as np
import sqlite3

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, ALL, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from layout.index import index_layout
from layout.activity_pages import activity_layout
from layout.simulation import simulation_layout

from src.database import create_database, insert_activity_data
from src.engine import simulate_activity_durations, run_cpm_calculations, analyze_total_float, aggregate_cpm_results
from src.plot import create_network_graph
from src.llm import create_agent, save_conversation_history, initial_prompt

# ---------------------------------- Set up ---------------------------------- #

activities = {
    'a': 'Project Initiation',
    'b': 'Requirement Gathering',
    'c': 'System Design',
    'd': 'Database Development',
    'e': 'Backend Development',
    'f': 'UI/UX Design',
    'g': 'Frontend Development',
    'h': 'Integration',
    'i': 'User Training',
    'j': 'Testing',
    'k': 'Deployment',
    'l': 'Project Closure'
}

activities_dependencies = {
    'Project Initiation': [],
    'Requirement Gathering': ['Project Initiation'],
    'System Design': ['Requirement Gathering'],
    'Database Development': ['System Design'],
    'Backend Development': ['System Design'],
    'UI/UX Design': ['Requirement Gathering'],
    'Frontend Development': ['UI/UX Design'],
    'Integration': ['Backend Development', 'System Design'],
    'User Training': ['Integration'],
    'Testing': ['Integration'],
    'Deployment': ['User Training', 'Testing'],
    'Project Closure': ['Deployment']
}

activity_scores = {
    'Project Initiation': lambda p, c, t: 0.5 * p + 0.4 * c + 0.1 * t,
    'Requirement Gathering': lambda p, c, t: 0.6 * p + 0.2 * c + 0.2 * t,
    'System Design': lambda p, c, t: 0.3 * p + 0.4 * c + 0.3 * t,
    'Database Development': lambda p, c, t: 0.2 * p + 0.5 * c + 0.3 * t,
    'Backend Development': lambda p, c, t: 0.3 * p + 0.3 * c + 0.4 * t,
    'UI/UX Design': lambda p, c, t: 0.4 * p + 0.1 * c + 0.5 * t,
    'Frontend Development': lambda p, c, t: 0.3 * p + 0.1 * c + 0.6 * t,
    'Integration': lambda p, c, t: 0.2 * p + 0.3 * c + 0.5 * t,
    'User Training': lambda p, c, t: 0.7 * p + 0.2 * c + 0.1 * t,
    'Testing': lambda p, c, t: 0.3 * p + 0.4 * c + 0.3 * t,
    'Deployment': lambda p, c, t: 0.2 * p + 0.6 * c + 0.2 * t,
    'Project Closure': lambda p, c, t: 0.5 * p + 0.3 * c + 0.2 * t
}

app_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(app_dir, 'database')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = 'Software Implementation Project'

# ------------------------------ Layout callback ----------------------------- #

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Download(id='download-data'),
    dcc.Store(id='agent-store')
])

# Container for storing the LangChain agent for each activity
agents = {}

@app.callback(
    [Output('page-content', 'children'),
     Output('agent-store', 'data')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/simulation':
        page_content = simulation_layout(aggregated_cpm_results, 'column')
        agent_data = None
    elif pathname in [f'/{activity_code}' for activity_code in activities]:
        page_content = activity_layout(pathname[1:], activities[pathname[1:]])
        agent_id = str(pathname[1:])  # Using the activity code as the unique ID
        # Check if the agent has been initialized, otherwise initialize it
        if agent_id not in agents:
            agents[agent_id] = create_agent(api_key=os.environ['OPENAI_API_KEY'])
        agent_data = {'agent_id': agent_id}
    else:
        page_content = index_layout()
        agent_data = None
    
    return page_content, agent_data

# ----------------------------- Chatbot callback ----------------------------- #

@app.callback(
    [Output({'type': 'chat-output', 'index': ALL}, 'children'),
     Output({'type': 'conversation-store', 'index': ALL}, 'data')],
    [Input({'type': 'send-chat', 'index': ALL}, 'n_clicks')],
    [State({'type': 'chat-input', 'index': ALL}, 'value'),
     State('agent-store', 'data'),
     State({'type': 'conversation-store', 'index': ALL}, 'data')],
    prevent_initial_call=True
)
def handle_chat_interaction(n_clicks, chat_input, agent_data, conversation_data):
    ctx = callback_context

    if not ctx.triggered:
        return dash.no_update

    # Find the ID (activity key) of the button that triggered the callback
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    activity_key = json.loads(button_id)['index']

    # Generate the response using LangChain agent
    agent_executor = agents[agent_data['agent_id']]
    # Initial prompt
    if conversation_data[0] is None:
        response = agent_executor.invoke({'input': initial_prompt(activities[activity_key])})['output']
    # Subsequent prompts
    else:
        response = agent_executor.invoke({'input': chat_input[0]})['output']

    updated_conversation_data = conversation_data[0] if conversation_data[0] is not None else []
    updated_conversation_data.append({'user': chat_input[0], 'bot': response})
    
    # Only display the bot's response in the chat output
    return [f'{activities[activity_key]}: {response}'], [updated_conversation_data]

# ------------------------------ Slider callback ----------------------------- #

@app.callback(
    Output('save-message', 'children'), 
    [Input({'type': 'confirm-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'people-slider', 'index': ALL}, 'value'),
     State({'type': 'technology-slider', 'index': ALL}, 'value'),
     State({'type': 'cost-slider', 'index': ALL}, 'value'),
     State({'type': 'conversation-store', 'index': ALL}, 'data')],
    prevent_initial_call=True
)
def on_confirm_button_click(n_clicks, people_value, technology_value, cost_value, conversation_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    activity_code = json.loads(button_id)['index']
    activity_name = activities[activity_code]

    # Each of the values is a list with a single element
    insert_activity_data(os.path.join(database_path, 'project_data.db'), activity_name, people_value[0], technology_value[0], cost_value[0])
    
    # Save the conversation history to a text file
    print(conversation_data)
    if conversation_data is not None:
        save_conversation_history(database_path, activity_code, conversation_data[0])

    return f'Data for {activity_name} saved successfully for people={people_value}, technology={technology_value}, cost={cost_value}'

# ---------------------------- Simulation callback --------------------------- #

@app.callback(
    Output('url', 'pathname'),
    [Input('run-simulation-button', 'n_clicks')],
    prevent_initial_call=True
)
def run_simulation(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    resource_data = pd.read_sql_query('SELECT * FROM activity_data', sqlite3.connect(os.path.join(database_path, 'project_data.db')))

    # Simulate the activity durations
    simulation_results, original_durations = simulate_activity_durations(resource_data=resource_data, activity_scores=activity_scores, num_simulations=10)
    
    # Run the CPM calculations for each simulation
    cpm_results = run_cpm_calculations(activity_dependencies=activities_dependencies, simulation_results=simulation_results, num_simulations=10)
    
    # Calculate the counts of zero total float for each activity
    total_float_results = analyze_total_float(cpm_results=cpm_results)
    
    # Calculate summary statistics for each activity
    global aggregated_cpm_results
    aggregated_cpm_results = aggregate_cpm_results(cpm_results, original_durations).to_json(date_format='iso', orient='split')
    
    graph_file_path = os.path.join(app_dir, 'assets', 'network_graph.html')
    create_network_graph(activities_dependencies, total_float_results, graph_file_path)

    return '/simulation'

# ----------------------------- Download callback ---------------------------- #

@app.callback(
    Output('download-data', 'data'),
    [Input('download-button', 'n_clicks')],
    prevent_initial_call=True
)
def generate_download_link(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    data = pd.read_json(StringIO(aggregated_cpm_results), orient='split')

    return dcc.send_data_frame(data.to_csv, 'aggregated_cpm_results.csv', index=False)

if __name__ == '__main__':
    
    create_database(db_path=os.path.join(database_path, 'project_data.db')) 
    app.run_server(debug=True)