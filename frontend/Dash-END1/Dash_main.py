'''
This file is the main Dash front end file for the system. It is responsible for the main layout of the Dash portion of the system.
'''

import dash
from dash import dcc 
from dash import html
from dash.dependencies import Input, Output
import requests

app = dash.Dash(__name__)


app.layout = [
    html.Div(className='row', children=' Real-Time Adaptive Data Analytics and Visualisation Platform for Industrial Manufacturing Execution Systems',
             style={'textAlign': 'center', 'color': 'blue', 'fontSize': 30}),
    html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Button('Get Data', id='get-data-button', n_clicks=0),
    html.Div(id='output-container')
])]

@app.callback(
    Output('output-container', 'children'),
    Input('get-data-button', 'n_clicks')
)
def update_output(n_clicks):
    if n_clicks > 0:
        data = get_data()
        return f'Button clicked {n_clicks} times. Data: {data}'
    return 'Click the button to get data.'


def get_data():
    # This function will send a request to the FastAPI server to get data from the database

    response = requests.get('http://192.168.1.81:8000/data?database=postgres&table_name=plc_step_test&limit=1000') # simple fixed request URL for now
    return response.json()


if __name__ == '__main__':
 
    app.run_server(host='0.0.0.0',debug=True,port=8050) 