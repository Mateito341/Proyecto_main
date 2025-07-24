# Importar librerías necesarias
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
import sqlite3

def obtener_datos_mapa():
    conn = sqlite3.connect("ensayos.db")
    query = """
        SELECT 
            u.latitude, 
            u.longitude, 
            u.farm, 
            c.name AS cliente
        FROM ubicacion u
        LEFT JOIN ensayos e ON u.ensayo_id = e.ensayo_id
        LEFT JOIN clientes c ON e.cliente_id = c.cliente_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obtener_datos_aplico():
    conn = sqlite3.connect("ensayos.db")
    query = """
        SELECT 
            p.speed,
            m.sens AS sensitivity,
            r.weed_applied
        FROM pulverizadora p
        JOIN ensayos e ON p.ensayo_id = e.ensayo_id
        JOIN resultados_malezas r ON e.ensayo_id = r.ensayo_id
        LEFT JOIN modelo_deteccion m ON e.ensayo_id = m.ensayo_id
        WHERE r.weed_applied IS NOT NULL 
        AND (p.speed IS NOT NULL OR m.sens IS NOT NULL)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Convertir sensibilidad a entero y filtrar solo valores 1, 2, 3
    if 'sensitivity' in df.columns:
        df['sensitivity'] = pd.to_numeric(df['sensitivity'], errors='coerce')
        df = df[df['sensitivity'].isin([1, 2, 3]) | df['sensitivity'].isna()]
    return df

# Obtener datos
df_mapa = obtener_datos_mapa()
df_aplico = obtener_datos_aplico()

# Crear figura del mapa
fig_mapa = px.scatter_map(
    df_mapa,
    lat="latitude",
    lon="longitude",
    hover_name="cliente",
    hover_data=["farm"],
    zoom=4,
    height=500
)
fig_mapa.update_layout(margin={"r":0, "t":0, "l":0, "b":0})

# Inicializar la app
app = Dash(__name__)

# Definir layout
app.layout = html.Div([
    html.H1("Ubicaciones de Clientes"),
    html.Hr(),
    
    dcc.Graph(
        id='mapa-clientes',
        figure=fig_mapa,
        style={'marginBottom': '50px'}
    ),
    
    html.H2("Tabla de ubicaciones"),
    dash_table.DataTable(
        data=df_mapa.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_mapa.columns],
        page_size=6
    ),

    # Gráfico de aplicación
    html.H1("Aplicación de Pulverizadora"),
    html.Hr(),
    dcc.RadioItems(
        options=[
            {'label': 'Velocidad de avance (km/h)', 'value': 'speed'},
            {'label': 'Nivel de sensibilidad (1-3)', 'value': 'sensitivity'}
        ],
        value='speed',
        id='tipo-grafico-radio',
        inline=True,
        style={'marginBottom': '20px'}
    ),
    
    dcc.Graph(
        id='grafico-aplicacion'
    )
])

@callback(
    Output('grafico-aplicacion', 'figure'),
    Input('tipo-grafico-radio', 'value')
)
def actualizar_grafico(tipo_grafico):
    if tipo_grafico == 'speed':
        # Crear rangos de velocidad
        df_aplico['rango'] = pd.cut(df_aplico['speed'], bins=[0, 5, 10, 15, 20, 25], 
                                   labels=["0-5", "5-10", "10-15", "15-20", "20-25"])
        titulo = "Aplicación de herbicida según velocidad de avance"
        etiqueta_x = "Rango de velocidad (km/h)"
    else:
        # Usar valores discretos de sensibilidad
        df_aplico['rango'] = df_aplico['sensitivity'].astype(str)
        titulo = "Aplicación de herbicida según nivel de sensibilidad"
        etiqueta_x = "Nivel de sensibilidad (1-3)"
    
    fig = px.histogram(
        df_aplico.dropna(subset=['rango']),
        x='rango',
        color='weed_applied',
        barmode='stack',
        labels={'weed_applied': 'Aplicado', 'rango': etiqueta_x},
        category_orders={"weed_applied": [0, 1], 
                        "rango": ["1", "2", "3"] if tipo_grafico == 'sensitivity' else None},
        title=titulo
    )
    
    fig.update_layout(
        xaxis_title=etiqueta_x,
        yaxis_title="Cantidad de Malezas",
        xaxis={'type': 'category'}
    )
    
    return fig

# Ejecutar
if __name__ == '__main__':
    app.run(debug=True)