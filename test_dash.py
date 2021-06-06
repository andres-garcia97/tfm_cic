# Test for dash format

# Specific libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

### DASH LAYOUT PREPARATION
# App initialization
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# ['https://drive.google.com/file/d/10y4q6NMvh--UmzFl88f2ImOuo_narSkw/view?usp=sharing']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True
