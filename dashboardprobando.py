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
            {'label': 'Velocidad de avance', 'value': 'speed'},
            {'label': 'Nivel de sensibilidad', 'value': 'sensitivity'}
        ],
        value='speed',
        id='tipo-grafico-radio',
        inline=True,
        style={'marginBottom': '10px'}
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
        df = df.dropna(subset=['sensitivity'])
        df['rango'] = df['sensitivity'].astype(int).astype(str)
        titulo = "Porcentaje de malezas aplicadas según sensibilidad"
        etiqueta_x = "Nivel de sensibilidad"
    
    # elimina filas con valores nulos en 'rango' y 'weed_applied'
    df = df.dropna(subset=['rango', 'weed_applied'])

    # Calcular porcentaje promedio aplicado y conteo
    porcentajes = df.groupby('rango')['weed_applied'].mean() * 100
    counts = df.groupby('rango').size()
    
    # Para sensibilidad, asegurar que todas las categorías estén presentes
    if tipo_grafico == 'sensitivity':
        # Crear un índice completo con todos los niveles de sensibilidad
        niveles_completos = ['1', '2', '3']
        porcentajes = porcentajes.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    
    plot_data = pd.DataFrame({
        'rango': porcentajes.index,
        'porcentaje': porcentajes.values,
        'count': counts.values
    })
    
    # Para velocidad, ordenar por rango
    if tipo_grafico == 'speed':
        plot_data = plot_data.sort_values('rango')

    # Crear figura vacía
    fig = go.Figure()

    # Agregar barras
    fig.add_trace(go.Bar(
        x=plot_data['rango'],
        y=plot_data['porcentaje'],
        name='Porcentaje aplicado',
        marker_color='#008148',
        text=[f"{p:.1f}%" if p > 0 else "" for p in plot_data['porcentaje']],
        textposition='auto',
        width=0.5,
        hoverinfo='x+y',
    ))

    # Agregar línea solo si hay más de un punto con datos
    datos_con_valores = plot_data[plot_data['porcentaje'] > 0]
    if len(datos_con_valores) > 1:
        fig.add_trace(go.Scatter(
            x=datos_con_valores['rango'],
            y=datos_con_valores['porcentaje'],
            mode='lines+markers',
            name='Tendencia',
            line=dict(color='#EF8A17', width=3),
            marker=dict(size=8)
        ))

    # Línea horizontal en 90%
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

    # Configuración específica del eje X para sensibilidad
    if tipo_grafico == 'sensitivity':
        fig.update_xaxes(
            type='category',  # Forzar tratamiento como categorías
            categoryorder='array',
            categoryarray=['1', '2', '3']  # Orden específico
        )

    # Personalizar tooltip para incluir la cantidad de ensayos
    fig.data[0].hovertemplate = (
        f"<b>%{{x}}</b><br>"
        "Porcentaje aplicado: %{y:.1f}%<br>"
        "Cantidad de ensayos: %{customdata[0]}<extra></extra>"
    )

    # Agregar datos personalizados (cantidad de ensayos)
    fig.data[0].customdata = plot_data[['count']].values
        


    fig.update_layout(
        title=titulo,
        xaxis_title=etiqueta_x,
        yaxis_title='Porcentaje aplicado (%)',
        yaxis=dict(range=[-10, 105]),
        margin=dict(b=100)
    )

    return fig

# Ejecutar
if __name__ == '__main__':
    app.run(debug=True)