import pandas as pd
import numpy as np
import dash
from jupyter_dash import JupyterDash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import psycopg2
from sqlalchemy import create_engine
import os
import pymongo
from bson.json_util import loads, dumps
postgres_password = os.environ['POSTGRES_PASSWORD']
mongo_username = os.environ['MONGO_INITDB_ROOT_USERNAME']
mongo_password = os.environ['MONGO_INITDB_ROOT_PASSWORD']
mongo_init_db = os.environ['MONGO_INITDB_DATABASE']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

engine = create_engine("postgresql+psycopg2://{user}:{pw}@postgres:5432/{db}"
                       .format(user="postgres", pw=postgres_password, db="contrans"))

myclient = pymongo.MongoClient(f"mongodb://{mongo_username}:{mongo_password}@mongo:27017/{mongo_init_db}?authSource=admin")
contrans_db = myclient['contrans']
bills = contrans_db['bills']

myquery = '''
SELECT *
FROM members
'''
members = pd.read_sql_query(myquery, con=engine)
members['last_name'] = [x.title() for x in members['last_name']]
members['full_name'] = members['first_name'] + ' ' + members['last_name'] + ' (' + members['party'] + '-' + members['state'] + ')'


app = JupyterDash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
[
    html.H1("Congress Transparency Dashboard"),
    
    dcc.Dropdown(id = 'member',
                options = [{'label': x, 'value': y} for x, y in zip(members['full_name'], members['propublica_id'])],
                value = 'A000370'),
    
    dcc.Tabs([
        
            dcc.Tab(label='Ideology and Contact Info', children = [
                html.Div([dcc.Markdown(id = 'membertable')], style={'width': '32%', 'float': 'left'}),   

                html.Div([dcc.Graph(id = 'membergraph')], style={'width': '65%', 'float': 'right'}),

        ]),

        dcc.Tab(label='Characteristic Words', children = [
            
            html.Div([
                dcc.Markdown('**The following words best describe the bills that this person has sponsored:**'),
                dcc.Markdown(id = 'charwords')
            ], style={'width': '32%', 'float': 'left'}),
            
            html.Div([
                dcc.Markdown('**This individual has sponsored the following bills:**'),
                dcc.Markdown(id = 'bills')
            ], style={'width': '65%', 'float': 'right'})
        
    ])   
        
    ])
    
 
    
]

)

@app.callback(Output(component_id = 'membergraph', component_property = 'figure'), 
              Input(component_id = 'member', component_property = 'value'))

def membergraph(propub):
    df = members.query(f"propublica_id == '{propub}'")

    fig = px.scatter(members, x = 'DWNOMINATE', y = 'votes_with_party_pct',
                    labels = {'DWNOMINATE':'Left/Right Political Ideology',
                             'votes_with_party_pct':'Percent of time votes with majority of their party'},
                    height = 800, width=1200,
                    color = 'party',
                    symbol = 'chamber',
                    opacity = .5,
                    hover_data = ['full_name'])

    fig.add_traces(go.Scatter(x=df['DWNOMINATE'], y=df['votes_with_party_pct'],
                              marker = dict(size = 12),
                             marker_symbol = 'star'))

    return fig

@app.callback(Output(component_id = 'membertable', component_property = 'children'), 
              Input(component_id = 'member', component_property = 'value'))

def membertable(propub):
    members['memselect'] = members['propublica_id'] == propub
    members['memselectsize'] = 1 + (14*(members['memselect']))
    disp = members.query("memselect==True")
    disp = disp[['title', 'full_name', 'state', 'district', 'party', 'gender',
            'date_of_birth', 'leadership_role', 'url', 'DWNOMINATE', 'seniority', 
            'next_election', 'total_votes', 'missed_votes', 'votes_with_party_pct']]
    disp = disp.T
    disp.columns = ['']
    return disp.to_markdown()
    
@app.callback(Output(component_id = 'charwords', component_property = 'children'), 
              Input(component_id = 'member', component_property = 'value'))

def charwords(propub):
    
    myquery = f'''
    SELECT word, tf_idf
    FROM charwords
    WHERE sponsor_id = '{propub}'
    ORDER BY tf_idf DESC;
    '''
    tab = pd.read_sql_query(myquery, con=engine)
    
    return tab.to_markdown()


@app.callback(Output(component_id = 'bills', component_property = 'children'), 
              Input(component_id = 'member', component_property = 'value'))

def getbills(propub):
    myquery = bills.find({'sponsor_id': propub}, 
                     {'_id': 0,
                     'nunber': 1,
                     'title': 1,
                     'house_passage': 1,
                     'senate_passage': 1,
                     'enacted':1,
                     'latest_major_action':1,
                     'congressdotgov_url': 1})
    tab = pd.DataFrame.from_records(loads(dumps(myquery)))
    return tab.to_markdown()
    
if __name__== "__main__":
    app.run_server(mode= 'external', host = "0.0.0.0", debug=True)