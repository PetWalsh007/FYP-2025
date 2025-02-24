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


logging.basicConfig(filename="dash_main.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Load the existing config
CONFIG_FILE = "config.json"
# global dataframe for data to plot 
dataframe = pd.DataFrame()

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
    html.A(html.Button("Go to Home Page"), href="/", target="_self"), #_self used to trigger full page reload 
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
   
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
            dcc.DatePickerRange(
                                id='data-date-range',
                                display_format='DD/MM/YYYY',
                                initial_visible_month=date.today(),
                                ),

            html.Button('Process Data', id='process-data', n_clicks=0, className='button'),
            html.Button('Get X Data', id='get-all-data-button', n_clicks=0, className='button'),
            html.Button('Clear', id='clear-screen-button', n_clicks=0, className='button'),
            html.Button("Download CSV", id="btn_csv"),
            html.Button("Config", id="config-button", n_clicks=0, className='button'),
            dcc.Download(id="download-dataframe-csv"),
        ], style=button_style),
        html.Div([
            html.Label("Select Data Store:"),
            
            dcc.RadioItems(
                id="store-selector",
                options=[
                    {"label": html.Span(" Store 1", id="store-1-label"), "value": "dataframe-store-1"},
                    {"label": html.Span(" Store 2", id="store-2-label"), "value": "dataframe-store-2"},
                    {"label": html.Span(" Store 3", id="store-3-label"), "value": "dataframe-store-3"},
                ],
                value="dataframe-store-1",
                labelStyle={'display': 'inline-block', 'marginRight': '10px'}
            ),
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'display': 'flex', 'justifyContent': 'center'}),

        
        html.Div([
            html.Label('X Number of data points to display:', style={'fontSize': '18px', 'marginRight': '10px'}),
            dcc.Input(id='data-points', type='number', value=10, style={'fontSize': '18px', 'width': '100px'}),
            html.Label('Select the database to query:', style={'fontSize': '18px', 'marginRight': '10px', 'marginLeft': '15px'}),
            dcc.Dropdown(id='database', options=config.get("database_options", []), value='postgres', style={'fontSize': '18px', 'width': '170px'}),
            dcc.Dropdown(
                        id="table_name",
                        options= [
                                    {"label": f"{db_name.upper()} - {table}", "value": table}
                                    for db_name, db_info in config["databases"].items()
                                    for table in db_info["database"].get("tables", [])
                                ],  # Dynamically loads all tables
                        value=None,
                        placeholder="Select a Table",
                        style={'fontSize': '18px', 'width': '250px'}
    ),
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'display': 'flex','justifyContent': 'center'}),
        html.Div(id='output-container', style=text_style2),

        html.Div([
            dcc.Dropdown(id="x-axis-dropdown", placeholder="Select X-Axis", style={'width': '250px'}),
            dcc.Dropdown(id="y-axis-dropdown", multi=True, placeholder="Select Y-Axis", style={'width': '350px'}),
            dcc.Dropdown(id='Graph-type', options=[{'label': 'Scatter', 'value': 'scatter'}, {'label': 'Line', 'value': 'line'},
                                                   {'label': 'Bar', 'value': 'bar'}, {'label': 'Box', 'value': 'box'},
                                                    {'label': 'Histogram', 'value': 'histogram'},
                                                    {'label': 'Pie', 'value': 'pie'},
                                                   ], value='scatter', style={'width': '150px'}),
        ], style={'display': 'flex', 'gap': '10px', 'margin': '20px'}),

        dcc.Graph(id="data-plot"),  

        html.Div([dash_table.DataTable(
                                        id="data-table",
                                        columns=[],  # Columns 
                                        data=[],  # defualt empty data
                                        filter_action="native",
                                        sort_action="native",
                                        page_size=1500   
                                        )
                ], style={'marginTop': '20px'}),
        dcc.Store(id='store', data={'get_data_clicks': 0, 'get_all_data_clicks': 0, 'onscreen_data':[]}),  # Store to keep track of click counts
        dcc.Store(id='dataframe-store-1', storage_type='session', data={}),  # Store the first dataframe 
        dcc.Store(id='dataframe-store-2', storage_type='session', data={}),  # Store the second dataframe
        dcc.Store(id='dataframe-store-3', storage_type='session', data={}),  # Store the third dataframe
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
def update_store_colors(store1, store2, store3):
    logging.debug(f"store1: {store1}, store2: {store2}, store3: {store3}")
    
    def get_style(data):
        has_data = {'color': 'green', 'fontWeight': 'bold', 'backgroundColor': '#DFF2BF', 'padding': '3px 6px', 'borderRadius': '5px'}
        no_data = {'color': 'blue', 'fontWeight': 'normal', 'backgroundColor': '#FFBABA', 'padding': '3px 6px', 'borderRadius': '5px'}
        return has_data if data else no_data

    styles = get_style(store1), get_style(store2), get_style(store3)
    logging.debug(f"styles: {styles}")
    return styles







# Serves as the callback function for the Dash app to update the content of the output containers

@app.callback(
    [Output('output-container', 'children'),
     Output('data-table', 'columns'),  
     Output('data-table', 'data'),  
     Output('store', 'data'),  # Store data for visualization
     Output('url', 'pathname'),
     Output('download-dataframe-csv', 'data'),
     Output('x-axis-dropdown', 'options'),  # Populate X-axis dropdown
     Output('y-axis-dropdown', 'options')],  # Populate Y-axis dropdown (numeric)
    [Input('clear-screen-button', 'n_clicks'),
     Input('data-date-range', 'start_date'),
     Input('data-date-range', 'end_date'),
     Input('process-data', 'n_clicks'),
     Input('get-all-data-button', 'n_clicks'),
     Input('store-selector', 'value'),
     Input('data-points', 'value'),
     Input('database', 'value'),
     Input('table_name', 'value'),
     Input("btn_csv", "n_clicks"),
     Input("config-button", "n_clicks"),
     Input('url', 'pathname')],
    [State('store', 'data'),
     State('dataframe-store-1', 'data'),
     State('dataframe-store-2', 'data'),
     State('dataframe-store-3', 'data')],
    prevent_initial_call=True
)
def update_output(na_button,st_date , end_date , get_data_clicks, get_all_data_clicks, selected_store ,data_pt, db_sel, tbl_sel ,download_cts, config_button, pathname, store_data, data_store_1, data_store_2, data_store_3):

    """
    This function is the main callback function for the main app page. It is used to update the main content containers.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

     # Ensure stores are dictionaries
    if data_store_1 is None:
        data_store_1 = {}
    if data_store_2 is None:
        data_store_2 = {}
    if data_store_3 is None:
        data_store_3 = {}
    
    # https://dash.plotly.com/dash-core-components/download
    # Generate CSV data from the current data on the screen
    if button_id == 'btn_csv':
        
        filename1 = f"data_{time.strftime('%H%M%S')}_{random.randint(1,50)}.csv"
        data = store_data.get('onscreen_data', [{'col1': 'value1', 'col2': 'value2'}, {'col1': 'value3', 'col2': 'value4'}])
        csv_data = generate_csv_data(data)
        return dash.no_update, dash.no_update, dash.no_update, store_data, dash.no_update, dcc.send_data_frame(csv_data.to_csv, filename=filename1, index=False), dash.no_update, dash.no_update

    if button_id == 'clear-screen-button':
        store_data['get_data_clicks'] = 0
        store_data['get_all_data_clicks'] = 0
        
        return clear_screen(), [], [], store_data, dash.no_update, dash.no_update, [], []  # Clear the content of both output containers, reset click counts, and reset dropdowns

    if button_id == 'process-data' and get_data_clicks > 0:
        store_data['get_data_clicks'] += 1  
        global dataframe
       # data = get_data(store_data['get_data_clicks'], db_sel, tbl_sel)  

        data = get_data(store_data['get_data_clicks'])
        # log data 
        logging.info(f"Here -------- {data}")
        store_data['onscreen_data'] = data
        dataframe = pd.DataFrame(data)
        logging.info(f"Here dframe -------- {dataframe}")
        # update data_store_1
        # Save data to the selected store
        if selected_store == "dataframe-store-1":
            data_store_1 = {"data": data}
        elif selected_store == "dataframe-store-2":
            data_store_2 = {"data": data}
        elif selected_store == "dataframe-store-3":
            data_store_3 = {"data": data}

    elif button_id == 'store-selector':
        if selected_store == "dataframe-store-1":
            data = data_store_1.get("data")
            logging.info(f"Here dframe 1 -------- {data}")
        elif selected_store == "dataframe-store-2":
            data = data_store_2.get("data")
        elif selected_store == "dataframe-store-3":
            data = data_store_3.get("data")

        dataframe = pd.DataFrame(data)

        column_options = [{"label": col, "value": col} for col in dataframe.columns]
        numeric_columns = [{"label": col, "value": col} for col in dataframe.select_dtypes(include="number").columns]


    elif button_id == 'get-all-data-button' and get_all_data_clicks > 0:
        store_data['onscreen_data'] = []
        all_data = get_data_all(data_pt, db_sel, tbl_sel)  
        store_data['get_data_clicks'] = 0  
        dataframe = pd.DataFrame(all_data)
        logging.info(f"Here dframe  all -------- {dataframe}")
        store_data['onscreen_data'] = dataframe.to_dict('records')

    elif button_id == 'config-button':
        return dash.no_update, dash.no_update, dash.no_update, store_data, '/dash/page2', dash.no_update, dash.no_update, dash.no_update 

    else:
        return dash.no_update, dash.no_update, dash.no_update, store_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    column_options = [{"label": col, "value": col} for col in dataframe.columns]
    numeric_columns = [{"label": col, "value": col} for col in dataframe.select_dtypes(include="number").columns]

    #log data stores 1 2 3 
    logging.info(f"data_store_1: {data_store_1}")
    logging.info(f"data_store_2: {data_store_2}")
    logging.info(f"data_store_3: {data_store_3}")

    return (
        html.Div([f"Data retrieved for {tbl_sel} in {db_sel}."]),
        [{"name": i, "id": i} for i in dataframe.columns],  # Table Columns
        store_data["onscreen_data"],  # Table Data
        store_data,  # Store Data for visualization
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
        return px.scatter(title="No Data Available. Fetch Data First.")

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

def generate_csv_data(data_to_download):
    # data is in a list of dictionaries format, must convert to pandas dataframe
    df = pd.DataFrame(data_to_download)
    return df

   

def get_data(n_clicks):
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


    url = f'http://{endpoint_ip}:{endpoint_port}/rec_req?operation=stats' 

    response = requests.post(url, json=data)
   
    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    response = response.json()

    logging.info(response)
    # flatten processed in the response
    response = response['processed']


    
    return response

def get_data_all(pts, db_sel, tbl_sel):
    
    #using config file to get the table name
  
    #database_table_sel = config['databases'][db_sel]['database']['table']
    endpoint_ip = config['endpoints']['abstraction']['ip']
    endpoint_port = config['endpoints']['abstraction']['port']
    
    response = requests.get(f'http://{endpoint_ip}:{endpoint_port}/data?database={db_sel}&table_name={tbl_sel}&limit={pts}') # updated to take the table name from the dropdown

    if response.status_code == 500:
        return [{"Error": "Error in getting data"}]
    return response.json()


def send_data_for_processing(*args, **kwargs):
    # This function will send data to the appropriate LxCT for processing

    endpoint_ip = config['endpoints']['backend']['ip']
    endpoint_port = config['endpoints']['backend']['port']


    pass



if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True) 