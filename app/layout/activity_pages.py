from dash import html, dcc
import dash_bootstrap_components as dbc

def create_slider(id: str, activity_code: str) -> dcc.Slider:
    """
    Create a slider with the given ID and activity code.
    
    Parameters
    ----------
    id : str
        ID of the slider.
    activity_code : str
        Activity code of the slider. 
        
    Returns
    -------
    dcc.Slider
        The slider for the given ID and activity code.
    """
    slider = dcc.Slider(
        id={'type': id, 'index': activity_code},
        min=0, 
        max=100, 
        step=1, 
        value=50, 
        tooltip={'placement': 'bottom', 'always_visible': True},
        marks={i: str(i) for i in [0, 25, 50, 75, 100]}
    )
    
    return slider
    

def activity_layout(activity_code: str, activity_name: str) -> dbc.Container:
    """
    Create the layout for the activity page.
    
    Parameters
    ----------
    activity_code : str
        Activity code of the activity.
    activity_name : str
        Name of the activity.
        
    Returns
    -------
    dbc.Container
        The layout for the activity page.
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1(activity_name, className='display-4'),
                html.Hr(),
                dbc.Label('People:'),
                create_slider('people-slider', activity_code),
                dbc.Label('Technology:'),
                create_slider('technology-slider', activity_code),
                dbc.Label('Cost:'),
                create_slider('cost-slider', activity_code),
                html.Div(id={'type': 'slider-output', 'index': activity_code}, className='slider-output'),  # Slider output
                html.Hr(),
                dbc.Label('Chat with your AI assistant:'),
                dcc.Textarea(id={'type': 'chat-input', 'index': activity_code}, style={'width': '100%', 'height': 100}),
                dbc.Button('Send', id={'type': 'send-chat', 'index': activity_code}, color='primary', className='my-2'),
                html.Div(id={'type': 'chat-output', 'index': activity_code}, className='chat-output'),
                html.Hr(),
                dbc.Button('Confirm', id={'type': 'confirm-button', 'index': activity_code}, color='success', className='my-2'),
                dcc.Link('Go back to homepage', href='/', className='btn btn-secondary my-2'),
                html.Hr(),
                html.Div(id='save-message'),
                dcc.Store(id={'type': 'conversation-store', 'index': activity_code})
            ])
        ])
    ])