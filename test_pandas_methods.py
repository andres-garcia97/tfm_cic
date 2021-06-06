# Generic libraries
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
import datetime
import sys, os
import plotly.express as px

from plotly import graph_objs as go
from datetime import datetime as dt
from datetime import date
from datetime import timedelta
from os import system

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

begin_time = datetime.datetime.now()

# data_lvsm = pd.read_excel(script_path + '/../DATA/LVSM_Def.xlsx',  engine='openpyxl', header=0, names=values_column_names)
data_lvsm = pd.read_csv(script_path + '/../DATA/LVSM_Def.csv',  sep = ';', header=0, names=values_column_names)
print(datetime.datetime.now() - begin_time)

data_lvsm.head()