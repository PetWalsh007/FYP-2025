'''
This file is the main Dash front end file for the system. It is responsible for the main layout of the Dash portion of the system.

https://dash.plotly.com/ for more information on Dash and how the Dash framework works

'''

import dash
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
    global config
    config = load_config()
     
load_config_call()



# routes pathname added for testing 
app = dash.Dash(__name__, requests_pathname_prefix='/dash/')
app.title = 'RTA MES'
server = app.server  # Expose the Flask server for Gunicorn



def connect_redis():
    
    redis_host = config['endpoints']['redis']['ip']
    redis_port = config['endpoints']['redis']['port']
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
if redis_client is None:
    t=5
    logging.error("Failed to connect to Redis server. Retrying...")
    time.sleep(t)
    connect_redis()  # Retry connecting to Redis server
    if redis_client is None:
        logging.error(f"Failed to connect to Redis server {config['endpoints']['redis']['ip']} after retrying....")
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
app.layout = html.Div([
    html.A(html.Button("Go to Home Page", className='Button', style=button_style2), href="/", target="_self"),
    html.Button('Clear', id='clear-screen-button', n_clicks=0, className='button', style=button_style2),
    html.Button("Download CSV", id="btn_csv", className='button', style=button_style2),
    html.Button("Config", id="config-button", n_clicks=0, className='button', style={**button_style2, 'marginRight': '0px'}),
    dcc.Download(id="download-dataframe-csv"),  # _self used to trigger full page reload 
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Label('X Number of data points to display:', style={'fontSize': '18px', 'marginRight': '10px'}),
    dcc.Input(id='data-points', type='number', value=10, style={'fontSize': '18px', 'width': '100px'}),
], style={'fontFamily': 'Times New Roman', 'padding': '40px'})




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
                options=config.get("database_options", []),
                value='postgres',
                style={'fontSize': '18px', 'width': '170px', 'marginRight': '10px'}
            ),
            dcc.Dropdown(
                id="table_name",
                options=[
                    {"label": f"{db_name.upper()} - {table}", "value": table}
                    for db_name, db_info in config["databases"].items()
                    for table in db_info["database"].get("tables", [])
                ],
                value=None,
                placeholder="Select a Table",
                style={'fontSize': '18px', 'width': '250px', 'marginRight': '10px'}
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
                options=config.get("analytics", []),
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
           html.Div([html.Label("Stored Redis Keys from this Session:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                     html.Div(id="available-keys-container", style={'marginBottom': '10px', 'textAlign': 'center', 'display': 'grid', 'gap': '10px'}),


                    html.Label("Enter Redis Key to Retrieve Data:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    dcc.Input(id='redis-key-entry', type='text', placeholder="Enter Redis Key", style={'marginRight': '10px', 'fontSize': '16px', 'padding': '5px'}),

                    html.Button("Retrieve Data from Redis", id="fetch-from-redis-button", n_clicks=0, className='button', style=button_style),

                    # Hidden store to keep track of Redis keys
                    dcc.Store(id='redis-key-store', data=[]),
                    ],style={'flex': '1', 'marginTop': '20px', 'textAlign': 'left', 'padding': '20px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'backgroundColor': '#ededed  '}),

            html.Div([
                    html.Label("Stored Processed Data Keys from this Session:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    html.Div(id="available-processed-keys-container", style={'marginBottom': '10px', 'textAlign': 'center'}),

                    html.Label("Enter Processed Data Key to Retrieve Data:", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                    dcc.Input(id='processed-key-entry', type='text', placeholder="Enter Processed Data Key", style={'marginRight': '10px', 'fontSize': '16px', 'padding': '5px'}),

                    html.Button("Retrieve Processed Data from Redis", id="fetch-processed-from-redis-button", n_clicks=0, className='button', style=button_style),

                    # Hidden store to keep track of Processed Data Redis keys
                    dcc.Store(id='processed-key-store', data=[]),
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
        dcc.Store(id='store', data={'get_data_clicks': 0, 'get_all_data_clicks': 0, 'onscreen_data':[]}),  # Store to keep track of click counts
    ])


page2_layout = html.Div([
    html.H1("Edit Config File"),
    
    html.P("Warning: Editing the config file may cause the system to stop working. Ensure Backup has been taken", style={'color': 'red'}),
    
    dcc.Textarea(
        id='config-textarea',
        value=json.dumps(config, indent=4),
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
    html.A('Go back to main page Dash', href='/dash/')
    
])

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
        endpoint_ip = config['endpoints']['abstraction']['ip']
        endpoint_port = config['endpoints']['abstraction']['port']
        response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/command?rst=restart_server_main_abstraction')
        time.sleep(2) # for a wait time to allow the server to restart
        return response.text
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
    return main_page_layout()



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
     Input('data-points', 'value'),
     Input('database', 'value'),
     Input('table_name', 'value'),
     Input("btn_csv", "n_clicks"),
     Input("config-button", "n_clicks"),
     Input('url', 'pathname')],
    [State('store', 'data'),
     State('redis-key-store', 'data'),
     State('redis-key-entry', 'value'),
     State('processed-key-store', 'data'),
     State('processed-key-entry', 'value'),
     State('redis-key-for-proc', 'value')],
    prevent_initial_call=True
)
def update_output(clear_btn, get_data_btn, fetch_data_btn, fetch_processed_data_btn, st_date, end_date, process_btn,
                  data_pt, db_sel, tbl_sel, download_cts, config_button, pathname,
                  store_data, redis_key_store, manual_key_entry, processed_key_store, manual_processed_key_entry, to_process_key):

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
        logging.info(f"Fetching Redis Key - Data Points: {data_pt}, DB: {db_sel}, Table: {tbl_sel}, Start Date: {st_date}, End Date: {end_date}")
        response_json = get_data_all(data_pt, db_sel, tbl_sel, st_date, end_date)  # Calls backend
        redis_key = response_json.get("redis_key")

        if redis_key:
            if not redis_key_store:
                redis_key_store = []
            redis_key_store.append(redis_key)
            return(
                f"Data requested. Redis Key: {redis_key}",[], [], store_data, 
                redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, [], []
            )

        return ("Failed to retrieve data.", [], [], store_data, 
                redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, [], [])

    # Updated to now only fetch the data from Redis when a user clicks the retrieve data from redis button 
    if button_id == 'fetch-from-redis-button' :
        redis_key = manual_key_entry or (redis_key_store[-1] if redis_key_store else None)
        if redis_key:
            try:
                # Fetch data from Redis using the key if exists
                if redis_client.exists(redis_key):
                    logging.info(f"Redis key {redis_key} exists")
                    redis_data = redis_client.get(redis_key)
                else:
                    logging.info(f"Redis key {redis_key} does not exist")
                    return (
                        f"Redis key {redis_key} does not exist", [], [], store_data,
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
                    f"Error retrieving data from Redis: {e}", [], [], store_data,
                    redis_key_store, html.Ul([html.Li(key) for key in redis_key_store]), dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, [], []
                ) 

    # Used to fetch the processed data from redis using a key - same conecpt as above
    if button_id == 'fetch-processed-from-redis-button':
        redis_key = manual_processed_key_entry or (processed_key_store[-1] if processed_key_store else None)
        if redis_key:
            try:
                redis_data = redis_client.get(redis_key)
                if redis_data:
                    redis_data = json.loads(redis_data)
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
                    dash.no_update, dash.no_update, [], []
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
        store_data['get_data_clicks'] += 1  
        try:
            data = send_data_for_processing(to_process_key)
            store_data['onscreen_data'] = data
            dataframe = pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Error processing data: {e}")


    # Config Page
    if button_id == 'config-button':
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, 
                '/dash/page2', dash.no_update, dash.no_update, dash.no_update)
    # Update Graph menu
    column_options = [{"label": col, "value": col} for col in dataframe.columns]
    numeric_columns = [{"label": col, "value": col} for col in dataframe.select_dtypes(include="number").columns]

    return (
        html.Div([""]),
        [{"name": i, "id": i} for i in dataframe.columns],  # Table Columns
        store_data["onscreen_data"],  # Table Data
        store_data,  # Store Data for visualization
        redis_key_store,
        dash.no_update,  # Redis keys
        dash.no_update,  # Processed keys
        dash.no_update,  # Processed keys container
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
    #database_table_sel = config['databases'][db_sel]['database']['table']
    endpoint_ip = config['endpoints']['backend']['ip']
    endpoint_port = config['endpoints']['backend']['port']

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

def get_data_all(pts, db_sel, tbl_sel, st_date, end_date):
    
    #using config file to get the table name
  
    #database_table_sel = config['databases'][db_sel]['database']['table']
    endpoint_ip = config['endpoints']['abstraction']['ip']
    endpoint_port = config['endpoints']['abstraction']['port']
    
    response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/data?database={db_sel}&table_name={tbl_sel}&limit={pts}&start={st_date}&end={end_date}') # updated to take the table name from the dropdown
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


def send_data_for_processing(redis_key_proc):
    # This function will send data to the appropriate LxCT for processing

    endpoint_ip = config['endpoints']['backend']['ip']
    endpoint_port = config['endpoints']['backend']['port']
    logging.info(f"Sending data for processing to {endpoint_ip}:{endpoint_port}")


    
    url = f'http://{endpoint_ip}:{endpoint_port}/rec_req?operation=stats&redis_key={redis_key_proc}'  
    response = requests.post(url, json=data)
    
    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    response = response.json()

    
    # flatten processed in the response
    response = response['processed']

    return response




if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True) 