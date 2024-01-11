from dash import html, dcc
import dash_bootstrap_components as dbc

activities = {
    'a': "Project Initiation",
    'b': "Requirement Gathering",
    'c': "System Design",
    'd': "Database Development",
    'e': "Backend Development",
    'f': "UI/UX Design",
    'g': "Frontend Development",
    'h': "Integration",
    'i': "User Training",
    'j': "Testing",
    'k': "Deployment",
    'l': "Project Closure"
}

activity_descriptions = {
    'a': "Setting the project's scope, objectives, and key stakeholders to ensure a clear start.",
    'b': "Collecting detailed requirements from stakeholders to guide project design and development.",
    'c': "Designing the overall system architecture, including hardware and software components.",
    'd': "Developing and structuring the necessary databases for the project's data storage needs.",
    'e': "Focusing on the server-side development to ensure robust and scalable backend solutions.",
    'f': "Creating the user interface and user experience designs for an intuitive and appealing product.",
    'g': "Building the client-side of the application, focusing on responsive and interactive features.",
    'h': "Combining all developed components into a single, functional system.",
    'i': "Providing training to users, ensuring they can effectively utilize the new system.",
    'j': "Thoroughly testing the system to identify and resolve any issues before deployment.",
    'k': "Deploying the final product to a live environment, making it accessible to end-users.",
    'l': "Concluding the project with a formal closure process, including documentation and handover."
}

def index_layout() -> dbc.Container:
    """
    Create the layout for the index page.
    
    Returns
    -------
    dbc.Container
        The layout for the index page. 
    """
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1('Software Implementation Project', className='display-3'),
                    html.P('Select an activity to view its details and input the data. When you are ready:', className='lead'),
                    html.Hr(className='my-2'),
                    dbc.Button('Run Simulation', id='run-simulation-button', color='success', className='mb-4')  
                ])
            ], className='text-center'),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader(activities[activity]),
                    dbc.CardBody([
                        html.P(activity_descriptions[activity])
                    ]),
                    dbc.CardFooter(dbc.Button('View Details', href=f'/{activity}', color='primary')),
                ], className='mb-3'), width=12, sm=6, md=4, lg=3)  # Adjust the width for different screen sizes
                for activity in activities
            ], className='g-4')  # Use 'g-4' to add some spacing between cards
        ])
    ])