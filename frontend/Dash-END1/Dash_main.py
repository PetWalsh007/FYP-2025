'''
This file is the main Dash front end file for the system. It is responsible for the main layout of the Dash portion of the system.
'''

import dash
from dash import dcc 
from dash import html
from dash.dependencies import Input, Output, State
import requests
import pandas as pd

app = dash.Dash(__name__)
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
    html.Div(className='row', children='Real-Time Adaptive Data Analytics and Visualisation Platform for Industrial Manufacturing Execution Systems',
             style=dev_style),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Div([
        html.Button('Get Data', id='get-data-button', n_clicks=0, className='button'),
        html.Button('Get X Data', id='get-all-data-button', n_clicks=0, className='button'),
        html.Button('Clear', id='clear-screen-button', n_clicks=0, className='button'),
        html.Button("Download CSV", id="btn_csv"),
        dcc.Download(id="download-dataframe-csv"),
    ], style=button_style),
    
    html.Div([
        html.Label('X Number of data points to display:', style={'fontSize': '18px', 'marginRight': '10px'}),
        dcc.Input(id='data-points', type='number', value=10, style={'fontSize': '18px', 'width': '100px'})
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div(id='output-container', style=text_style2),
    html.Div(id='output-container-all', style=text_style1),
    dcc.Store(id='store', data={'get_data_clicks': 0, 'get_all_data_clicks': 0}),  # Store to keep track of click counts
], style={'fontFamily': 'Times New Roman', 'padding': '70px'})

# Serves as the callback function for the Dash app to update the content of the output containers
@app.callback(
    [Output('output-container', 'children'),
     Output('output-container-all', 'children'),
     Output('store', 'data')],
    [Input('clear-screen-button', 'n_clicks'),
     Input('get-data-button', 'n_clicks'),
     Input('get-all-data-button', 'n_clicks'),
     Input('data-points', 'value')],
     Input("btn_csv", "n_clicks"),
    [State('store', 'data')],
    prevent_initial_call=True
)
def update_output(na_button, get_data_clicks, get_all_data_clicks, data_pt, download_cts,store_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn_csv':
        # Generate CSV data
        data = get_data(store_data['get_data_clicks'])  # Define data here
        csv_data = generate_csv_data(data)
        return dash.no_update, dash.no_update, store_data, dcc.send_data_frame(csv_data.to_csv, "data.csv")

    if button_id == 'clear-screen-button':
            store_data['get_data_clicks'] = 0
            store_data['get_all_data_clicks'] = 0
            return clear_screen(), clear_screen(), store_data  # Clear the content of both output containers and reset click counts

    if button_id == 'get-data-button' and get_data_clicks > 0:
        store_data['get_data_clicks'] += 1  
        data = get_data(store_data['get_data_clicks'])
        return html.Div(['Button clicked ', html.B(store_data["get_data_clicks"]), f' times. Data: {data}']), clear_screen(), store_data

    if button_id == 'get-all-data-button' and get_all_data_clicks > 0:
        all_data = get_data_all(data_pt)
        store_data['get_data_clicks'] = 0 # Reset the click count for the other button
        return clear_screen(), f'Button clicked. All Data: {all_data}', store_data

    return dash.no_update, dash.no_update, dash.no_update  
   
def clear_screen():
    return ''

def generate_csv_data(data_to_download):
    # data is in a list of dictionaries format, must convert to pandas dataframe
    df = pd.DataFrame(data_to_download)
    return df

   

def get_data(n_clicks):
    # This function will send a request to the FastAPI server to get data from the database

    response = requests.get(f'http://192.168.1.81:8000/data?database=postgres&table_name=plc_step_test&limit={n_clicks}') # simple fixed request URL for now
    return response.json()

def get_data_all(pts):
  

    response = requests.get(f'http://192.168.1.81:8000/data?database=postgres&table_name=plc_step_test&limit={pts}') 
    return response.json()


if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True) 