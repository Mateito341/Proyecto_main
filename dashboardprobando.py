import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# 1. Inicializar la aplicación
app = dash.Dash(__name__)

# 2. Cargar datos (ejemplo)
df = pd.DataFrame({
    "Fruit": ["Manzanas", "Naranjas", "Plátanos", "Manzanas", "Naranjas", "Plátanos"],
    "Cantidad": [4, 1, 2, 2, 4, 5],
    "Ciudad": ["SF", "SF", "SF", "NY", "NY", "NY"]
})

# 3. Crear figuras/gáficos
fig1 = px.bar(df, x="Fruit", y="Cantidad", color="Ciudad", barmode="group")
fig2 = px.pie(df, values="Cantidad", names="Fruit")

# 4. Diseño del layout
app.layout = html.Div(children=[
    html.H1(children='Mi Primer Dashboard'),
    
    html.Div(children='''
        Un dashboard de ejemplo con Dash.
    '''),
    
    dcc.Graph(
        id='graph1',
        figure=fig1
    ),
    
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in df['Ciudad'].unique()],
        value='SF'
    ),
    
    dcc.Graph(
        id='graph2',
        figure=fig2
    )
])

# 5. Callbacks para interactividad
@app.callback(
    Output('graph2', 'figure'),
    [Input('dropdown', 'value')]
)
def update_figure(selected_city):
    filtered_df = df[df['Ciudad'] == selected_city]
    fig = px.pie(filtered_df, values="Cantidad", names="Fruit")
    return fig

# 6. Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)