# layouts 
from dash import html, dcc

# Define styles
button_style2 = {
    'fontSize': '16px',
    'padding': '10px 20px',
    'marginRight': '10px'
}

# Define the layout
app_layout = html.Div([
    html.A(html.Button("Go to Home Page", className='Button', style=button_style2), href="/", target="_self"),
    html.Button('Clear', id='clear-screen-button', n_clicks=0, className='button', style=button_style2),
    html.Button("Download CSV", id="btn_csv", className='button', style=button_style2),
    html.Button("Config", id="config-button", n_clicks=0, className='button', style=button_style2),
    html.Button('Add Database', id='Add_db', className='button', style=button_style2),
    dcc.Download(id="download-dataframe-csv"),  # _self used to trigger full page reload
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    # Additional components can be added here
], style={'fontFamily': 'Times New Roman', 'padding': '40px'})