""" INTERACTIVE MALAGA VISUALIZATION

    Se pretende desarrollar una herramienta que permita visualizar la saturación 
    de dicha red en sus distintos puntos. Bajo el formato de un mapa de calor, el 
    usuario es capaz de seleccionar la variable observada y el momento del frame 
    para poder interactuar con los datos recogidos y ver su evolución.

"""
## LIBRARIES AND DATA

# Generic libraries
import pandas as pd
import requests
from io import StringIO
import numpy as np
import matplotlib.pyplot as plt
import datetime
import sys, os
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
from os import system

# print(__doc__)
# _ = system('cls')

### DATA EXTRACTION

# Numeric values extraction (excel LVSM_Def.xlsx)
values_column_names = ["time", "branch" , "organization", "substation", "transformer_code", "App SW", 
                        "V_L1", "I_L1", "W_L1", "QL_L1", "QC_L1","cos_L1", "angle_L1",
                        "V_L2", "I_L2", "W_L2", "QL_L2", "QC_L2","cos_L2", "angle_L2",
                        "V_L3", "I_L3", "W_L3", "QL_L3", "QC_L3","cos_L3", "angle_L3",
                        "temp_amb",
                        "aplus_L1", "aminus_L1", "RplusL_L1", "RminusL_L1", "RplusC_L1", "RminusC_L1", 
                        "aplus_L2", "aminus_L2", "RplusL_L2", "RminusL_L2", "RplusC_L2", "RminusC_L2",
                        "aplus_L3", "aminus_L3", "RplusL_L3", "RminusL_L3", "RplusC_L3", "RminusC_L3"]

# Retrieve data on values
script_path = os.path.dirname(__file__)

# Read csv from local file
data_lvsm = pd.read_csv(script_path + '/../DATA/LVSM_Def.csv',  sep = ';', header=0, names=values_column_names)

# Read csv from GitHub
# url_data = 'https://gitlab.com/Ander_gargas/tfm-cic/-/raw/master/Listado_Trafos.csv'
# data_lvsm = pd.read_csv(url_data,  sep = ';', header=0, names=values_column_names, encoding='latin-1')

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


# Numeric values extraction 2 (excel Listado_Trafos.xlsx)
info_column_names = ["ident", "transformer", "substation", "MT_line", "manufacturer", 
                     "model", "series_num", "year", "power", "units", "stato_mat",
                     "lat", "long", "quantity", "family", "number"]

# Retrieve info table  
# Read csv from local file
full_info = pd.read_csv(script_path +'/../DATA/Listado_Trafos.csv', header=0, sep=';', names=info_column_names) 

# Read csv from gitlab files
# url_info = 'https://gitlab.com/Ander_gargas/tfm-cic/-/raw/master/Listado_Trafos.csv'
# full_info = pd.read_csv(url_info,  sep = ';', header=0, names=values_column_names, encoding='latin-1')

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
external_stylesheets = [dbc.themes.CERULEAN]
app = dash.Dash(__name__, title='Malaga Visual Tool', external_stylesheets=external_stylesheets)

# app = dash.Dash(__name__, title='Malaga Visual Tool')
server = app.server
app.config.suppress_callback_exceptions = True

intro_text_esp = """
    **Sobre la App**  
    Esta aplicación pretende mostrar un tablero de control que dé visibilidad sobre la evolución temporal de congestión en la red eléctrica. 
    Hace uso de datos registrados en el pasado de [la base de datos propia de Smart City Malaga](http://malagasmart.malaga.eu/es/habitat-sostenible-y-seguro/energia/smartcity-malaga/#.X6Bar4hKhPY) 
    durante el periodo 2019 - 2020. 

    Para ello, se ruega seleccionar la variable de interés, elegir el instante de la instantanea y de lanzar la visualización para apreciar
    la salud de la malla eléctrica de la ciudad de Málaga a través de los datos registrados en los centros de transformación.
    
"""
intro_text_eng = """
    **About this app**  
    This app implements a visualization dashboard made to get insight on the power network evolution over time. It displays data registered from
    past years from the [Smart City Malaga's dataset of city of Malaga](http://malagasmart.malaga.eu/es/habitat-sostenible-y-seguro/energia/smartcity-malaga/#.X6Bar4hKhPY) 
    during the 2019-2020 period. 

    Select the represented variable from the box menu, click on the button to run the figure and choose the instantaneous snapshot of the
    city electrical grid in terms of congestion throughout their respective transformer centers. 

"""


### LAYOUT OF THE DASH MAP
# Dash App Layout
app.layout = html.Div(  # Global div
    children=[          # Header + user div + heat map + auxiliar figures
        html.Div(       # Header
            children = [
                html.H2(
                    "Malaga Visual Tool",
                    # height='55px',
                    style={
                        'display': 'inline-block',
                        'margin-left': '20px'
                    }
                ),
                html.Img(
                    # src="https://drive.google.com/uc?export=view&id=1m17KAS2GEoGND8UsyvYH8BoqpVQ0hIBg",
                    src='/assets/smart_malaga_logo.png',
                    height='55px',  #55 
                    width='85px',   #85
                    style={
                        'display': 'inline-block',
                        'margin-left': '600px',
                    }
                ),
                html.Img(
                    # src="https://drive.google.com/uc?export=view&id=1zoq8aGDBkMN6gbRcFmGQg1aKpN-0DCdQ",
                    src='/assets/logo_cic.png',
                    height='55px',  #55 
                    width='150px',  #150
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
                'borderBottom': 'thin lightgrey solid',
                'heigth': '70px',
                'background': 'linear-gradient(90deg, lightblue, snow, white)'
            }
            # className="header__title",            # used with CSS to style elements with common properties 
        ),  
               
        html.Div(             # Body block
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

                                html.H4("Malaga Transformer Center", style={'margin-left':'30px'}),
                            ],
                            style = {
                                'text-align': 'justify',
                                'display': 'inline-block',
                                'width': '62%', 
                                'float': 'left',
                                'margin-left' : '10px',
                                'padding': '10px 0 10px 10px'
                            }
                        ),

                        html.Div(           # Right sub-section: User's menu
                            children=[
                                html.H4("Opciones del mapa"),
                                                        
                                html.P("Modo de visualización"),
                                dcc.RadioItems(
                                    id='modo-vista',
                                    options=[{'label': i, 'value': i} for i in [' Imagen', ' Evolución diaria']],
                                    value='Imagen'
                                ),
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
                                                    display_format="D/M/Y",
                                                    style={
                                                        "border": "2px solid black",
                                                    },
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
                                    html.Button(
                                        " Ejecutar ",
                                        id="btn-updt-map",
                                        title="Lanzar la presentación de resultados",
                                        n_clicks=0
                                    )
                                    # dbc.Button(
                                    #     " Ejecutar ",
                                    #     color = "Primary",
                                    #     className="mr-1",
                                    #     block = True,
                                    #     id="btn-updt-map",
                                    #     n_clicks=0
                                    # ),
                                ),
                            ], 
                            style = {
                                'display': 'inline-block',
                                'width': '30%',
                                'margin-left' : '55px',
                                'padding':'5px 5px 5px 5px'
                            }
                        ),

                        html.Br(),
                        html.Hr(style = {'margin-top': '2%', 'margin-right': '1%'})
                    ]
                ),
                
                html.Div(           # Second Division: Heat map
                    children = [
                        dcc.Graph(
                            id="map-graph", 
                            config={"responsive": True},
                            style={
                                'left': '0px',
                                'top' : '0px',
                                'display': 'block'
                            } 
                        )
                    ],
                    style = {
                       'display': 'block',
                       'margin-top' : '0'
                    }
                ),

                html.Div(           # Third Division: histogram + line figure
                    children = [
                        html.Div(           # Top sub-section: CT selection
                            children =[
                                html.P(
                                """Selecciona la subestación:"""
                                ),
                                dcc.RadioItems(
                                    id='modo-hist',
                                    options=[{'label': i, 'value': i} for i in ['Todas', 'Manualmente']],
                                    value='Manualmente'
                                ),
                                dcc.Dropdown(
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
                                    placeholder="Selecciona una subestacion",
                                    multi=True,
                                    value = 'S201'
                                )
                            ],
                            style = {
                                'display': 'block',
                                'width': '40%',
                                'margin-left' : '30%'
                            }
                        ),

                        html.Div(           # Left sub-section: histogram on variable
                            children = [
                                dcc.Graph(id="histogram")
                            ],
                            style = {
                                'display' : 'inline-block',
                                'width' : '45%',
                                'float' : 'left'
                            }
                        ),

                        html.Div(           # Right sub-section: dropdown CT + line figure
                            children = [
                                dcc.Graph(id="line")
                            ],
                            style = {
                                'display' : 'inline-block',
                                'width' : '45%',
                                'margin-left' : '55px'
                            }
                        )
                    ]
                )                  
            ],
        ),
    ],
)



### APP CALLBACKS

# Adapt the menu depending on the selected mode
@app.callback(
    Output("hour-div", "style"), 
    [Input("modo-vista", "value")]
)
def update_div(visual_mode):
    if visual_mode == "Evolución diaria":
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
    date = d.strftime("%Y-%m-%d %H:%M")

    # Generate the list of values to use in later functions
    obs_values = data[data.time == date][['substation',str(variables_dict[variable_items])]]
    obs_values['substation'] = list(map(lambda x: x.replace("S",""), obs_values['substation'].tolist()))     # Getting rid of the "S"

    # Finally, we concat the lat and long to this pd dataframe through our dictionnary
    obs_values["lat"] = list(map(lambda x: trafos_loc[x][0], obs_values["substation"].tolist()))
    obs_values["long"] = list(map(lambda x: trafos_loc[x][1], obs_values["substation"].tolist()))
    obs_values["year"] = list(map(lambda x: info[info.ident == x]["year"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["manufacturer"] = list(map(lambda x: info[info.ident == x]["manufacturer"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["power"] = list(map(lambda x: info[info.ident == x]["power"].tolist()[0], obs_values["substation"].tolist()))    

    # List of transformers having a value
    filled_trafos = list(map(lambda x: x.replace("S",""), data[data.time == date]["substation"].tolist())) 

    # Complete list of tranformers
    full_list_trafos = list(trafos_loc.keys())                                                                

    # List of elements missing their value
    missing_trafos_list = np.setdiff1d(full_list_trafos, filled_trafos)

    # We now fill the list with the data we know from missing trafos, 
    # but putting a 0 in the observed value
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
    fig = px.density_mapbox(obs_values, lat='lat', lon='long', z=variables_dict[variable_items], radius=25,
                            center=dict(lat=36.72016, lon=-4.42034), zoom=12, hover_name='substation', hover_data=['manufacturer','power'],
                            mapbox_style="stamen-terrain")

    # SECOND VERSION: usando Density_mapbox de graph_objects - Pro: Customizable, el tamaño es bueno, Contra: no sé cómo centrarlo en Malaga
    #                                                               ni como ponerle hoverdata
    # fig = go.Figure(
    #     go.Densitymapbox(
    #         lat = obs_values['lat'], lon=obs_values['long'], 
    #         z = obs_values[variables_dict[variable_items]], 
    #         zoom = 5,
    #         radius = 25
    #     )
    # )

    # fig.update_layout(
    #     mapbox_style = "stamen-terrain", 
    #     mapbox_center_lon = -4.42034, mapbox_center_lat = 36.72016,
    #     margin = {"r":40,"t":0,"l":40,"b":40},
    #     # hovertext = obs_values['substation'],
    #     # hoverinfo = [obs_values['manufacturer'],obs_values['power']],
    # )

    fig.update_layout(transition_duration=700)

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

    date_picker_def = dt.strptime(date_picker, '%Y-%m-%d')
    day = date_picker_def.day
    month = date_picker_def.month
    year = date_picker_def.year
    d = datetime.datetime(int(year), int(month), int(day), int(hour_selector))
    date = d.strftime("%Y-%m-%d %H:%M")
    obs_values = data[data.time == date][['substation',str(variables_dict[variable_dropdown])]]
    obs_values['substation'] = list(map(lambda x: x.replace("S",""), obs_values['substation'].tolist()))

    obs_values["lat"] = list(map(lambda x: trafos_loc[x][0], obs_values["substation"].tolist()))
    obs_values["long"] = list(map(lambda x: trafos_loc[x][1], obs_values["substation"].tolist()))
    obs_values["year"] = list(map(lambda x: info[info.ident == x]["year"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["manufacturer"] = list(map(lambda x: info[info.ident == x]["manufacturer"].tolist()[0], obs_values["substation"].tolist()))
    obs_values["power"] = list(map(lambda x: info[info.ident == x]["power"].tolist()[0], obs_values["substation"].tolist()))    

    filled_trafos = list(map(lambda x: x.replace("S",""), data[data.time == date]["substation"].tolist()))
    full_list_trafos = list(trafos_loc.keys())                                                         

    missing_trafos_list = np.setdiff1d(full_list_trafos, filled_trafos)

    temp_list = []
    column_names_missing = obs_values.columns

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
    # fig = px.histogram(obs_values, x=obs_values['substation'], y=variables_dict[variable_dropdown])

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

        substation = ['S201', 'S2274', 'S242', 'S286', 'S287', 'S406', 'S480', 'S499', 'S531', 'S612', 'S68638', 'S7116', 'S733', 'S740', 'S744', 'S76020', 'S813', 'S820', 'S850', 'S868']
        date_new = pd.to_datetime(date_picker, format = '%Y-%m-%d')

        i = 0
        data_complete_fin = pd.DataFrame()

        for i in range(0,len(substation)):
            obs_values = (data_new[data_new.date == date_new][['substation',str(variables_dict[variable_dropdown]),'hour']])
            obs_values = (obs_values[obs_values.substation == substation[i]][['substation',str(variables_dict[variable_dropdown]),'hour']])
            data_complete_fin = data_complete_fin.append(obs_values)
            i+=1

        fig = px.line(data_complete_fin, x='hour', y=variables_dict[variable_dropdown], hover_name='substation', color= 'substation')
    

    else:
        if(variable_dropdown is None):
            variable_dropdown = 'Tension'

        if(substation_dropdown is None):
            substation_dropdown = 'S201'
    
        if type(substation_dropdown) == str : 
            substation_dropdown = [substation_dropdown]

        date_new = pd.to_datetime(date_picker, format = '%Y-%m-%d')

        i = 0
        data_complete = pd.DataFrame()

        for i in range(0,len(substation_dropdown)):
            obs_values = (data_new[data_new.date == date_new][['substation',str(variables_dict[variable_dropdown]),'hour']])
            obs_values = (obs_values[obs_values.substation == substation_dropdown[i]][['substation',str(variables_dict[variable_dropdown]),'hour']])
            data_complete = data_complete.append(obs_values)
            i+=1

        fig = px.line(data_complete, x='hour', y=variables_dict[variable_dropdown], hover_name='substation', color= 'substation')

    
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)


