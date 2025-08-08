# Punto de entrada principal de la aplicación Dash
from dash import Dash, html, dcc, dash_table
from database import obtener_datos_malezas, obtener_datos_mapa, obtener_datos_aplico
from visualization import crear_mapa, crear_grafico
from components import filtros_layout
from callbacks import register_callbacks

# Obtener datos iniciales
df_malezas = obtener_datos_malezas()
df_mapa = obtener_datos_mapa()
df_aplico = obtener_datos_aplico()

# Crear la aplicación Dash
app = Dash(__name__)

# Configurar el layout principal
app.layout = html.Div([
    # Sección del mapa
    html.H1("Ubicaciones de Clientes"),
    html.Hr(),
    
    dcc.Graph(
        id='mapa-clientes',
        figure=crear_mapa(df_mapa),
        style={'marginBottom': '50px'}
    ),
    
    html.H2("Tabla de ubicaciones"),
    dash_table.DataTable(
        data=df_mapa.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_mapa.columns],
        page_size=6
    ),

    # Sección de análisis con filtros
    html.H1("Análisis de Aplicación"),
    html.Hr(),
    filtros_layout(df_aplico, df_malezas),
    
    # Gráficos en filas
    html.Div([
        html.Div([dcc.Graph(id='grafico-velocidad')], 
                style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='grafico-sensibilidad')], 
                style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([dcc.Graph(id='grafico-tamano')], 
                style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='grafico-ubicacion')], 
                style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([dcc.Graph(id='grafico-baldosa')], 
                style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='grafico-velocidad-viento')], 
                style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([dcc.Graph(id='grafico-tipo')], 
                style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='grafico-especie')], 
                style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.Div([
        html.Div([dcc.Graph(id='grafico-nombre')], 
                style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='grafico-diameter')], 
                style={'width': '49%', 'display': 'inline-block'})
    ]),

    # Botón de descarga
    html.Div([
        html.Button(
            "Descargar datos de malezas filtrados", 
            id="btn-descargar-malezas",
            style={
                'margin': '10px', 
                'padding': '10px',
                'background-color': '#008148', 
                'color': 'white',
                'border': 'none', 
                'border-radius': '5px',
                'cursor': 'pointer'
            }
        ),
        dcc.Download(id="download-malezas-filtradas")
    ], style={'text-align': 'center', 'margin': '20px'})
])

# Registrar todos los callbacks
register_callbacks(app, df_malezas)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True, port=8050)