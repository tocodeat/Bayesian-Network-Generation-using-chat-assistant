from typing import List
from io import StringIO
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd

def create_header() -> dbc.Row:
    """
    Create a header row for the simulation layout.

    Returns
    -------
    dbc.Row
        A Dash Bootstrap Components Row containing the header.
    """
    return dbc.Row([
        dbc.Col(html.H2('Critical Paths', className='text-center mb-4'), width=12)
    ])

def create_network_graph() -> dbc.Row:
    """
    Create a row containing an iframe for the network graph.

    Returns
    -------
    dbc.Row
        A Dash Bootstrap Components Row containing an iframe.
    """
    return dbc.Row([
        dbc.Col(html.Iframe(src='/assets/network_graph.html', width='100%', height='500px'), width=12)
    ])

def create_table(aggregated_cpm_results: pd.DataFrame) -> dash_table.DataTable:
    """
    Create a data table from aggregated CPM results.

    Parameters
    ----------
    aggregated_cpm_results : pd.DataFrame
        The aggregated CPM results to be displayed in the table.

    Returns
    -------
    dash_table.DataTable
        A Dash DataTable component displaying the CPM results.
    """
    return dash_table.DataTable(
        id='cpm-results-table',
        columns=[
            {'name': i, 'id': i, 'type': 'numeric', 'format': dash_table.Format.Format(precision=0, scheme=dash_table.Format.Scheme.fixed)} 
            if aggregated_cpm_results[i].dtype in ['float64', 'int64'] else {'name': i, 'id': i}
            for i in aggregated_cpm_results.columns
        ],
        data=aggregated_cpm_results.to_dict('records'),
        editable=True,
        style_table={'overflowX': 'auto'}, 
        style_cell={'textAlign': 'center', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        style_data={'textAlign': 'center'},
        style_as_list_view=True,
        sort_action='native',
        sort_mode='multi',
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Max Delay} = 0',
                    'column_id': 'Max Delay'
                },
                'backgroundColor': '#c53d46',
                'color': 'white'
            },
            {
                'if': {
                    'filter_query': '{Max Delay} > 0',  
                    'column_id': 'Max Delay'
                },
                'backgroundColor': '#90EE90'
            }
        ]
    )

def create_table_description() -> html.P:
    """
    Create a paragraph describing the data table.

    Returns
    -------
    html.P
        A Dash HTML Paragraph component.
    """
    return html.P('This table displays summary statistics for across multiple simulations, providing insights into the criticality of each project activity.', className='text-center mt-4 mb-2')

def create_download_button() -> html.Div:
    """
    Create a download button for exporting the data table.

    Returns
    -------
    html.Div
        A Dash HTML Div component containing the download button
    """
    return html.Div(
        dbc.Button('Download CSV', id='download-button', color='primary', className='mt-2 mb-4'),
        style={'display': 'flex', 'justify-content': 'center'}
    )

def simulation_layout(aggregated_cpm_results: str, layout_type: str) -> dbc.Container:
    """
    Create the layout for the simulation results page.

    Parameters
    ----------
    aggregated_cpm_results : str
        JSON string containing the aggregated CPM results.
    layout_type : str
        The type of layout to use ('row' or 'column').

    Returns
    -------
    dbc.Container
        The container with the simulation layout based on the specified type.
    """
    aggregated_cpm_results_df = pd.read_json(StringIO(aggregated_cpm_results), orient='split') if aggregated_cpm_results else pd.DataFrame()
    table = create_table(aggregated_cpm_results_df)
    header = create_header()
    network_graph = create_network_graph()
    table_description = create_table_description()
    download_button = create_download_button()

    if layout_type == 'row':
        return dbc.Container([
            header,
            network_graph,
            dbc.Row([
                dbc.Col(table_description, width={'size': 10, 'offset': 1})
            ]),
            dbc.Row([
                dbc.Col(download_button, width={'size': 4, 'offset': 4})
            ]),
            dbc.Row(
                dbc.Col(table, width={'size': 10, 'offset': 1}),
                justify='center',
            ),
            dbc.Row([
                dbc.Col(dbc.Button('Back to Home', href='/', color='secondary', className='mt-4 mb-4'), width=12, className='text-center')
            ])
        ])
    elif layout_type == 'column':
        return dbc.Container([
            header,
            dbc.Row([
                dbc.Col(network_graph, md=6),
                dbc.Col([table_description, table, download_button], md=6)
            ], align='center'),
            dbc.Row([
                dbc.Col(dbc.Button('Back to Home', href='/', color='secondary', className='mt-4 mb-4'), width=12, className='text-center')
            ])
        ])