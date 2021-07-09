""" INTERACTIVE MALAGA VISUALIZATION

    Se pretende desarrollar una herramienta que permita visualizar la saturación 
    de dicha red en sus distintos puntos. Bajo el formato de un mapa de calor, el 
    usuario es capaz de seleccionar la variable observada y el momento del frame 
    para poder interactuar con los datos recogidos y ver su evolución.

"""
## LIBRARIES AND DATA

# Generic libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from os import system
import plotly.express as px

# Specific libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from plotly import graph_objs as go
from datetime import datetime as dt
from datetime import date
from datetime import timedelta

# ML Libraries
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN

# print(__doc__)
# _ = system('cls')

### CONSTANTS
LATENT_SHAPE = 3
EPS = 0.55
N = 20000

###### DATA EXTRACTION
### Numeric values extraction 1 (excel LVSM_Def.xlsx)
values_column_names = ["time", "branch" , "organization", "substation", "transformer_code", "App SW", 
                        "V_L1", "I_L1", "W_L1", "QL_L1", "QC_L1","cos_L1", "angle_L1",
                        "V_L2", "I_L2", "W_L2", "QL_L2", "QC_L2","cos_L2", "angle_L2",
                        "V_L3", "I_L3", "W_L3", "QL_L3", "QC_L3","cos_L3", "angle_L3",
                        "temp_amb",
                        "aplus_L1", "aminus_L1", "RplusL_L1", "RminusL_L1", "RplusC_L1", "RminusC_L1", 
                        "aplus_L2", "aminus_L2", "RplusL_L2", "RminusL_L2", "RplusC_L2", "RminusC_L2",
                        "aplus_L3", "aminus_L3", "RplusL_L3", "RminusL_L3", "RplusC_L3", "RminusC_L3"]

# Read csv from local file
# data_lvsm = pd.read_csv('DATA/LVSM_Def.csv',  sep = ';', header=0, names=values_column_names, encoding='latin-1')

# Read csv from GitHub
data_lvsm = pd.read_csv('https://raw.githubusercontent.com/andres-garcia97/tfm_cic/main/DATA/LVSM_Def.csv',  sep = ';', header=0, names=values_column_names, encoding='latin-1')

# Cleaning data table
data = data_lvsm.drop(["aplus_L1", "aminus_L1", "RplusL_L1", "RminusL_L1", "RplusC_L1", "RminusC_L1", 
                  "aplus_L2", "aminus_L2", "RplusL_L2", "RminusL_L2", "RplusC_L2", "RminusC_L2",
                  "aplus_L3", "aminus_L3", "RplusL_L3", "RminusL_L3", "RplusC_L3", "RminusC_L3"], axis=1)
data = data.reset_index(drop = True)

# Change column types to appropiate
data = data.astype({"time": str, "branch": str , "organization": str, "substation": str, "transformer_code": str, "App SW": str})

data[["V_L1", "I_L1", "W_L1", "QL_L1", "QC_L1","cos_L1", "angle_L1",
      "V_L2", "I_L2", "W_L2", "QL_L2", "QC_L2","cos_L2", "angle_L2",
      "V_L3", "I_L3", "W_L3", "QL_L3", "QC_L3","cos_L3", "angle_L3",
      "temp_amb"]] = data[["V_L1", "I_L1", "W_L1", "QL_L1", "QC_L1","cos_L1", "angle_L1",
                           "V_L2", "I_L2", "W_L2", "QL_L2", "QC_L2","cos_L2", "angle_L2",
                           "V_L3", "I_L3", "W_L3", "QL_L3", "QC_L3","cos_L3", "angle_L3",
                           "temp_amb"]].astype(float)

### Deal with the "24:00" problem. Adapt BOTH the hour and the day. 
# Get the indexes and replace hour
for i, date in enumerate(data['time']):
    if date.split()[1].split(':')[0] == '24':
        data.loc[i, 'time'] = data.loc[i, 'time'].replace("24:00","00:00")
        data.loc[i, 'time'] = pd.to_datetime(data.loc[i, 'time'], format = '%Y-%m-%d %H:%M') + timedelta(days = 1)

# Update the format
data['time'] = pd.to_datetime(data['time'], format = '%Y-%m-%d %H:%M:%S')

# Cleaning NA values
if data.isna().sum().sum() < .10 * len(data): 
    data = data.dropna()
else:
    raise Exception("Careful! Deleting NaN values would cut most of the dataset")

# Remove duplicates
if data.duplicated().sum() < .10 * len(data): 
    data = data.drop_duplicates(subset=['time', 'substation', 'App SW'])
else:
    raise Exception("Careful! Deleting duplicated values would cut most of the dataset")

# Copy of the dataframe to split date and hour
data_new = data.copy(deep=True)

# Split the time column into date and hour columns, for diagram's input preparation
data_new['date'] = (data_new['time']).dt.date
data_new['hour'] = (data_new['time']).dt.time

# Delete the old time column
data_new = data_new.drop(["time"], axis=1)

# Put both columns at the start
data_new = pd.concat([data_new['hour'], data_new.drop('hour',axis=1)], axis=1)
data_new = pd.concat([data_new['date'], data_new.drop('date',axis=1)], axis=1)

# Feature extraction
feat_names = ["V_L1", "I_L1", "W_L1", "QL_L1", "QC_L1"]
X = data_new[feat_names].to_numpy()
date_list = data_new["date"].to_numpy()
hour_list = data_new["hour"].to_numpy()
substation_coding = {v: i for i, v in enumerate(np.unique(data_new[["substation"]]))}
trafo_list = data_new["substation"].map(substation_coding).array

# Standardize Data
sc = StandardScaler()
X_std = sc.fit_transform(X)

### PCA Creation and codings representation on latent space
pca = PCA(n_components = 3, svd_solver='auto')
codings = pca.fit_transform(X_std)



### Numeric values extraction 2 (excel Listado_Trafos.xlsx)
info_column_names = ["ident", "transformer", "substation", "MT_line", "manufacturer", 
                     "model", "series_num", "year", "power", "units", "stato_mat",
                     "lat", "long", "quantity", "family", "number"]

# Retrieve info table  
# Read csv from local file
# full_info = pd.read_csv('DATA/Listado_Trafos.csv', header=0, sep=';', names=info_column_names, encoding='latin-1') 

# Read csv from gitlab files
full_info = pd.read_csv('https://raw.githubusercontent.com/andres-garcia97/tfm_cic/main/DATA/Listado_Trafos.csv', header=0, sep=';', names=info_column_names, encoding='latin-1') 

# Cleaning info table
info = full_info.reset_index(drop = True)

# Change column types to appropiate
info = info.astype({"ident": str, "transformer": str , "substation": str, "MT_line": str, "manufacturer": str, "model": str, "series_num": str, "year": int, "power": int, 
"units": str, "stato_mat": str, "lat": float, "long": float, "quantity": str, "family": str, "number": int})

# Creating a dictionnary with all possible variable to observe
variables_dict = {
    "Tension": "V_L1",
    "Intensidad": "I_L1",
    "Potencia activa": "W_L1",
    "Potencia reactiva cap": "QC_L1",
    "Temperatura ambiente": "temp_amb"
}

variables = list(variables_dict.keys())

# Save the locations of transformers in a dictionary
trafos_loc = {}
for i in range(len(info)):
  trafos_loc[info['ident'][i]] = (info['lat'][i], info['long'][i])


### DASH LAYOUT PREPARATION
# App initialization
app = dash.Dash(__name__, 
    title='Malaga Visual Tool', 
    external_stylesheets=[dbc.themes.CERULEAN],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

server = app.server
app.config.suppress_callback_exceptions = True

intro_text_esp = """
    **Sobre la App**  
    Esta Dashboard basado en Dash plotly ofrece visibilidad sobre la evolución temporal de congestión en la red eléctrica y analiza la existencia de datos anómalos en el pasado. 
    La aplicación hace uso de datos registrados en [la base de datos de Smart City Malaga](http://malagasmart.malaga.eu/es/habitat-sostenible-y-seguro/energia/smartcity-malaga/#.X6Bar4hKhPY) 
    durante el periodo 2019 - 2020. 

    En este tab "Heatmap", seleccionar la variable y fecha de interés. Según la hora escogida, tras ejecutar la visualización se observa la comparativa instantanea en varios formatos para cada uno de los centros y así evaluar la salud de la malla eléctrica de la ciudad de Málaga a través de las mediciones realizadas en ellos.
        
"""
intro_text_eng = """
    **About this app**  
    This Plotly-based dashboard provides insight into the power network evolution over time and analyzes the existence of past outliers. 
    The application displays data stored during past years in the [Smart City Malaga's dataset](http://malagasmart.malaga.eu/es/habitat-sostenible-y-seguro/energia/smartcity-malaga/#.X6Bar4hKhPY) 
    during the 2019 - 2020 period. 

    In this "Heatmap" tab, select the variable and datetime of interest. After executing the app, the instantaneous comparison is diaplyed into many formats for each of the centers, hence possible to evaluate the grid's health. 

"""

intro_outlier_tab_esp = """
    En esta pestaña "Outlier Detection", seleccionar el centro de transformacion y el marco temporal y observar los datos anómalos detectados durante dicho intervalo de tiempo. Dicha detección se basa en un modelo DBSCAN que genera un clustering sobre el conjunto de datos de dicho centro.
    """

intro_outlier_tab_eng = """
    In this "Outlier Detection" tab, select the transformation center and timeframe to observe the outlier data points detected during this period. This detection is based on a DBSCAN clustering algorithm trained on the dataset belonging to this CT. After executing the app, the instantaneous comparison is displayed into many formats for each of the centers, hence possible to evaluate the grid's health. 
    """


### LAYOUT OF THE DASH MAP
# Dash App Layout
app.layout = html.Div(  # Global div
    children=[          # Header + user div + heat map + auxiliar figures
        html.Div(       # Header
            children = [
                html.H2(
                    "Malaga Visual Tool",
                    style={
                        'display': 'inline-block',
                        'margin-left': '2%'
                    }
                ),
                html.Img(
                    # src="https://drive.google.com/uc?export=view&id=1m17KAS2GEoGND8UsyvYH8BoqpVQ0hIBg",
                    src='/assets/smart_malaga_logo.png',
                    height='30%',  #55px 
                    width='6%',   #85px
                    style={
                        'display': 'inline-block',
                        'margin-left': '53%',
                    }
                ),
                html.Img(
                    # src="https://drive.google.com/uc?export=view&id=1zoq8aGDBkMN6gbRcFmGQg1aKpN-0DCdQ",
                    src='/assets/logo_cic.png',
                    height='30%',  #55px 
                    width='10%',  #150px
                    style={
                        'display': 'inline-block',
                    }
                ),
            ],
            style={
                'display': 'flex',
                'flex-direction': 'row',
                'align-items': 'center',
                'justify-content': 'center',
                'heigth': '5%',   # 70px
                'background': 'linear-gradient(90deg, lightblue, snow, white)'
            }
            # className="header_title",            # used with CSS to style elements with common properties 
        ),  

        html.Div(           # Tabs for window selection
            dbc.Tabs(
                [
                    dbc.Tab(label="Heatmap", tab_id="heatmap", tab_style = {'width': '11%', 'textAlign': 'center'}),
                    dbc.Tab(label="Outlier Detector", tab_id="outlier_detect", tab_style = {'width': '11%', 'textAlign': 'center'}),
                ],
                id="body_tabs",
                active_tab="heatmap",
            ),
            style={
                    'display': 'block',
                    'padding-left': '3%',
                    'background': 'linear-gradient(90deg, lightblue, snow, white)'
                }
        ),
               
        html.Div(             # Body block Heatmap
            [   
                html.Div(           # First division: description, title  and user's menu
                    children=[
                        html.Div(           # Left sub-section: Description and title
                            id="intro-text-div", 
                            children = [
                                html.Br(),
                                dcc.Markdown(intro_text_esp), 
                                html.Br(),
                                dcc.Markdown(intro_text_eng),
                                html.Br(),
                                html.H4("Malaga Transformer Center Heatmap", style={'margin-left':'6%'}),   # 30px
                            ],
                            style = {
                                'text-align': 'justify',
                                'display': 'inline-block',
                                'width': '62%', 
                                'float': 'left',
                                'margin-left' : '2%',   #10px
                                'padding': '1%'   #10px
                            }
                        ),

                        html.Div(           # Right sub-section: User's menu
                            children=[
                                html.H4("Opciones del mapa"),
                                html.Br(),                        
                                html.Div(           # Selection of variable and date
                                    children = [
                                        html.Div(
                                            children=[
                                                html.P("Variable seleccionada"),
                                                dcc.Dropdown( 
                                                    id = "variable-dropdown",    # Used to identify the dcc in callbacks
                                                    options=[
                                                        {"label": "Tension", "value": "Tension"},
                                                        {"label": "Intensidad", "value": "Intensidad"},
                                                        {"label": "Potencia activa", "value": "Potencia activa"},
                                                        {"label": "Potencia reactiva capacitiva", "value": "Potencia reactiva cap"},
                                                        {"label": "Temperatura ambiente", "value": "Temperatura ambiente"},
                                                    ],
                                                    value="Intensidad",      # The initial selected value
                                                    placeholder = "Selecciona una variable",
                                                ),
                                            ],
                                            style={
                                                'display': 'inline-block',
                                                'width':'45%'
                                            }
                                        ),
                                        html.Div(
                                            children = [
                                                html.P("Fecha seleccionada"),
                                                dcc.DatePickerSingle(
                                                    id="date-picker",
                                                    min_date_allowed=min(data['time']).date(),
                                                    max_date_allowed=max(data['time']).date(),
                                                    initial_visible_month='2019-06-26',
                                                    date='2019-06-26',
                                                    display_format="D/M/Y"
                                                ),
                                            ],
                                            style={
                                                'display': 'inline-block',
                                                'width':'45%',
                                                'margin-left': '5%',
                                                'float': 'right'
                                            }
                                        )
                                    ]
                                ),
                                html.Br(),
                        
                                html.Div(
                                    id="hour-div",
                                    children=[
                                        html.P("Hora de día"),
                                        dcc.Slider(
                                            id="hour-selector",
                                            min=1, max=24,
                                            marks={
                                                4: "4",
                                                8: "8",
                                                12: "12",
                                                16: "16",
                                                20: "20",
                                                24: "24",
                                            },
                                            value = 10,
                                            tooltip={"placement": "bottom"},
                                        ),
                                    ],
                                ),

                                html.Hr(style = {'margin-top': '1%', 'margin-right': '1%'}),
                                html.P(id="variable-selected"),
                                html.P(id="date-value"),
                                html.P(id="hour-selected"),
                                html.Br(),
                                                        
                                html.Div(
                                    children=[
                                        html.Button(
                                            " Ejecutar ",
                                            id="btn-updt-map",
                                            title="Lanzar la presentación de resultados",
                                            className="button-primary"
                                        )
                                    ],
                                ),
                            ], 
                            style = {
                                'display': 'inline-block',
                                'width': '30%',
                                'margin-left' : '3%',     # 55px
                                'padding':'1%'      # 5px
                            }
                        ),

                        html.Br(),
                        html.Hr(style = {'margin-top': '1%', 'margin-right': '1%', 'margin-left': '1%'})
                    ]
                ),
                
                html.Div(           # Second Division: Heat map
                    children = [
                        dcc.Graph(
                            id="map-graph", 
                        )
                    ],
                ),

                html.Div(           # Third Division: histogram + line figure
                    children = [
                        dbc.Row(           # Top sub-section: CT selection
                            [
                                dbc.Col(html.P(children="""Selecciona la subestación:""", style={'textAlign':'right'}), width = 3),
                                dbc.Col(dcc.RadioItems(
                                            id='modo-hist',
                                            options=[{'label': i, 'value': i} for i in ['Todas', 'Manualmente']],
                                            value='Manualmente',
                                            style={'textAlign':'left'}
                                ), width = 3),
                                dbc.Col(dcc.Dropdown(
                                        id="substation-dropdown",
                                        options=[
                                            {"label": 'S201', "value": 'S201'},
                                            {"label": 'S2274', "value": 'S2274'},
                                            {"label": 'S242', "value": 'S242'},
                                            {"label": 'S286', "value": 'S286'},
                                            {"label": 'S287', "value": 'S287'},
                                            {"label": 'S406', "value": 'S406'},
                                            {"label": 'S480', "value": 'S480'},
                                            {"label": 'S499', "value": 'S499'},
                                            {"label": 'S531', "value": 'S531'},
                                            {"label": 'S612', "value": 'S612'},
                                            {"label": 'S68638', "value": 'S68638'},
                                            {"label": 'S7116', "value": 'S7116'},
                                            {"label": 'S733', "value": 'S733'},
                                            {"label": 'S740', "value": 'S740'},
                                            {"label": 'S744', "value": 'S744'},
                                            {"label": 'S76020', "value": 'S76020'},
                                            {"label": 'S813', "value": 'S813'},
                                            {"label": 'S820', "value": 'S820'},
                                            {"label": 'S850', "value": 'S850'},
                                            {"label": 'S868', "value": 'S868'}
                                        ],
                                        placeholder="Selecciona una o varias subestaciones",
                                        multi=True,
                                        value='S201',
                                        style = {'align': 'left'}
                                    ), width = 4
                                )
                            ], justify = 'center'
                        ),
                        dbc.Row(
                            [
                                dbc.Col(           # Left sub-section: histogram on variable
                                    dcc.Graph(id="histogram"),
                                    width = 6
                                ),

                                dbc.Col(           # Right sub-section: dropdown CT + line figure
                                    dcc.Graph(id="line"),
                                    width = 6
                                )
                            ],
                            no_gutters = True
                        )
                    ]                   
                )              
            ],
            style = {'display': 'block'},
            id = 'body_heatmap'
        ),



        html.Div(             # Body block Outlier Detection
            children = [
                html.Div(           # First division: description, title and user's menu
                    children=[
                        html.Div(           # Left sub-section: Description and title
                            id="intro-text-div-analysis", 
                            children = [
                                html.Br(),
                                dcc.Markdown(intro_outlier_tab_esp), 
                                html.Br(),
                                dcc.Markdown(intro_outlier_tab_eng),
                                html.Br(),
                                html.H4("Malaga Transformer Clustering", style={'margin-left':'6%'}),   # 30px
                            ],
                            style = {
                                'text-align': 'justify',
                                'display': 'inline-block',
                                'width': '55%', 
                                'float': 'left',
                                'margin-left' : '2%',   #10px
                                'padding': '1%'   #10px
                            }
                        ),

                        html.Div(           # Right sub-section: User's menu
                            children=[
                                html.H4("Opciones del Análisis"),
                                html.Br(),                        
                                html.Div(           # Selection of CT and timeframe
                                    children = [
                                        html.Div(       # Selection of the CT
                                            children=[
                                                html.P("Centro de Transformación"),
                                                dcc.Dropdown( 
                                                    id = 'substation-dropdown-analysis',    # Used to identify the dcc in callbacks
                                                    options=[{'label': key, 'value': value} for key, value in substation_coding.items()],
                                                    value = 11,      # The initial selected value
                                                    placeholder = "Selecciona un CT"
                                                ),
                                            ],
                                            style={
                                                'display': 'block'
                                            }
                                        ),
                                        html.Br(),
                                        html.Div(       # Date Range
                                            children = [
                                                html.P("Rango de fechas"),
                                                html.Div(
                                                    dcc.DatePickerRange(
                                                        id="date-picker-range",
                                                        min_date_allowed=min(data['time']).date(),
                                                        max_date_allowed=max(data['time']).date(),
                                                        initial_visible_month='2019-08-01',
                                                        start_date = '2019-08-01',
                                                        end_date = '2019-11-01',
                                                        display_format="D/M/Y"
                                                    )
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                                html.Br(),
                                html.Div(
                                    children=[
                                        html.Button(
                                            " Ejecutar ",
                                            id="btn-updt-outlier",
                                            title="Lanzar la visualización de resultados",
                                            className="button-primary"
                                        )
                                    ],
                                )                                                       
                            ], 
                            style = {
                                'display': 'inline-block',
                                'width': '35%',
                                'margin-left' : '2%',     # 55px
                                'padding':'1%'      # 5px
                            }
                        ),
                        html.Br(),
                        html.Hr(style = {'margin-top': '1%', 'margin-right': '1%', 'margin-left': '1%'})
                    ]
                ),

                html.Div(           # Second Division: Outlier Detection map
                    children = [
                        html.H5(id="CT-selected-analysis", style={'textAlign': 'center', 'width': '80%', 'margin-left': '10%'}),
                        dcc.Graph(
                            id="outlier-3d-graph",
                            style = {
                                'width': '90vw'
                                , 'height': '110vh'
                                , 'margin-left': '6%'
                            } 
                        )
                    ],
                ),
            ],
            style = {'display': 'none'},
            id = 'body_outlier_detect'
        )
    ]
)



### APP CALLBACKS
# Display one of the two tab contents
@app.callback(
   Output(component_id='body_heatmap', component_property='style'),
   Output(component_id='body_outlier_detect', component_property='style'),
   [Input(component_id='body_tabs', component_property='active_tab')])

def update_tab_content(visibility_state):
    if visibility_state == 'heatmap':
        return {'display': 'block'}, {'display': 'none'}
    if visibility_state == 'outlier_detect':
        return {'display': 'none'}, {'display': 'block'}

###  CALLBACKS FROM HEATMAP TAB
# Display Dropdown list on Trafos only when 'Manualmente' is selected, hide if 'Todas' is selected
@app.callback(
    Output("substation-dropdown", "style"), 
    [Input("modo-hist", "value")]
)
def update_div(selection_mode):
    if selection_mode == "Todas":
        return {"display": "none"}
    return {"display": "block"}

# Show the data selected
# Variable selected
@app.callback(
    Output(component_id='variable-selected', component_property='children'),
    [Input(component_id='variable-dropdown', component_property='value')]
)
def update_output_variable(input_value1):
    return 'La variable seleccionada es: {}'.format(input_value1)

# Date selected
@app.callback(
    Output(component_id='date-value', component_property='children'),
    [Input(component_id='date-picker', component_property='date')]
)
def update_output_date(input_value2):
    return 'La fecha seleccionada es: {}'.format(input_value2)

# Hour selected
@app.callback(
    Output(component_id='hour-selected', component_property='children'),
    [Input(component_id='hour-selector', component_property='value')]
)
def update_output_hour(input_value3):
    return 'La hora seleccionada es: {}'.format(input_value3)

# Generate heat map
@app.callback(
    Output('map-graph','figure'),
    [Input('btn-updt-map','n_clicks')],
    [State('date-picker','date'),
     State('hour-selector','value'),
     State('variable-dropdown','value')]
)
def update_map(n_clicks, date_picker, hour_selector, variable_items):
    # Decompose the values of the date
    date_picker_def = dt.strptime(date_picker, '%Y-%m-%d')
    day = date_picker_def.day
    month = date_picker_def.month
    year = date_picker_def.year

    # Rebuild a new datetime frame
    d = datetime.datetime(int(year), int(month), int(day), int(hour_selector))
    # Format it to the desired structure

    # Generate the list of values to use in later functions
    obs_values = data[data.time == pd.Timestamp(d)][['substation',str(variables_dict[variable_items])]]
    obs_values['substation'] = list(map(lambda x: x.replace("S",""), obs_values['substation'].tolist()))     # Getting rid of the "S"

    # Finally, we concat the lat and long to this pd dataframe through our dictionnary
    obs_values["lat"] = list(map(lambda x: trafos_loc[x][0], obs_values["substation"].tolist()))
    obs_values["long"] = list(map(lambda x: trafos_loc[x][1], obs_values["substation"].tolist()))
    obs_values["year"] = list(map(lambda x: info[info.ident == x]["year"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["manufacturer"] = list(map(lambda x: info[info.ident == x]["manufacturer"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["power"] = list(map(lambda x: info[info.ident == x]["power"].tolist()[0], obs_values["substation"].tolist()))    

    # List of transformers having a value
    filled_trafos = list(map(lambda x: x.replace("S",""), data[data.time == pd.Timestamp(d)]["substation"].tolist())) 

    # Complete list of tranformers
    full_list_trafos = list(trafos_loc.keys())                                                                

    # List of elements missing their value
    missing_trafos_list = np.setdiff1d(full_list_trafos, filled_trafos)

    # We now fill the list with the data we know from missing trafos, but putting a 0 in the observed value
    temp_list = []
    column_names_missing = obs_values.columns

    for element in missing_trafos_list:
        temp_list.append([element, 0, trafos_loc[element][0], trafos_loc[element][1],   
                    info[info.ident == element]["year"].tolist()[0],                 
                    info[info.ident == element]["manufacturer"].tolist()[0],         
                    info[info.ident == element]["power"].tolist()[0]])               

    # We now format this list into a panda dataframe
    pd_temp_list = pd.DataFrame(temp_list, columns = column_names_missing)
    
    # And end appending this part to the former list with registered values
    obs_values = obs_values.append(pd_temp_list, ignore_index = True)

    # FIRST VERSION: usando density_mapbox de Plotly Express - Pro: lo hace todo bien, Contra: muy delgado
    # fig = px.density_mapbox(obs_values, lat='lat', lon='long', z=variables_dict[variable_items], radius=25,
    #                         center=dict(lat=36.72016, lon=-4.42034), zoom=12, hover_name='substation', hover_data=['manufacturer','power'],
    #                         mapbox_style="stamen-terrain")

    # SECOND VERSION: usando Density_mapbox de graph_objects - Pro: Customisable, the scope is adaptable to the window size
    fig = go.Figure(
        go.Densitymapbox(
            lat = obs_values['lat'], lon=obs_values['long'], 
            z = obs_values[variables_dict[variable_items]],
            customdata = obs_values['substation'],
            hovertemplate = '<b>CT code: S%{customdata}<br>Value: %{z}</b><extra></extra>',
        )
    )

    fig.update_layout(
        mapbox_style = "stamen-terrain", 
        mapbox_center_lon = -4.42034, mapbox_center_lat = 36.72016,
        margin = {"r": 40,"t": 0,"l": 40,"b": 40},
        mapbox_zoom = 12,
        transition_duration=700
    )

    return fig

#Generate histogram
@app.callback(
    Output("histogram", "figure"),
    [Input("date-picker", "date"),
     Input("hour-selector", "value"),
     Input("variable-dropdown","value"),
     Input("substation-dropdown","value"),
     Input("modo-hist", "value")],
)

def update_histogram(date_picker, hour_selector, variable_dropdown, substation_dropdown, modo_hist):

    # Data Preparation: Generate the appropiate date format then slice data
    date_picker_def = dt.strptime(date_picker, '%Y-%m-%d')
    day = date_picker_def.day
    month = date_picker_def.month
    year = date_picker_def.year
    d = datetime.datetime(int(year), int(month), int(day), int(hour_selector))
    
    obs_values = data[data.time == pd.Timestamp(d)][['substation', str(variables_dict[variable_dropdown])]]
    obs_values['substation'] = list(map(lambda x: x.replace("S",""), obs_values['substation'].tolist()))
    obs_values["lat"] = list(map(lambda x: trafos_loc[x][0], obs_values["substation"].tolist()))
    obs_values["long"] = list(map(lambda x: trafos_loc[x][1], obs_values["substation"].tolist()))
    obs_values["year"] = list(map(lambda x: info[info.ident == x]["year"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["manufacturer"] = list(map(lambda x: info[info.ident == x]["manufacturer"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["power"] = list(map(lambda x: info[info.ident == x]["power"].tolist()[0], obs_values["substation"].tolist()))    

    # Select the trafos with values
    filled_trafos = list(map(lambda x: x.replace("S",""), data[data.time == pd.Timestamp(d)]["substation"].tolist()))
    full_list_trafos = list(trafos_loc.keys())                                                         

    # Those trafos not having data are the difference between all trafos and those with measurement
    missing_trafos_list = np.setdiff1d(full_list_trafos, filled_trafos)

    temp_list = []
    column_names_missing = obs_values.columns

    # When not having measurement, we fill info with 0 everywhere
    for element in missing_trafos_list:
        temp_list.append([element, 0, trafos_loc[element][0], trafos_loc[element][1],   
                    info[info.ident == element]["year"].tolist()[0],                 
                    info[info.ident == element]["manufacturer"].tolist()[0],         
                    info[info.ident == element]["power"].tolist()[0]])               


    pd_temp_list = pd.DataFrame(temp_list, columns = column_names_missing)
    obs_values = obs_values.append(pd_temp_list, ignore_index = True)

    obs_values["substation"].replace({
        '201': 'S201', '2274': 'S2274', '242': 'S242', 
        '286': 'S286', '287': 'S287', '406': 'S406', 
        '480': 'S480', '499': 'S499', '531': 'S531', 
        '612': 'S612', '68638': 'S68638', '7116': 'S7116', 
        '733': 'S733', '740': 'S740', '744': 'S744', 
        '76020': 'S76020', '813': 'S813', '820': 'S820', 
        '850': 'S850', '868': 'S868'
        }, inplace=True)

    
    if (modo_hist == 'Todas'):
        substation = ['S201', 'S2274', 'S242', 'S286', 'S287', 'S406', 'S480', 'S499', 'S531', 'S612', 'S68638', 'S7116', 'S733', 'S740', 'S744', 'S76020', 'S813', 'S820', 'S850', 'S868']
        # We change the colors of those selected
        colors = ['blue',] * len(full_list_trafos)
        selected_indices = [i for i, val in enumerate(obs_values["substation"]) if val in substation]
        for i in selected_indices:
            colors[i] = 'crimson'

    # When Manual Selected
    else:
        if type(substation_dropdown) == str : 
            substation_dropdown = [substation_dropdown]
    
        # We change the colors of those selected
        colors = ['blue',] * len(full_list_trafos)
        selected_indices = [i for i, val in enumerate(obs_values["substation"]) if val in substation_dropdown]
        for i in selected_indices:
            colors[i] = 'crimson'
    
    
    # We create the bar plot
    fig = px.bar(
        obs_values, 
        x = obs_values['substation'], y = variables_dict[variable_dropdown], 
    )

    fig.update_traces(
        marker_color = colors
    )
    
    return fig

# Generate line
@app.callback(
   Output("line", "figure"),
   [Input("date-picker", "date"),
    Input("variable-dropdown", "value"),
    Input("substation-dropdown","value"),
    Input("modo-hist", "value")],
)

def update_line(date_picker, variable_dropdown, substation_dropdown, modo_hist):
    if (modo_hist == 'Todas'):
        if(variable_dropdown is None):
            variable_dropdown = 'Tension'

        # Data preparation: Format inputs, slice and generate obs_values, for the line plot
        substation = ['S201', 'S2274', 'S242', 'S286', 'S287', 'S406', 'S480', 'S499', 'S531', 'S612', 'S68638', 'S7116', 'S733', 'S740', 'S744', 'S76020', 'S813', 'S820', 'S850', 'S868']
        date_new = pd.to_datetime(date_picker, format = '%Y-%m-%d').date()

        data_complete_fin = pd.DataFrame()

        for i in range(0,len(substation)):
            obs_values = (data_new[data_new.date == date_new][['substation',str(variables_dict[variable_dropdown]),'hour']])
            obs_values = (obs_values[obs_values.substation == substation[i]][['substation',str(variables_dict[variable_dropdown]),'hour']])
            data_complete_fin = data_complete_fin.append(obs_values)

        fig = px.line(data_complete_fin, x='hour', y=variables_dict[variable_dropdown], color= 'substation')

        return fig
    
    # When Manual Selected CT
    else:
        if(variable_dropdown is None):
            variable_dropdown = 'Tension'

        if(substation_dropdown is None):
            substation_dropdown = 'S201'
    
        if type(substation_dropdown) == str : 
            substation_dropdown = [substation_dropdown]

        date_new = pd.to_datetime(date_picker, format = '%Y-%m-%d').date()

        data_complete = pd.DataFrame()

        for i in range(0,len(substation_dropdown)):
            obs_values = (data_new[data_new.date == date_new][['substation',str(variables_dict[variable_dropdown]),'hour']])
            obs_values = (obs_values[obs_values.substation == substation_dropdown[i]][['substation',str(variables_dict[variable_dropdown]),'hour']])
            data_complete = data_complete.append(obs_values)

        fig = px.line(data_complete, x='hour', y=variables_dict[variable_dropdown], 
                hover_data={
                    'hour': False
                    , 'substation': False
                }, 
                color= 'substation'
        )

        # Update the background layout so it hovers data based on a vertical line for all present graphs
        fig.update_layout(
            hovermode="x",
            hoverdistance=100,      # Distance to show hover label of data point
            spikedistance=1000,     # Distance to show spike
            xaxis=dict(
                showspikes=True, # Show spike line for X-axis
                
                # Format spike
                spikethickness=2,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="across",
            ),
        )

        return fig



###  CALLBACKS FROM OUTLIER TAB

# Generate message from results and outlier map
@app.callback(
    Output(component_id='outlier-3d-graph', component_property='figure'),
    Output(component_id='CT-selected-analysis', component_property='children'),
    [Input(component_id='btn-updt-outlier', component_property='n_clicks')],
    [State(component_id='substation-dropdown-analysis', component_property='value'),
     State(component_id='date-picker-range', component_property='start_date'),
     State(component_id='date-picker-range', component_property='end_date')]
)
def update_outlier_graph(n_clicks, CT_selection, begin_date, end_date):
    
    ### Preparation of data
    dt_begin_date = dt.strptime(begin_date, '%Y-%m-%d').date()
    dt_end_date = dt.strptime(end_date, '%Y-%m-%d').date()

    # PCA codings for points belonging to this CT
    codings_CT = codings[trafo_list == CT_selection]

    # Dates of data points belonging to this CT
    date_list_CT = date_list[trafo_list == CT_selection]
    hour_list_CT = hour_list[trafo_list == CT_selection]

    # Coding of the points both being from the CT and inside the Date Range
    codings_selected = codings[(trafo_list == CT_selection) & (dt_begin_date <= date_list) & (date_list <= dt_end_date)]

    # Get the name of the CT from its encoded value in the dictionary
    CT_name = list(substation_coding.keys())[list(substation_coding.values()).index(CT_selection)]

    # Fit of the model
    db = DBSCAN(eps = EPS, min_samples = 0.005 * len(codings_CT)).fit(codings_CT)
    # Labels predicting clusters and outliers, giving to these last a -1 value
    labels = db.labels_

    indices_outliers = np.where(labels == -1)

    # If there were no outliers detected
    if np.where(labels == -1)[0].size == 0:
        n_outlier = 0
        msg = ('\nAmong the dates {} and {}, {} points were found in total belonging to the CT {}. Among these, none of them are outliers.\n'.format(dt_begin_date.strftime("%Y-%m-%d"), dt_end_date.strftime("%Y-%m-%d"), len(codings_selected), CT_name))

    else:    
        n_outlier = len(indices_outliers)
        msg = ('\nAmong the dates {} and {}, {} points were found in total belonging to the CT {}. Among these, {} of them are outliers.\n'.format(dt_begin_date.strftime("%Y-%m-%d"), dt_end_date.strftime("%Y-%m-%d"), len(codings_selected), CT_name, n_outlier))

    # Filter data in 3 different arrays
    codings_not_selected = codings_CT[(dt_begin_date >= date_list_CT) | (date_list_CT >= dt_end_date)]
    codings_inlier = codings_CT[(labels != -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)]
    codings_outlier = codings_CT[(labels == -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)]

    # We stack horizontally the codings, date (as a string) joined to hour and type of each point, useful for including hoverlabels and other properties in the visualization
    codings_not_selected = np.hstack((
        codings_not_selected, 
        np.reshape([x.strftime('%m/%d/%Y') + y.strftime(' %H:%M') for x, y in zip(date_list_CT[(dt_begin_date >= date_list_CT) | (date_list_CT >= dt_end_date)], hour_list_CT[(dt_begin_date >= date_list_CT) | (date_list_CT >= dt_end_date)])], (len(codings_not_selected), 1)), 
        np.reshape(['not_selected']*len(codings_not_selected), (len(codings_not_selected), 1))))

    codings_inlier = np.hstack((
        codings_inlier, 
        np.reshape([x.strftime('%m/%d/%Y') + y.strftime(' %H:%M') for x, y in zip(date_list_CT[(labels != -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)], hour_list_CT[(labels != -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)])], (len(codings_inlier), 1)), 
        np.reshape(['inlier']*len(codings_inlier), (len(codings_inlier), 1))))

    codings_outlier = np.hstack((
        codings_outlier, 
        np.reshape([x.strftime('%m/%d/%Y') + y.strftime(' %H:%M') for x, y in zip(date_list_CT[(labels == -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)], hour_list_CT[(labels == -1) & (dt_begin_date <= date_list_CT) & (date_list_CT <= dt_end_date)])], (len(codings_outlier), 1)), 
        np.reshape(['outlier']*len(codings_outlier), (len(codings_outlier), 1))))

    # Generate the df, with column names and types
    if np.where(labels == -1)[0].size == 0:
        df = pd.DataFrame(np.concatenate((codings_not_selected, codings_inlier), axis=0), columns = ['C1', 'C2', 'C3', 'date', 'type']).astype({'C1': float, 'C2': float, 'C3': float, 'date': str, 'type': str})
    else:
        df = pd.DataFrame(np.concatenate((codings_not_selected, codings_inlier, codings_outlier), axis=0), columns = ['C1', 'C2', 'C3', 'date', 'type']).astype({'C1': float, 'C2': float, 'C3': float, 'date': str, 'type': str})

    # Mappings of attributes
    symbol = {'not_selected': 'circle', 'inlier': 'circle', 'outlier': 'cross'}
    color = {'not_selected': 'rgb(0, 0, 200)', 'inlier': 'rgb(0, 200, 0)', 'outlier': 'rgb(200, 0, 0)'}
    size_dict = {'not_selected': 0.25, 'inlier': 1, 'outlier': 3}
    
    df['size'] = np.vectorize(size_dict.get)(df['type']).tolist()

    # Generate the 3D scatter plot
    fig = px.scatter_3d(df, x='C1', y='C2', z='C3', 
                        size = 'size',
                        color = 'type',
                        color_discrete_map = color,
                        symbol = 'type',
                        symbol_map = symbol,
                        hover_name = 'date',
                        hover_data = {
                            'type': True,
                            'C1': False,
                            'C2': False,
                            'C3': False,
                            'size': False,
                        }
                    )
        
    return fig, msg


if __name__ == "__main__":
    app.run_server(debug=True)


