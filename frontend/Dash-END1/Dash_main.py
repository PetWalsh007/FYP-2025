'''
This file is the main Dash front end file for the system. It is responsible for the main layout of the Dash portion of the system.

https://dash.plotly.com/ for more information on Dash and how the Dash framework works

'''

import dash
from flask import request, g
from dash import dcc, dash_table
from dash import html
from dash.dependencies import Input, Output, State
import requests
import pandas as pd
import json
import subprocess
import time
import random
import plotly.express as px
from datetime import date
import logging
import redis as rd

import layouts

logging.basicConfig(filename="dash_main.log", level=logging.INFO, format="%(asctime)s - %(message)s")



# Load the existing config
CONFIG_FILE = "config.json"
# global dataframe for data to plot 
dataframe = pd.DataFrame()

def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        return {}

def save_config(config_data):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)


def load_config_call():
    global CONFIG
    CONFIG = load_config()


def pull_config_data():
    # function to pull the updated config data from the server db 

    # send a request to the abstraction layer /healthcheck endpoint to see if tis active 
    # if it is active then send a request to the abstraction layer /config endpoint to get the config data



    config_local = load_config()
    config_server = None


    try:
        response = requests.get(f"http://{CONFIG['endpoints']['db-connection-layer']['ip']}:{CONFIG['endpoints']['db-connection-layer']['port']}/healthcheck")
        if response.status_code == 200:
            logging.info("Abstraction layer is active")
          
    except Exception as e:
        logging.error(f"Error connecting to abstraction layer: {e}")
        return None

    try:
        response = requests.get(f"http://{CONFIG['endpoints']['db-connection-layer']['ip']}:{CONFIG['endpoints']['db-connection-layer']['port']}/config")
        if response.status_code == 200:
            config_server = response.json()
            # if error in response then log the error and return None
            if 'error' in config_server:
                logging.error(f"Error pulling config data from server: {config_server['error']}")
                return None
            logging.info("Config data pulled from server")
        else:
            logging.error(f"Error pulling config data from server: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error connecting to abstraction layer: {e}")
        return None

    # comparing local config with server config and updating local config with server config

    try:
        # Extracting the "endpoints" section from both configurations
        local_endpoints = config_local.get("endpoints", {})
        server_endpoints = config_server.get("endpoints", {})

        # Compare and update the local endpoints with server endpoints
        for key, server_endpoint in server_endpoints.items():
            if key not in local_endpoints or local_endpoints[key] != server_endpoint:
                logging.info(f"Updating endpoint '{key}' in local config with server data.")
                local_endpoints[key] = server_endpoint

        # Save the updated endpoints back to the local configuration
        config_local["endpoints"] = local_endpoints

        # Save the updated local configuration to the config file
        save_config(config_local)
        logging.info("Local configuration updated successfully with server data.")

    except Exception as e:
        logging.error(f"Error updating local config with server data: {e}")


    pass







def app_startup_routine():
    logging.info("App started")
    load_config_call()

    pull_config_data()

    load_config_call()

    






# routes pathname added for testing 
try:
    app = dash.Dash(__name__, requests_pathname_prefix='/dash/')
    app.title = 'RTA MES'
    server = app.server  # Expose the Flask server for Gunicorn

except Exception as e:
    logging.error(f"Error initializing Dash app: {e}")
    


app_startup_routine()  # Call the startup routine to load the config and log the startup
     

@app.server.before_request
def capture_client_ip():
    excluded_paths = [
        "/_dash-layout", "/_dash-dependencies", "/_dash-update-component",
        "/_dash-component-suites", "/favicon.ico"
    ]

    # Skip logging for these paths - startup dash calls
    if any(request.path.startswith(path) for path in excluded_paths):
        return

    g.client_ip = request.headers.get("X-Real-IP", request.remote_addr)
    logging.info(f"Client IP: {g.client_ip} - Method: {request.method} - Path: {request.path}")


@app.callback(
    Output('client-ip-store', 'data'),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def store_client_ip(_):
    ip = request.headers.get("X-Real-IP", request.remote_addr)
    logging.info(f"Storing client IP to dcc.Store: {ip}")
    return ip


def connect_redis():
    
    redis_host = CONFIG['endpoints']['redis-memory-store']['ip']
    redis_port = CONFIG['endpoints']['redis-memory-store']['port']
    global redis_client
    try:
        redis_client = rd.StrictRedis(host=redis_host, port=redis_port, db=0)
        redis_client.ping()
        logging.info("Connected to Redis server successfully.")
        
    except rd.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")
        redis_client = None
        return None
    

connect_redis()  # Connect to Redis server at the start of the app

try:
    if redis_client is None:
        t=5
        logging.error("Failed to connect to Redis server. Retrying...")
        while t < 30:
            time.sleep(t)
            connect_redis()  # Retry connecting to Redis server
            if redis_client:
                logging.info("Connected to Redis server successfully after retry.")
                break
            t += 5
            logging.error(f"Retrying to connect to Redis server {CONFIG['endpoints']['redis-memory-store']['ip']}...")
        if redis_client is None:
            logging.error(f"Failed to connect to Redis server {CONFIG['endpoints']['redis-memory-store']['ip']} after retrying....")
            raise ConnectionError("Could not connect to Redis server. Exiting...")
except Exception as e:
    logging.error(f"Error connecting to Redis server: {e}")
    raise ConnectionError("Could not connect to Redis server. Exiting...")    
    

dev_style = {
    'textAlign': 'center',
    'color': '#1F7BEF',
    'fontSize': '36px',
    'fontWeight': 'bold',
    'marginBottom': '20px'
}

button_style = {
    'textAlign': 'center',
    'marginBottom': '20px',
    'marginTop': '20px',
    'display': 'flex',
    'justifyContent': 'center'
}

button_style2 = {
    'fontSize': '16px',
    'padding': '10px 20px',
    'marginRight': '10px'
}

text_style1 = { 
    'textAlign': 'center',
    'marginBottom': '20px',
    'marginTop': '20px',
    'display': 'flex',
    'justifyContent': 'center',
    'fontSize': '18px',
    'color': '#303'
}
text_style2 = { 
    'textAlign': 'left',
    'marginBottom': '20px',
    'marginTop': '20px',
    'display': 'flex',
    'justifyContent': 'left',
    'fontSize': '25px',
    'color': '#000'
}

# Define the layout of the Dash app 
app.layout = layouts.app_layout




# Define the layout for the main page
# https://dash.plotly.com/dash-html-components for more information on the HTML components
# https://dash.plotly.com/dash-core-components for more information on the DCC's
# https://dash.plotly.com/datatable for more information on the DataTable component used 
# https://dash.plotly.com/dash-core-components/graph for more information on the Graph component used
# https://plotly.com/ For more information on Plotty - Used for graphing

# Updated 08/02 to a function to allow for easier testing of dynamic content in dropdown from JSON config
# Updated 16/02 to add date picker range dcc and also update to begin in browser storage of multiple dataframe ahead of backend work
def main_page_layout():
    return html.Div([
        html.Div(className='row', children='Real-Time Adaptive Data Analytics and Visualisation Platform for Industrial Manufacturing Execution Systems',
                style=dev_style),
        html.Div([
            html.Label('Select the database to query:', style={'fontSize': '18px', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='database',
                options=CONFIG.get("database_options", []),
                value='postgres',
                style={'fontSize': '18px', 'width': '170px', 'marginRight': '10px'}
            ),
            dcc.Dropdown(
                id="table_name",
                options = [
                    {"label": f"{db_info['label']} - {table}", "value": table}
                    for db_info in CONFIG["database_options"]
                    for table in db_info.get("tables", [])
                ],
                value=None,
                placeholder="Select a Table",
                style={'fontSize': '18px', 'width': '400px',  'marginRight': '10px', 'whiteSpace': 'normal'    
                }, # https://www.w3schools.com/cssref/pr_text_white-space.php

            ),
            dcc.DatePickerRange(
                id='data-date-range',
                display_format='DD/MM/YYYY',
                initial_visible_month=date.today(),
                style={'fontSize': '16px', 'marginRight': '10px'}
            ),
             html.Button('Get Raw Data', id='get-all-data-button', n_clicks=0, className='button', style=button_style2),
                    ], style={'textAlign': 'center', 'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'}),
            html.Div([
            dcc.Input(id='redis-key-for-proc', type='text', placeholder="Enter Raw Data Key", style={'marginRight': '10px', 'fontSize': '16px', 'padding': '5px'}),
            dcc.Dropdown(
                id='analysis-type',
                options=CONFIG.get("analytics", []),
                placeholder="Select Analysis Type",
                style={'fontSize': '12px', 'width': '200px', 'marginRight': '10px'}
            ),
            html.Button('Process Data', id='process-data', n_clicks=0, className='button', style=button_style2),
           

        ], style={'textAlign': 'center', 'marginBottom': '20px', 'marginTop': '20px', 'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '10px'}),

        # https://dash.plotly.com/dash-html-components 
        # https://www.w3.org/TR/css-grid-3/
        # https://www.w3schools.com/css/css_grid.asp
        # https://community.plotly.com/t/using-css-grid-with-dash/29018
        # 

        html.Div([
           html.Div([html.Label("Stored Raw Data Keys from this Session:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                     html.Div(id="available-keys-container", style={'marginBottom': '10px', 'textAlign': 'center', 'display': 'grid', 'gap': '10px'}),


                    html.Label("Enter Redis Key to Retrieve Data:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    dcc.Input(id='redis-key-entry', type='text', placeholder="Enter Redis Key", style={'marginRight': '10px', 'fontSize': '16px', 'padding': '5px'}),

                    html.Button("Retrieve Data from Redis", id="fetch-from-redis-button", n_clicks=0, className='button', style=button_style),

                    # Hidden store to keep track of Redis keys
                    dcc.Store(id='redis-key-store', data=[], storage_type='session'),  
                    ],style={'flex': '1', 'marginTop': '20px', 'textAlign': 'left', 'padding': '20px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'backgroundColor': '#ededed  '}),

            html.Div([
                    html.Label("Stored Processed Data Keys from this Session:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    html.Div(id="available-processed-keys-container", style={'marginBottom': '10px', 'textAlign': 'center'}),

                    html.Label("Enter Processed Data Key to Retrieve Data:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    dcc.Input(id='processed-key-entry', type='text', placeholder="Enter Processed Data Key", style={'marginRight': '10px', 'fontSize': '16px', 'padding': '5px'}),

                    html.Button("Retrieve Processed Data from Redis", id="fetch-processed-from-redis-button", n_clicks=0, className='button', style=button_style),

                    # Hidden store to keep track of Processed Data Redis keys
                    dcc.Store(id='processed-key-store', data=[], storage_type='session'),
                    ], style={'flex': '1', 'marginTop': '20px', 'textAlign': 'left', 'padding': '20px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'backgroundColor': '#ededed '}),

                ], style={'display': 'flex', 'gap': '20px'}),
        # html.Div([
        #     html.Label("Select Data Store:"),
            
        #     dcc.RadioItems(
        #         id="store-selector",
        #         options=[
        #             {"label": html.Span("Store 1", id="store-1-label"), "value": "dataframe-store-1"},
        #             {"label": html.Span("Store 2", id="store-2-label"), "value": "dataframe-store-2"},
        #             {"label": html.Span("Store 3", id="store-3-label"), "value": "dataframe-store-3"},
        #         ],
        #         value="dataframe-store-1",
        #         labelStyle={'display': 'inline-block', 'marginRight': '10px'}
        #     ),
        # ], style={'textAlign': 'center', 'marginBottom': '20px', 'display': 'flex', 'justifyContent': 'center'}),

        

        html.Div(id='output-container', style=text_style2),

        html.Div([
            dcc.Dropdown(id="x-axis-dropdown", placeholder="Select X-Axis", style={'width': '250px'}),
            dcc.Dropdown(id="y-axis-dropdown", multi=True, placeholder="Select Y-Axis", style={'width': '350px'}),
            dcc.Dropdown(id='Graph-type', options=[{'label': 'Scatter', 'value': 'scatter'}, {'label': 'Line', 'value': 'line'},
                                                   {'label': 'Bar', 'value': 'bar'}, {'label': 'Box', 'value': 'box'},
                                                    {'label': 'Histogram', 'value': 'histogram'},
                                                    {'label': 'Pie', 'value': 'pie'},
                                                   ], value='Pie', style={'width': '150px'}),
        ], style={'display': 'flex', 'gap': '10px', 'margin': '20px'}),

        dcc.Graph(id="data-plot"),  

        html.Div([dash_table.DataTable(
                                        id="data-table",
                                        columns=[],  # Columns 
                                        data=[],  # defualt empty data
                                        filter_action="native",
                                        sort_action="native",
                                        page_size=50  
                                        )
                ], style={'marginTop': '20px'}),
        dcc.Store(id='store', data={'get_data_clicks': 0, 'get_all_data_clicks': 0, 'onscreen_data':[]}, storage_type='session'),  # Store to keep track of click counts // onscreen data
    ])


page2_layout = html.Div([
    html.H1("Edit Config File"),
    
    html.P("Warning: Editing the config file may cause the system to stop working. Ensure Backup has been taken", style={'color': 'red'}),
    
    dcc.Textarea(
        id='config-textarea',
        value=json.dumps(CONFIG, indent=4),
        style={'width': '100%', 'height': 300},
    ),
    dcc.ConfirmDialog(
        id='confirm-danger',
       message='This will restart the server for all users! If you continue, Please wait for confirmation message.',
    ),
    dcc.ConfirmDialog(
        id='confirm-danger-dbs',
       message='This will restart the database connections for all users! If you continue, Please wait for confirmation message.',
    ),
    html.Button('Save Config File to Server', id='save-config-button', n_clicks=0),
    html.Button('Restart Dash Server', id='restart-system-button', n_clicks=0),
    html.Button('Restart DB Connections', id='restart-db-connections-button', n_clicks=0),
    html.Div(id='restart-confirmation', style={'marginTop': '20px'}),
    html.Div(id='restart-dbs-confirmation', style={'marginTop': '20px'}),
    html.Div(id='save-confirmation', style={'marginTop': '20px'}),
    html.A(
    html.Button('Go back to main page Dash', style={'fontSize': '16px', 'padding': '10px 20px'}),
    href='/dash/',
    target='_self')
    
])


# dev page for adding new databases to postgres - palceholder

#  - endpoint_name, endpoint_type, endpoint_ip, endpoint_port, driver_name, connection_uname, connection_password, metadata (defualt {time_col_name:"time"}), is_active defualt true

page_3_layout = html.Div([
    html.H1("Add Database Configuration", style={'textAlign': 'center'}),

    html.Label("Endpoint Name:", style={'fontSize': '16px'}),
    dcc.Input(id='endpoint-name', type='text', placeholder="Enter endpoint name", style={'marginBottom': '10px', 'width': '100%'}),
    html.Label("Endpoint Type:", style={'fontSize': '16px'}),
    dcc.Input(id='endpoint-type', type='text', placeholder="Enter endpoint type (e.g., PostgreSQL)", style={'marginBottom': '10px', 'width': '100%'}),
    html.Label("Endpoint IP:", style={'fontSize': '16px'}),
    dcc.Input(id='endpoint-ip', type='text', placeholder="Enter endpoint IP", style={'marginBottom': '10px', 'width': '100%'}),
    html.Label("Endpoint Port:", style={'fontSize': '16px'}),
    dcc.Input(id='endpoint-port', type='number', placeholder="Enter endpoint port", style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Driver Name:", style={'fontSize': '16px'}),
    dcc.Input(id='driver-name', type='text', placeholder="Enter driver name", style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Database Name:", style={'fontSize': '16px'}),
    dcc.Input(id='database-name', type='text', placeholder="Enter database name", style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Connection Username:", style={'fontSize': '16px'}),
    dcc.Input(id='connection-uname', type='text', placeholder="Enter connection username", style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Connection Password:", style={'fontSize': '16px'}),
    dcc.Input(id='connection-password', type='password', placeholder="Enter connection password", style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Metadata (default: {time_col_name: 'time'}):", style={'fontSize': '16px'}),
    dcc.Input(id='metadata', type='text', placeholder="Enter metadata (JSON format)", value='{"time_col_name": "time"}', style={'marginBottom': '10px', 'width': '100%'}),

    html.Label("Is Active (default: true):", style={'fontSize': '16px'}),
    dcc.Dropdown(
        id='is-active',
        options=[
            {'label': 'True', 'value': True},
            {'label': 'False', 'value': False},
        ],
        value=True,
        style={'marginBottom': '10px', 'width': '100%'}
    ),

    html.Button('Add Database', id='update-db-button', n_clicks=0, style={'marginTop': '20px', 'fontSize': '16px', 'padding': '10px 20px'}),
    html.Div(id='update-db-confirmation', style={'marginTop': '20px', 'fontSize': '16px', 'color': 'green'}),
    html.A( html.Button('Go back to main page Dash', style={'fontSize': '16px', 'padding': '10px 20px'}),
    href='/dash/',
    target='_self')
    ]
    )

@app.callback(
    Output('update-db-confirmation', 'children'),
    [Input('update-db-button', 'n_clicks')],
    [
        State('endpoint-name', 'value'),
        State('endpoint-type', 'value'),
        State('endpoint-ip', 'value'),
        State('endpoint-port', 'value'),
        State('driver-name', 'value'),
        State('database-name', 'value'),
        State('connection-uname', 'value'),
        State('connection-password', 'value'),
        State('metadata', 'value'),
        State('is-active', 'value'),
    ]
)
def update_database(n_clicks, endpoint_name, endpoint_type, endpoint_ip, endpoint_port, driver_name, db_name ,connection_uname, connection_password, metadata, is_active):
    if n_clicks > 0:
        try:
            # Load the current config
            ctx = dash.callback_context
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Update the database configuration
            new_db_config = {
                "endpoint_name": endpoint_name,
                "endpoint_type": endpoint_type,
                "endpoint_ip": endpoint_ip,
                "endpoint_port": endpoint_port,
                "driver_name": driver_name,
                "database_name": endpoint_name,
                "connection_uname": connection_uname,
                "connection_password": connection_password,
                "metadata": json.loads(metadata),
                "is_active": is_active,
            }
            
            if button_id == 'update-db-button':
                # send data here to endpoint to send to server db 
                logging.info(f"Updating database configuration")
                reply = send_data_to_server(new_db_config)  # Send data to server
                
                pass 

            return reply
        except Exception as e:
            logging.error(f"Error updating database: {e}")
            return f"Error updating database: {e}"

    return dash.no_update


def send_data_to_server(data):
    # data is a dictionary containing the data to be sent to the server - can we the full dictionay to the backend for it to unpack 
    response = requests.post(f"http://{CONFIG['endpoints']['db-connection-layer']['ip']}:{CONFIG['endpoints']['db-connection-layer']['port']}/add_database_connection", json=data)
    logging.info(f"Sending data to server: {data}")
    message = response.json().get('message', 'No message returned')
    return f"Message From Server: {message}"












# https://dash.plotly.com/dash-core-components/confirmdialog for more information on the ConfirmDialog component






@app.callback(
    Output('confirm-danger-dbs', 'displayed'),
    [Input('restart-db-connections-button', 'n_clicks')]
)
def restart_dbs_confirm(n_clicks):
    if n_clicks > 0:
        # Command to restart the database connections
        return True
       
    return ''

@app.callback(
    Output('restart-dbs-confirmation', 'children'),
    [Input('confirm-danger-dbs', 'submit_n_clicks')]
)
def restart_server_dbs(submit_n_clicks):
    if submit_n_clicks:
        endpoint_ip = CONFIG['endpoints']['db-connection-layer']['ip']
        endpoint_port = CONFIG['endpoints']['db-connection-layer']['port']
        response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/command?rst=restart_server_main_abstraction')
        time.sleep(2) # for a wait time to allow the server to restart
        # extract message from response
        if response.status_code == 200:
            message = response.json().get('message', 'No message returned')
            return f"Message From Server: {message}"
    return ''


@app.callback(
    Output('confirm-danger', 'displayed'),
    [Input('restart-system-button', 'n_clicks')]
)
def restart_server_confirm(n_clicks):
    if n_clicks > 0:
        # Command to restart the server
        return True
       
    return ''

@app.callback(
    Output('restart-confirmation', 'children'),
    [Input('confirm-danger', 'submit_n_clicks')]
)
def restart_server(submit_n_clicks):
    if submit_n_clicks:
        subprocess.Popen(["sudo", "systemctl", "restart", "gunicorn"])
        time.sleep(2) # for a wait time to allow the server to restart
        return 'Server restarted successfully!'

    return ''


@app.callback(
    Output('save-confirmation', 'children'),
    [Input('save-config-button', 'n_clicks')],
    [State('config-textarea', 'value')]
)
def save_config_file(n_clicks, config_text):
    if n_clicks > 0:
        config_data = json.loads(config_text)
        save_config(config_data)
        # reload the config into config global variable
        load_config_call()
        return 'Config file saved successfully!'
    return ''



# This callback is used to update the textarea with the current configuration data 
@app.callback(
    Output('config-textarea', 'value'),
    [Input('url', 'pathname')]
)
def update_config_textarea(pathname):
    if pathname == '/dash/page2':  
        return json.dumps(load_config(), indent=4)
    return dash.no_update

# this call back is used to change the page layout based on the URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/dash/page2':
        return page2_layout
    elif pathname == '/dash/page3':
        return page_3_layout
    return main_page_layout()


# Deprecated - This callback is used to update the colour of the store labels based on the data in the stores - no longer used
"""

@app.callback(
    [Output("store-1-label", "style"),
     Output("store-2-label", "style"),
     Output("store-3-label", "style")],
    [Input("dataframe-store-1", "data"),
     Input("dataframe-store-2", "data"),
     Input("dataframe-store-3", "data")],
    prevent_initial_call=True
)
def update_store_colours(store1, store2, store3):

    logging.info(f'In the Update Store Colours Callback')
    try:
        
        logging.info(f'In the Update Store Colours Callback - 2')
        return get_style(store1), get_style(store2), get_style(store3)

    except Exception as e:
        logging.error(f"Error in update_store_colours: {e}")
        return {}, {}, {}


def get_style(data):
    try:
        logging.info(f'In the get_style function')
        has_data = {'color': 'black', 'fontWeight': 'bold', 'backgroundColor': '#DFF2BF', 'padding': '3px 6px', 'borderRadius': '5px'}
        no_data = {'color': 'blue', 'fontWeight': 'normal', 'backgroundColor': '#FFBABA', 'padding': '3px 6px', 'borderRadius': '5px'}
        if data is None:
            logging.info('Here in get_style: data is None --- 1 ')
            return no_data
        if data:
            logging.info('Here in get_style: data is populated')
            return has_data
        logging.info('Here in get_style: data is None')
        return no_data
    except Exception as e:
        logging.error(f"Error in get_style: {e}")
        return  {'color': 'blue', 'fontWeight': 'normal', 'backgroundColor': '#FFBABA', 'padding': '3px 6px', 'borderRadius': '5px'}
"""     




# Serves as the callback function for the Dash app to update the content of the output containers
@app.callback(
    [Output('output-container', 'children'),
     Output('data-table', 'columns'),  
     Output('data-table', 'data'),  
     Output('store', 'data'),  # Store data for visualization
     Output('redis-key-store', 'data'),  # Store Redis keys
     Output('available-keys-container', 'children'),  # Show Redis keys
     Output('processed-key-store', 'data'),  # Store Processed Data keys
     Output('available-processed-keys-container', 'children'),  # Show Processed Data keys
     Output('url', 'pathname'),
     Output('download-dataframe-csv', 'data'),
     Output('x-axis-dropdown', 'options'),  # Populate X-axis dropdown
     Output('y-axis-dropdown', 'options')],  # Populate Y-axis dropdown (numeric)
    [Input('clear-screen-button', 'n_clicks'),
     Input('get-all-data-button', 'n_clicks'),
     Input('fetch-from-redis-button', 'n_clicks'),
     Input('fetch-processed-from-redis-button', 'n_clicks'),
     Input('data-date-range', 'start_date'),
     Input('data-date-range', 'end_date'),
     Input('process-data', 'n_clicks'),
     #Input('data-points', 'value'),
     Input('database', 'value'),
     Input('table_name', 'value'),
     Input("btn_csv", "n_clicks"),
     Input("config-button", "n_clicks"),
     Input('Add_db', 'n_clicks'),
     Input('url', 'pathname'),
     Input('analysis-type', 'value')],
    [State('store', 'data'),
     State('redis-key-store', 'data'),
     State('redis-key-entry', 'value'),
     State('processed-key-store', 'data'),
     State('processed-key-entry', 'value'),
     State('redis-key-for-proc', 'value'),
     State('client-ip-store', 'data')],
    prevent_initial_call=True
)
def update_output(clear_btn, get_data_btn, fetch_data_btn, fetch_processed_data_btn, st_date, end_date, process_btn,
                   db_sel, tbl_sel, download_cts, config_button, db_add_button ,pathname, analysis_type,
                  store_data, redis_key_store, manual_key_entry, processed_key_store, manual_processed_key_entry, to_process_key,   client_ip):

    # fix for none type issue
    get_data_btn = int(get_data_btn or 0)
    fetch_data_btn = int(fetch_data_btn or 0)
    clear_btn = int(clear_btn or 0)
    process_btn = int(process_btn or 0)
    download_cts = int(download_cts or 0)
    config_button = int(config_button or 0)
    fetch_processed_data_btn = int(fetch_processed_data_btn or 0)

    logging.info(f"Callback Triggered - Button ID: {dash.callback_context.triggered}")

    ctx = dash.callback_context
    if not ctx.triggered:
        return (dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, # redis keys update
                dash.no_update, dash.no_update, dash.no_update, dash.no_update)

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    global dataframe

    #  Clear screen 
    if button_id == 'clear-screen-button':
        logging.info("Clearing screen...")
        store_data['get_data_clicks'] = 0
        store_data['get_all_data_clicks'] = 0
        return (
            clear_screen(), [], [], {'get_data_clicks': 0, 'get_all_data_clicks': 0, 'onscreen_data': []},  # Reset store data
            [],  # Clear Redis key store
            [],  # Clear available keys container
            [],  # Clear processed key store
            [],  # Clear available processed keys container
            dash.no_update, dash.no_update,  [],  [] 
        )

    #  Retrieve and Store redis key
    if button_id == 'get-all-data-button' and get_data_btn > 0:
        if db_sel is None or tbl_sel is None or st_date is None or end_date is None:
            return ("Please Ensure a database, table, and date range are selected.", dash.no_update, dash.no_update, store_data, 
                    redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        logging.info(f"Fetching Redis Key -  DB: {db_sel}, Table: {tbl_sel}, Start Date: {st_date}, End Date: {end_date}")
        response_json = get_data_all( db_sel, tbl_sel, st_date, end_date, client_ip)  # Calls backend
        redis_key = response_json.get("redis_key")
        db_sel_lbl = next(
                                (item['label'] for item in CONFIG['database_options'] if item['value'] == db_sel),
                                None  
                            )
        if db_sel_lbl:
            redis_key_display = f"{redis_key} - {db_sel_lbl} - {tbl_sel} - {st_date} - {end_date}"
        else:
            redis_key_display = f"{redis_key} - {tbl_sel} - {st_date} - {end_date}"
        if redis_key:
            if not redis_key_store:
                redis_key_store = []
            redis_key_store.append(redis_key_display)
            return(
                f"Data requested. Redis Key: {redis_key}",dash.no_update, dash.no_update, store_data, 
                redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update,dash.no_update
            )

        return ("Failed to retrieve data.", [], [], store_data, 
                redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, [], [])

    # Updated to now only fetch the data from Redis when a user clicks the retrieve data from redis button 
    if button_id == 'fetch-from-redis-button' :
        redis_key = manual_key_entry or (redis_key_store[-1] if redis_key_store else None)
        redis_key = redis_key.split(' - ')[0] if redis_key else None
        redis_key = redis_key.strip()  
        if redis_key:
            try:
                # Fetch data from Redis using the key if exists
                if redis_client.exists(redis_key):
                    logging.info(f"Redis key {redis_key} exists")
                    redis_data = redis_client.get(redis_key)
                else:
                    logging.info(f"Redis key {redis_key} does not exist")
                    return (
                        f"Redis key {redis_key} does not exist", dash.no_update, dash.no_update, store_data,
                        redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, [], []
                    )
                if redis_data:
                    redis_data = json.loads(redis_data)
                    dataframe = pd.DataFrame(redis_data)
                    column_options = [{"label": col, "value": col} for col in dataframe.columns]
                    # update to ensure that columns that are not numeric are not shown in the y axis dropdown but string types that contian only numeric (steps) are allowed to be plotted
                    numeric_columns = [{"label": col, "value": col} for col in dataframe.columns if pd.to_numeric(dataframe[col], errors='coerce').notnull().all()]
                    store_data['onscreen_data'] = dataframe.to_dict('records')
                    return (
                        f"Data retrieved for Redis Key: {redis_key}", [{"name": i, "id": i} for i in dataframe.columns],  dataframe.to_dict('records'), store_data,  # Store Data for visualization
                        redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, column_options, numeric_columns
                    )

            except Exception as e:
                logging.error(f"Redis Raw Data Fetch Error: {e}")
                return (
                    f"Error retrieving data from Redis: {e}", dash.no_update, dash.no_update, store_data,
                    redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update
                ) 

    # Used to fetch the processed data from redis using a key - same conecpt as above
    if button_id == 'fetch-processed-from-redis-button':
        redis_key = manual_processed_key_entry or (processed_key_store[-1] if processed_key_store else None)
        # keys is of the form <redis_key> - <analysis_type> so we need to split the key to get the redis key only no space and remove the analysis 
        redis_key = redis_key.split(' - ')[0] if redis_key else None
        redis_key = redis_key.strip() 
        if redis_key:
            try:
                logging.info(f"Fetching Redis Key - Processed Data: {redis_key}")
                redis_data = redis_client.get(redis_key)
                logging.info(f"Redis key {redis_key} exists")
                if redis_data:
                    redis_data = json.loads(redis_data)
                    logging.info(f"Redis data loaded")
                    dataframe = pd.DataFrame(redis_data)
                    column_options = [{"label": col, "value": col} for col in dataframe.columns]
                    # update to ensure that columns that are not numeric are not shown in the y axis dropdown but string types that contian only numeric (steps) are allowed to be plotted
                    numeric_columns = [{"label": col, "value": col} for col in dataframe.columns if pd.to_numeric(dataframe[col], errors='coerce').notnull().all()]
                    store_data['onscreen_data'] = dataframe.to_dict('records')
                    return (
                        f"Data retrieved for Redis Key: {redis_key}",
                        [{"name": i, "id": i} for i in dataframe.columns],  dataframe.to_dict('records'),  store_data,  # Store Data for visualization
                        redis_key_store, dash.no_update, processed_key_store, dash.no_update,
                        dash.no_update, dash.no_update, column_options, numeric_columns
                    )

            except Exception as e:
                logging.error(f"Redis Process Data Fetch Error: {e}")
                return (
                    f"Error retrieving data from Redis: {e}", [], [], store_data,
                    redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, html.Ul([html.Li(key) for key in processed_key_store]), 
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update
                )
        pass 


    # https://dash.plotly.com/dash-core-components/download
    # Generate CSV data from the current data on the screen
    if button_id == 'btn_csv':
        filename1 = f"data_{time.strftime('%H%M%S')}_{random.randint(1,50)}.csv"
        logging.info(f"Generating CSV file: {filename1}")
        # check if the store data is empty
        if not store_data or "onscreen_data" not in store_data or not store_data["onscreen_data"]:
            return dash.no_update, dash.no_update, dash.no_update, store_data, redis_key_store, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        data = store_data.get('onscreen_data', [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}])
        csv_data = generate_csv_data(data)
        return(
                dash.no_update, dash.no_update, dash.no_update, store_data, 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, 
                dcc.send_data_frame(csv_data.to_csv, filename=filename1, index=False),
                dash.no_update, dash.no_update
        )

    # Process Data for Analysis
    if button_id == 'process-data' and process_btn > 0:
        logging.info(f"Processing Data - Code")

        if to_process_key is None:
            return (f"Please enter a Redis key to process data.", dash.no_update, dash.no_update, store_data, 
                    redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        try:
            data = send_data_for_processing(to_process_key, analysis_type)  # Calls backend
            logging.info(f"Processing Data - Redis Key: {to_process_key}")
            redis_key = data.get("redis_key")
            logging.info(f"Processing Data - Redis Key Returned: {redis_key}")
            if not redis_key:
                error_message = data.get("error")
            if redis_key:
                if not processed_key_store:
                    processed_key_store = []
                    
                analysis_type_lbl = next(
                                        (item['label'] for item in CONFIG['analytics'] if item['value'] == analysis_type),
                                        None  
                                    )
                if analysis_type_lbl:
                    appended_key_str = f"{redis_key} - {analysis_type_lbl}"
                else:
                    appended_key_str = redis_key
                processed_key_store.append(appended_key_str)
                return(
                    f"Data processed. Redis Key: {redis_key}",dash.no_update, dash.no_update, store_data, 
                    dash.no_update, dash.no_update, processed_key_store, html.Ul([html.Li(key) for key in processed_key_store]),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update
                )

            return (f"Failed To Process Data Dash Error Catch - No Key Returned From Server - Error: {error_message}.", [], [], store_data, 
                    dash.no_update, dash.no_update, processed_key_store, html.Ul([html.Li(key) for key in processed_key_store]),
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            return (f"Error processing data: {e}", [], [], store_data, 
                    dash.no_update, dash.no_update, processed_key_store, html.Ul([html.Li(key) for key in processed_key_store]),
                    dash.no_update, dash.no_update, [], [])



    # Config Page
    if button_id == 'config-button':
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, 
                '/dash/page2', dash.no_update, dash.no_update, dash.no_update)
    
    if button_id == 'Add_db':
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, 
                '/dash/page3', dash.no_update, dash.no_update, dash.no_update)

    # Update Graph menu
    column_options = [{"label": col, "value": col} for col in dataframe.columns]
    numeric_columns = [{"label": col, "value": col} for col in dataframe.select_dtypes(include="number").columns]

    return (
        html.Div([""]),
        [{"name": i, "id": i} for i in dataframe.columns],  # Table Columns
        store_data["onscreen_data"],  # Table Data
        store_data,  # Store Data for visualization
        redis_key_store,
        html.Ul([html.Li(key) for key in redis_key_store]),  # Redis keys
        processed_key_store,  # Processed keys
        html.Ul([html.Li(key) for key in processed_key_store]),  # Processed keys container
        dash.no_update,
        dash.no_update,
        column_options,  # Populate X-axis dropdown
        numeric_columns  # Populate Y-axis dropdown (only numeric columns)
    )
   

@app.callback(
    Output("data-plot", "figure"),
    [Input("x-axis-dropdown", "value"),
     Input("y-axis-dropdown", "value")],
     Input("Graph-type", "value"),
    State("store", "data"),
    prevent_initial_call=True
    
)
def update_graph(x_axis, y_axes, g_type ,store_data):
    """Plots selected data from stored dataset."""
    if not store_data or "onscreen_data" not in store_data or not store_data["onscreen_data"]:
        return px.pie(title="No Data Available. Fetch Data First.")

    df = pd.DataFrame(store_data["onscreen_data"])
    if not x_axis or not y_axes:
        return px.scatter(title="Select X and Y axes to display visualization.")

    
    if isinstance(y_axes, str):
        y_axes = [y_axes]

    # Force each y column to numeric
    for y_col in y_axes:
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

    df = df.dropna(subset=y_axes)
    if df.empty:
        return px.scatter(title="No valid data to plot after cleaning.")

    if not x_axis or not y_axes:
        return px.scatter(title="Select X and Y axes to display visualization.")
    
    if g_type == 'scatter':
        fig = px.scatter(df, x=x_axis, y=y_axes, title="Data Plot")
    elif g_type == 'line':

        fig = px.line(df, x=x_axis, y=y_axes, markers=True, title="Data Plot")
    elif g_type == 'bar':
        fig = px.bar(df, x=x_axis, y=y_axes, title="Data Plot")
    elif g_type == 'box':
        fig = px.box(df, x=x_axis, y=y_axes, title="Data Plot")
    elif g_type == 'histogram':
        fig = px.histogram(df, x=x_axis, y=y_axes, title="Data Plot")
    elif g_type == 'pie':
        fig = px.pie(df, names=x_axis, values=y_axes[0], title="Data Plot")
    else:
        fig = px.scatter(df, x=x_axis, y=y_axes, title="Data Plot")

    return fig



def clear_screen():
    return ''

def generate_csv_data(data_to_download) -> pd.DataFrame:
    # data is in a list of dictionaries format, must convert to pandas dataframe
    df = pd.DataFrame(data_to_download)
    return df

   
# Old Function previously used to get increments of data from the database - Now button calls send_data_for_processing
def get_data(n_clicks, redis_key_proc):
    # This function will send a request to the FastAPI server to get data from the database
   
    # use the config file to get the table name and database name
    #database_table_sel = CONFIG['databases'][db_sel]['database']['table']
    endpoint_ip = CONFIG['endpoints']['backend-service']['ip']
    endpoint_port = CONFIG['endpoints']['backend-service']['port']

    data = {
    "values": [
        {"sensor": "A", "reading": 10},
        {"sensor": "B", "reading": 20},
        {"sensor": "C", "reading": 30}
    ]
    }


    url = f'http://{endpoint_ip}:{endpoint_port}/rec_req?operation=stats&redis_key={redis_key_proc}'  

    response = requests.post(url, json=data)
   
    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    response = response.json()

    
    # flatten processed in the response
    response = response['processed']


    
    return response

def get_data_all(db_sel, tbl_sel, st_date, end_date, user_ip):
   
    #using config file to get the table name
  
    #database_table_sel = CONFIG['databases'][db_sel]['database']['table']
    endpoint_ip = CONFIG['endpoints']['db-connection-layer']['ip']
    endpoint_port = CONFIG['endpoints']['db-connection-layer']['port']
    logging.info(f"Fetching data from {endpoint_ip}:{endpoint_port}")
    response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/data?database={db_sel}&table_name={tbl_sel}&start={st_date}&end={end_date}&user={user_ip}') # updated to take the table name from the dropdown
    response_json = response.json()
    # send response to redis first 
    logging.info(f"Response Rec: {response_json}")
    if False:
        json_data = response.json()
        try:
            redis_client.set('data_response', json.dumps(json_data))
        except Exception as e:
            logging.error(f"Redis error: {e}")
            return [{"Error": "Error in getting data"}]

        if response.status_code == 500:
            return [{"Error": "Error in getting data"}]
        return response.json()
    else:
        return response_json


def send_data_for_processing(redis_key_proc, analysis_typ):
    # This function will send data to the appropriate LxCT for processing

    endpoint_ip = CONFIG['endpoints']['backend-service']['ip']
    endpoint_port = CONFIG['endpoints']['backend-service']['port']
    logging.info(f"Sending data for processing to {endpoint_ip}:{endpoint_port}")

    dual_key = False
    # strip the redis key to remove any spaces or whitespace
    # check to see if the redis key is sent as two keys, separated by a ','
    redis_key_proc = redis_key_proc.strip()
    if ',' in redis_key_proc:
        logging.info(f"Redis key is a dual key: {redis_key_proc}")
        dual_key = True
    
    url = f'http://{endpoint_ip}:{endpoint_port}/process_data?operation={analysis_typ}&redis_key={redis_key_proc}&dual={dual_key}'  
    logging.info(f"Sending data for processing to {url}")
    response_json = requests.post(url)
    logging.info(f"Response Rec: {response_json}")
    return response_json.json()




if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True) 