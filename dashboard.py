# Importar librerías necesarias
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px # Contruir gráficos
import dash_design_kit as ddk

# dcc: incluye componentes graficos
# html: incluye componentes de HTML
# dash_table: incluye componentes de tablas
# dash: es el framework principal


# Incorporar datos
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')

# Inicializar la aplicación Dash
app = Dash()

# Definir el layout de la aplicación
# App layout
app.layout = [
    html.Div(children='My First App with Data, Graph, and Controls'),
    html.Hr(),
    dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='controls-and-radio-item'),
    dash_table.DataTable(data=df.to_dict('records'), page_size=6),
    dcc.Graph(figure={}, id='controls-and-graph')
]

# Add controls to build the interaction
@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
def update_graph(col_chosen):
    fig = px.histogram(df, x='continent', y=col_chosen, histfunc='avg')
    return fig

# Correr la aplicación
if __name__ == '__main__':
    app.run(debug=True)
