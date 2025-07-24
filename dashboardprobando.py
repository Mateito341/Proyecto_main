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
    df = df_aplico.copy()
    
    if tipo_grafico == 'speed':
        df['rango'] = pd.cut(df['speed'], bins=[0, 5, 10, 15, 20, 25], 
                             labels=["0-5", "5-10", "10-15", "15-20", "20-25"])
        titulo = "Porcentaje de malezas aplicadas según velocidad"
        etiqueta_x = "Rango de velocidad (km/h)"
    else:
        df['rango'] = df['sensitivity'].astype(str)
        titulo = "Porcentaje de malezas aplicadas según sensibilidad"
        etiqueta_x = "Nivel de sensibilidad (1-3)"
    
    df = df.dropna(subset=['rango', 'weed_applied'])

    # Agrupar y calcular porcentaje
    grupo = df.groupby(['rango', 'weed_applied']).size().reset_index(name='count')
    total_por_rango = grupo.groupby('rango')['count'].transform('sum')
    grupo['percentage'] = grupo['count'] / total_por_rango * 100

    # Reemplazar valores para mostrar etiquetas legibles
    grupo['Aplicado'] = grupo['weed_applied'].replace({0: 'No aplicado', 1: 'Aplicado'})

    # Forzar orden deseado (Aplicado abajo, No aplicado arriba)
    orden_apilado = ['Aplicado', 'No aplicado']

    fig = px.bar(
        grupo,
        x='rango',
        y='percentage',
        color='Aplicado',
        labels={'rango': etiqueta_x, 'percentage': 'Porcentaje'},
        title=titulo,
        barmode='stack',
        category_orders={'Aplicado': ['Aplicado', 'No aplicado']},
        color_discrete_map={
                'Aplicado': "#14b91c",                     # Verde fuerte
                'No aplicado': 'rgba(46, 125, 50, 0.2)'     # Verde claro y transparente
            }
    )

    fig.update_layout(
        yaxis=dict(title='Porcentaje (%)', range=[-10, 100]),  # espacio extra abajo
        xaxis=dict(title=etiqueta_x, type='category'),
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        margin=dict(b=80)  # margen inferior para que no se corte
    )

    fig.add_shape(
        type='line',
        x0=-0.5,
        x1=len(grupo['rango'].unique()) - 0.5,
        y0=90,
        y1=90,
        line=dict(color='red', width=2, dash='dash'),
        xref='x',
        yref='y'
    )

    totales = grupo.groupby('rango')['count'].sum().reset_index()
    for i, row in totales.iterrows():
        fig.add_annotation(
            x=row['rango'],
            y=-5,  # debajo del eje
            text=f"{int(row['count'])} ensayos",
            showarrow=False,
            font=dict(size=12, color='gray'),
            yanchor='top'
    )

    return fig


# Ejecutar
if __name__ == '__main__':
    app.run(debug=True)