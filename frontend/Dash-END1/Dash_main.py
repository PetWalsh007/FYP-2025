'''
This file is the main Dash front end file for the system. It is responsible for the main layout of the Dash portion of the system.

https://dash.plotly.com/ for more information on Dash and how the Dash framework works

'''

import dash
from dash import dcc 
from dash import html
from dash.dependencies import Input, Output, State
import requests
import pandas as pd
import json
import subprocess
import time
import random


# Load the existing config
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

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
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.A(html.Button("Go to Home Page"), href="/", target="_self") #_self used to trigger full page reload 
], style={'fontFamily': 'Times New Roman', 'padding': '40px'})




# Define the layout for the main page
# https://dash.plotly.com/dash-html-components for more information on the HTML components
# https://dash.plotly.com/dash-core-components for more information on the DCC's

# Updated 08/02 to a function to allow for easier testing of dynamic content in dropdown from JSON config
def main_page_layout():
    return html.Div([
        html.Div(className='row', children='Real-Time Adaptive Data Analytics and Visualisation Platform for Industrial Manufacturing Execution Systems',
                style=dev_style),
        html.Div([
            html.Button('Get Data', id='get-data-button', n_clicks=0, className='button'),
            html.Button('Get X Data', id='get-all-data-button', n_clicks=0, className='button'),
            html.Button('Clear', id='clear-screen-button', n_clicks=0, className='button'),
            html.Button("Download CSV", id="btn_csv"),
            html.Button("Config", id="config-button", n_clicks=0, className='button'),
            dcc.Download(id="download-dataframe-csv"),
        ], style=button_style),
        
        html.Div([
            html.Label('X Number of data points to display:', style={'fontSize': '18px', 'marginRight': '10px'}),
            dcc.Input(id='data-points', type='number', value=10, style={'fontSize': '18px', 'width': '100px'}),
            html.Label('Select the database to query:', style={'fontSize': '18px', 'marginRight': '10px', 'marginLeft': '15px'}),
            dcc.Dropdown(id='database', options=config.get("database_options", []), value='postgres', style={'fontSize': '18px', 'width': '170px'}),
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'display': 'flex','justifyContent': 'center'}),
        html.Div(id='output-container', style=text_style2),
        html.Div(id='output-container-all', style=text_style1),
        dcc.Store(id='store', data={'get_data_clicks': 0, 'get_all_data_clicks': 0, 'onscreen_data':[]}),  # Store to keep track of click counts
    ])


page2_layout = html.Div([
    html.H1("Edit Config File"),
    
    html.P("Warning: Editing the config file may cause the system to stop working. Only edit if you know what you are doing.", style={'color': 'red'}),
    
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
    html.A('Go back to main page', href='/dash/')
    
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

# Serves as the callback function for the Dash app to update the content of the output containers

@app.callback(
    [Output('output-container', 'children'),
     Output('output-container-all', 'children'),
     Output('store', 'data'),
     Output('url', 'pathname'),
     Output('download-dataframe-csv', 'data')],
    [Input('clear-screen-button', 'n_clicks'),
     Input('get-data-button', 'n_clicks'),
     Input('get-all-data-button', 'n_clicks'),
     Input('data-points', 'value'),
     Input('database', 'value'),
     Input("btn_csv", "n_clicks"),
     Input("config-button", "n_clicks"),
     Input('url', 'pathname')],
    [State('store', 'data')],
    prevent_initial_call=True
)
def update_output(na_button, get_data_clicks, get_all_data_clicks, data_pt, db_sel, download_cts, config_button, pathname, store_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # https://dash.plotly.com/dash-core-components/download
    # Generate CSV data from the current data on the screen
    if button_id == 'btn_csv':
        
        filename1 = f"data_{time.strftime('%H%M%S')}_{random.randint(1,50)}.csv"
        data = store_data.get('onscreen_data', [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}])
        csv_data = generate_csv_data(data)
        return dash.no_update, dash.no_update, store_data, dash.no_update, dcc.send_data_frame(csv_data.to_csv, filename=filename1, index=False)

    if button_id == 'clear-screen-button':
        store_data['get_data_clicks'] = 0
        store_data['get_all_data_clicks'] = 0
        
        return clear_screen(), clear_screen(), store_data, dash.no_update, dash.no_update  # Clear the content of both output containers and reset click counts

    if button_id == 'get-data-button' and get_data_clicks > 0:
        
        store_data['get_data_clicks'] += 1  
        data = get_data(store_data['get_data_clicks'], db_sel)  
        store_data['onscreen_data'] = data  # update the store for onscreen data
        return html.Div(['Button clicked ', html.B(store_data["get_data_clicks"]), f' times. Data: {data}']), clear_screen(), store_data, dash.no_update, dash.no_update

    if button_id == 'get-all-data-button' and get_all_data_clicks > 0:
        store_data['onscreen_data'] = []  # Reset the onscreen data
        all_data = get_data_all(data_pt, db_sel)
        store_data['get_data_clicks'] = 0  # Reset the click count for the other button
        
        store_data['onscreen_data'] = all_data # update the store for onscreen data
        return clear_screen(), f'Button clicked. All Data: {all_data}', store_data, dash.no_update, dash.no_update

    if button_id == 'config-button':
        return dash.no_update, dash.no_update, store_data, '/dash/page2', dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
   




def clear_screen():
    return ''

def generate_csv_data(data_to_download):
    # data is in a list of dictionaries format, must convert to pandas dataframe
    df = pd.DataFrame(data_to_download)
    return df

   

def get_data(n_clicks, db_sel):
    # This function will send a request to the FastAPI server to get data from the database

    # use the config file to get the table name and database name
    database_table_sel = config['databases'][db_sel]['database']['table']
    endpoint_ip = config['endpoints']['abstraction']['ip']
    endpoint_port = config['endpoints']['abstraction']['port']


    response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/data?database={db_sel}&table_name={database_table_sel}&limit={n_clicks}') # updated to take the table name from the config file

    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    return response.json()

def get_data_all(pts, db_sel):

    #using config file to get the table name
  
    database_table_sel = config['databases'][db_sel]['database']['table']
    endpoint_ip = config['endpoints']['abstraction']['ip']
    endpoint_port = config['endpoints']['abstraction']['port']
    
    response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/data?database={db_sel}&table_name={database_table_sel}&limit={pts}') # updated to take the table name from the config file

    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    return response.json()




if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True) 