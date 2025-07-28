# Importar librerías necesarias
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
                    m.tile,
                    r.weed_applied,
                    r.size,
                    r.weed_placement,
                    r.weed_name,
                    r.weed_type,
                    c.crop_specie,
                    ca.wind_speed
                FROM pulverizadora p
                JOIN ensayos e ON p.ensayo_id = e.ensayo_id
                JOIN resultados_malezas r ON e.ensayo_id = r.ensayo_id
                LEFT JOIN modelo_deteccion m ON e.ensayo_id = m.ensayo_id
                LEFT JOIN condiciones_ambientales ca ON e.ensayo_id = ca.ensayo_id
                LEFT JOIN cultivo c ON e.ensayo_id = c.ensayo_id
                WHERE r.weed_applied IS NOT NULL 
                AND (p.speed IS NOT NULL OR m.sens IS NOT NULL)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Convertir sensibilidad a entero y filtrar solo valores 1, 2, 3
    if 'sensitivity' in df.columns:
        df['sensitivity'] = pd.to_numeric(df['sensitivity'], errors='coerce')
        df = df[df['sensitivity'].isin([1, 2, 3]) | df['sensitivity'].isna()]

    if 'tile' in df.columns:
        df['tile'] = pd.to_numeric(df['tile'], errors='coerce')
        df = df[df['tile'].isin([1, 2, 3]) | df['tile'].isna()]
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

# Función para crear gráficos
def crear_grafico(tipo_grafico, df, variable_analisis='weed_applied'):
    if tipo_grafico == 'speed':
        df['rango'] = pd.cut(df['speed'], bins=[0, 5, 10, 15, 20, 25], 
                           labels=["0-5", "5-10", "10-15", "15-20", "20-25"])
        titulo = f"Por velocidad de avance (km/h)"
        etiqueta_x = "Rango de velocidad de"
    elif tipo_grafico == 'sensitivity':
        df = df.dropna(subset=['sensitivity'])
        df['rango'] = df['sensitivity'].astype(int).astype(str)
        titulo = f"Por sensibilidad (1-3)"
        etiqueta_x = "Nivel de sensibilidad"
    elif tipo_grafico == 'size':
        df['size'] = pd.to_numeric(df['size'], errors='coerce')  # Forzar a numérico, NaN si no se puede
        df = df.dropna(subset=['size'])  # Eliminar filas donde no se pudo convertir
        df['rango'] = pd.cut(df['size'], bins=[0, 5, 10, 15, 20, 25], 
                            labels=["0-5", "5-10", "10-15", "15-20", "20-25"])
        titulo = f"Por tamaño de maleza (cm)"
        etiqueta_x = "Tamaño"
    elif tipo_grafico == 'weed_placement':
        df = df.dropna(subset=['weed_placement'])
        df['rango'] = df['weed_placement'].astype(str)
        titulo = f"Por ubicación de maleza"
        etiqueta_x = "Ubicación"
    elif tipo_grafico == 'tile':
        df = df.dropna(subset=['tile'])
        df['rango'] = df['tile'].astype(int).astype(str)
        titulo = f"Por baldosa (1-3)"
        etiqueta_x = "Nivel de baldosa"
    elif tipo_grafico == 'wind_speed':
        df['rango'] = pd.cut(df['wind_speed'], bins=[0, 5, 10, 15, 20, 25], 
                           labels=["0-5", "5-10", "10-15", "15-20", "20-25"])
        titulo = f"Por velocidad del viento (km/h)"
        etiqueta_x = "Rango de velocidad"
    elif tipo_grafico == 'weed_type':
        df = df.dropna(subset=['weed_type'])
        df['rango'] = df['weed_type'].astype(str)
        titulo = f"Por tipo de maleza"
        etiqueta_x = "Tipo"
    elif tipo_grafico == 'weed_name':
        df = df.dropna(subset=['weed_name'])
        df['rango'] = df['weed_name'].astype(str)
        titulo = f"Por nombre de maleza"
        etiqueta_x = "Nombre de maleza"
    elif tipo_grafico == 'crop_specie':
        df = df.dropna(subset=['crop_specie'])
        df['rango'] = df['crop_specie'].astype(str)
        titulo = f"Por especie de cultivo"
        etiqueta_x = "Especie de cultivo"


    
    df = df.dropna(subset=['rango', variable_analisis])

    # Cálculo de métricas
    if variable_analisis == 'weed_applied':
        metricas = df.groupby('rango', observed=False)[variable_analisis].mean() * 100
    else:
        metricas = df.groupby('rango', observed=False)[variable_analisis].mean()
    
    counts = df.groupby('rango', observed=False).size()
    
    # Para categorías conocidas, asegurar todas están presentes
    if tipo_grafico == 'sensitivity':
        niveles_completos = ['1', '2', '3']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)

    # Para categorías conocidas, asegurar todas están presentes
    if tipo_grafico == 'weed_type':
        niveles_completos = ['HA', 'G']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)

    if tipo_grafico == 'tile':
        niveles_completos = ['1', '2', '3']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)

    if tipo_grafico == 'weed_placement':
        niveles_completos = ['ROW', 'FURROW']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    
    plot_data = pd.DataFrame({
        'rango': metricas.index,
        'valor': metricas.values,
        'count': counts.values
    })
    
    if tipo_grafico == 'speed':
        plot_data = plot_data.sort_values('rango')

    if tipo_grafico == 'wind_speed':
        plot_data = plot_data.sort_values('rango')

    if tipo_grafico == 'size':
        plot_data = plot_data.sort_values('rango')

    fig = go.Figure()

    # Gráfico de barras principal verdes
    fig.add_trace(go.Bar(
        x=plot_data['rango'],
        y=plot_data['valor'],
        name=variable_analisis.replace('_', ' '),
        marker_color='#008148',
        text=[f"{v:.1f}%" if variable_analisis == 'weed_applied' else f"{v:.1f}" 
            for v in plot_data['valor']],
        textposition='auto',
        width=0.5,
        hoverinfo='x+y',
    ))

    # Grafico de tendencia naranja
    datos_con_valores = plot_data[plot_data['valor'] > 0]
    if len(datos_con_valores) > 1:
        fig.add_trace(go.Scatter(
            x=datos_con_valores['rango'],
            y=datos_con_valores['valor'],
            mode='lines+markers',
            name='Tendencia',
            line=dict(color='#EF8A17', width=3),
            marker=dict(size=8)
        ))

    if variable_analisis == 'weed_applied':
        fig.add_shape(
            type='line',
            x0=-0.5,
            x1=len(plot_data['rango']) - 0.5,
            y0=90,
            y1=90,
            line=dict(color='red', width=2, dash='dash'),
            xref='x',
            yref='y'
        )

    if tipo_grafico == 'sensitivity':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['1', '2', '3']
        )

    if tipo_grafico == 'tile':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['1', '2', '3']
        )

    if tipo_grafico == 'weed_placement':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['ROW', 'FURROW']
        )

    if tipo_grafico == 'weed_type':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['HA', 'G']
        )

    # Nota de porcentaje y cantdida de ensayos
    fig.data[0].hovertemplate = (
        f"<b>%{{x}}</b><br>"
        f"{variable_analisis.replace('_', ' ').title()}: %{{y:.1f}}"
        f"{'%' if variable_analisis == 'weed_applied' else ''}<br>"
        "Cantidad de malezas: %{customdata[0]}<extra></extra>"
    )

    fig.data[0].customdata = plot_data[['count']].values
        
    fig.update_layout(
        title=titulo,
        xaxis_title=etiqueta_x,
        yaxis_title=variable_analisis.replace('_', ' ').title() + 
                (' (%)' if variable_analisis == 'weed_applied' else ''),
        yaxis=dict(range=[-10, 105] if variable_analisis == 'weed_applied' else None),
        margin=dict(b=100, t=50),
        height=400
    )

    return fig

# Crear todos los gráficos
fig_velocidad = crear_grafico('speed', df_aplico.copy())
fig_sensibilidad = crear_grafico('sensitivity', df_aplico.copy())
fig_tamano = crear_grafico('size', df_aplico.copy())
fig_ubicacion = crear_grafico('weed_placement', df_aplico.copy())
fig_baldosa = crear_grafico('tile', df_aplico.copy())
fig_velocidad_viento = crear_grafico('wind_speed', df_aplico.copy())
fig_tipo = crear_grafico('weed_type', df_aplico.copy())
fig_nombre = crear_grafico('weed_name', df_aplico.copy())
fig_especie = crear_grafico('crop_specie', df_aplico.copy())

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

    # Gráficos de aplicación uno al lado del otro
    html.H1("Análisis de Aplicación"),
    html.Hr(),
    html.Div([
        html.Div([
            dcc.Graph(
                id='grafico-velocidad',
                figure=fig_velocidad
            )
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(
                id='grafico-sensibilidad',
                figure=fig_sensibilidad
            )
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    # Segunda fila de gráficos (nuevos)
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-tamano', figure=fig_tamano)
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafico-ubicacion', figure=fig_ubicacion)
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    # Tercer fila de gráficos (nuevos)
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-baldosa', figure=fig_baldosa)
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafico-velocidad-viento', figure=fig_velocidad_viento)
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    # Cuarta fila de gráficos (tipo de maleza)
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-tipo', figure=fig_tipo)
        ], style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='grafico-especie', figure=fig_especie)
        ], style={'width': '49%', 'display': 'inline-block'})
    ]),

    # quinta fila de gráficos (tipo de maleza)
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-nombre', figure=fig_nombre)
        ], style={'width': '49%', 'display': 'inline-block'})
    ])
])


# Ejecutar
if __name__ == '__main__':
    app.run(debug=True)