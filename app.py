from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import requests
import os

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                           'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css'])

# Fetch data from the API
api_url = "https://demo.thewaittimes.com/WaitTime/api/waittimegetsensor"

try:
    response = requests.get(api_url)
    response.raise_for_status()  # Raise an error for bad status codes
    content_type = response.headers.get('Content-Type')

    if 'application/json' in content_type:
        data = response.json()
    else:
        print("Unexpected content type:", content_type)
        data = {}
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from API: {e}")
    data = {}

# Extract and process sensor data
sensors_data = data.get('SensorList', [])
selected_sensors = sensors_data[:3]  # Use the first three instances for simplicity

# Rename the sensors to match the original names
sensor_name_map = {
    0: "Jamara 1",
    1: "BTW Jam 1&2",
    2: "Jamara 2"
}

processed_data = []
for idx, sensor in enumerate(selected_sensors):
    sensor_desc = sensor_name_map[idx]
    sensor_data = {
        'SensorDesc': sensor_desc,
        'NumberInline': int(sensor['NumberInline']),
        'SensorPercentage': int(sensor['SensorPercentage']),
        'ServeTimeFrames': int(sensor['ServeTimeFrames']),
        'DataReadTime': sensor['DataReadTime']
    }
    processed_data.append(sensor_data)


# Create a DataFrame for the complex graph
def create_df(sensor_data):
    timestamps = pd.date_range(start=sensor_data['DataReadTime'], periods=10, freq='15min')
    percentages = [sensor_data['SensorPercentage'] + ((i * 3) % 30) for i in range(10)]  # Create variability
    intermissions = [sensor_data['ServeTimeFrames'] / 10 + (i % 10) for i in range(10)]  # Create variability
    return pd.DataFrame({
        'time': timestamps,
        'percentage': percentages,
        'intermission': intermissions
    })


def create_complex_graph(dataframe, sensor_desc, data_read_time):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dataframe['time'],
        y=dataframe['percentage'],
        mode='lines',
        fill='tozeroy',
        name='Percentage',
        line=dict(color='darkorange')
    ))

    fig.add_trace(go.Scatter(
        x=dataframe['time'],
        y=dataframe['intermission'],
        mode='lines',
        fill='tozeroy',
        name='Intermission',
        line=dict(color='orange')
    ))

    fig.update_layout(
        title=f'{sensor_desc} | Date: {data_read_time.split("T")[0]} | Time: {data_read_time.split("T")[1]}',
        xaxis_title='Time of Day',
        yaxis_title='Percentage',
        xaxis=dict(showgrid=True, gridcolor='lightgray', tickformat='%H:%M', title_text='Time of Day'),
        yaxis=dict(showgrid=True, gridcolor='lightgray', range=[0, 100], title_text='Percentage'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        title_font=dict(size=18, color='black'),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(r=40)  # Add margin to the right
    )

    return fig


# Layout for each section
def create_section(sensor_data):
    emotion_label = "Calm" if sensor_data['SensorPercentage'] < 50 else "Busy"
    emotion_color = "yellow" if sensor_data['SensorPercentage'] < 50 else "red"

    df_sensor = create_df(sensor_data)
    graph = create_complex_graph(df_sensor, sensor_data['SensorDesc'], sensor_data['DataReadTime'])

    alerts = html.Div([
        dbc.Alert("Alert 1: Sample alert message", color="warning"),
        dbc.Alert("Alert 2: Another alert message", color="danger"),
        dbc.Alert("Alert 3: Yet another alert message", color="info")
    ])

    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4(sensor_data['SensorDesc'], className='text-white mb-0'),
                               style={'backgroundColor': '#007bff'}),
                dbc.CardBody([
                    html.P([html.I(className='fas fa-users'), f" Number of people: {sensor_data['NumberInline']}"],
                           className='card-text'),
                    html.P(
                        [html.I(className='fas fa-clock'), f" WaitTime: {sensor_data['ServeTimeFrames'] / 10} Minutes"],
                        className='card-text'),
                    html.P([html.I(className='fas fa-smile'), f" Emotion: {emotion_label}"], className='card-text'),
                    html.Div(style={'backgroundColor': emotion_color, 'width': '100px', 'height': '20px'}),
                ])
            ], color="light"),
        ], width=3, className='mb-4'),
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dcc.Graph(figure=graph, config={'displayModeBar': True}, style={'height': '300px'}),
                    alerts
                ])
            )
        ], width=8, className='mb-4'),  # Adjust width to leave space on the right
        dbc.Col(width=1)  # Empty column for spacing
    ], className='mb-4')


# Create sections for each sensor
sections = [create_section(sensor) for sensor in processed_data]

# Layout of the app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src='/assets/amsys_logo.png', style={'height': '50px'}), width=2),
        dbc.Col(html.H1("POC: Real-time Crowd Intelligence", className='text-center my-4'), width=8),
        dbc.Col(html.Img(src='/assets/royal_commission.jpeg', style={'height': '50px'}), width=2)
    ]),
    html.Hr(),
    *sections
], fluid=True, className='p-4')

# Run the app
# Use the PORT environment variable to set the port
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=True, host='0.0.0.0', port=port)
