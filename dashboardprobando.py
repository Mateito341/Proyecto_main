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
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df = df.dropna(subset=['size'])

        # Agregar bin extra para >25
        bins = [0, 5, 10, 15, 20, 25, float('inf')]
        labels = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]

        df['rango'] = pd.cut(df['size'], bins=bins, labels=labels, right=False)

        titulo = f"Por tamaño de maleza (cm)"
        etiqueta_x = "Tamaño"

        # Asegurar orden correcto en el gráfico
        orden_size = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        df['rango'] = pd.Categorical(df['rango'], categories=orden_size, ordered=True)
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
        'rango': metricas.index.astype(str).str.strip(),
        'valor': metricas.values,
        'count': counts.values
    })

    # Ordenar rangos
    if tipo_grafico == 'size':
        orden_size = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_size, ordered=True)
        plot_data = plot_data.sort_values('rango')

    if tipo_grafico == 'speed':
        orden_speed = ["0-5", "5-10", "10-15", "15-20", "20-25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_speed, ordered=True)
        plot_data = plot_data.sort_values('rango')

    if tipo_grafico == 'wind_speed':
        orden_wind = ["0-5", "5-10", "10-15", "15-20", "20-25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_wind, ordered=True)
        plot_data = plot_data.sort_values('rango')
    
    # Ordenar si corresponde
    if tipo_grafico in ['speed', 'wind_speed', 'size']:
        plot_data = plot_data.sort_values('rango')

    fig = go.Figure()

    # Colores condicionales
    colors = ['#008148' if val >= 90 else '#FF0000' for val in plot_data['valor']] if variable_analisis == 'weed_applied' else '#008148'
    
    fig.add_trace(go.Bar(
        x=plot_data['rango'],
        y=plot_data['valor'],
        marker_color=colors,
        text=[f"{v:.1f}%" if variable_analisis == 'weed_applied' else f"{v:.1f}" for v in plot_data['valor']],
        textposition='auto',
        width=0.5,
        hoverinfo='x+y',
        showlegend=False
    ))

    datos_con_valores = plot_data[plot_data['valor'] > 0]
    if len(datos_con_valores) > 1:
        fig.add_trace(go.Scatter(
            x=datos_con_valores['rango'],
            y=datos_con_valores['valor'],
            mode='lines+markers',
            line=dict(color='#EF8A17', width=3),
            marker=dict(size=8),
            showlegend=False
        ))

    # Anotaciones con índice numérico para evitar desplazamiento
    for i, row in enumerate(plot_data.itertuples()):
        fig.add_annotation(
            x=i,
            y=-2,
            text=f"{int(row.count)} ensayos",
            showarrow=False,
            font=dict(size=10, color="black"),
            xanchor='center',
            yanchor='top'
        )

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

    # Definir eje X categórico y orden específico
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

    # Tooltip con datos
    fig.data[0].hovertemplate = (
        f"<b>%{{x}}</b><br>"
        f"{'Porcentaje aplicado' if variable_analisis == 'weed_applied' else variable_analisis.replace('_', ' ').title()}: %{{y:.1f}}"
        f"{'%' if variable_analisis == 'weed_applied' else ''}<br>"
        "Cantidad de malezas: %{customdata[0]}<extra></extra>"
    )
    fig.data[0].customdata = plot_data[['count']].values
        
    fig.update_layout(
        title=titulo,
        xaxis_title=etiqueta_x,
        yaxis_title="Porcentaje aplicado (%)" if variable_analisis == 'weed_applied' else variable_analisis.replace('_', ' ').title(),
        yaxis=dict(range=[-10, 105] if variable_analisis == 'weed_applied' else None),
        margin=dict(b=140, t=50),
        height=400,
        showlegend=False
    )

    return fig

# Crear opciones para los filtros
def crear_opciones_filtro(columna):
    valores_unicos = df_aplico[columna].dropna().unique()
    if columna in ['sensitivity', 'tile']:
        valores_unicos = sorted([int(x) for x in valores_unicos if str(x).isdigit()])
        return [{'label': str(v), 'value': v} for v in valores_unicos]
    elif columna == 'size':
        return [{'label': '0-5 cm', 'value': '0-5'}, 
                {'label': '5-10 cm', 'value': '5-10'},
                {'label': '10-15 cm', 'value': '10-15'},
                {'label': '15-20 cm', 'value': '15-20'},
                {'label': '20-25 cm', 'value': '20-25'},
                {'label': '>25 cm', 'value': '>25'}]
    elif columna == 'wind_speed':
        return [{'label': '0-5 km/h', 'value': '0-5'}, 
                {'label': '5-10 km/h', 'value': '5-10'},
                {'label': '10-15 km/h', 'value': '10-15'},
                {'label': '15-20 km/h', 'value': '15-20'},
                {'label': '20-25 km/h', 'value': '20-25'}]
    else:
        return [{'label': str(v), 'value': v} for v in sorted(valores_unicos)]

# Layout de los filtros
filtros = html.Div([
    html.H3("Filtros"),
    html.Div([
        html.Div([
            html.Label("Baldosa (Tile)"),
            dcc.Dropdown(
                id='filtro-tile',
                options=crear_opciones_filtro('tile'),
                multi=True,
                placeholder="Seleccione baldosa(s)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Sensibilidad"),
            dcc.Dropdown(
                id='filtro-sens',
                options=crear_opciones_filtro('sensitivity'),
                multi=True,
                placeholder="Seleccione sensibilidad(es)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Tamaño maleza"),
            dcc.Dropdown(
                id='filtro-size',
                options=crear_opciones_filtro('size'),
                multi=True,
                placeholder="Seleccione tamaño(s)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Ubicación maleza"),
            dcc.Dropdown(
                id='filtro-placement',
                options=crear_opciones_filtro('weed_placement'),
                multi=True,
                placeholder="Seleccione ubicación(es)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'})
    ]),
    
    html.Div([
        html.Div([
            html.Label("Tipo de maleza"),
            dcc.Dropdown(
                id='filtro-type',
                options=crear_opciones_filtro('weed_type'),
                multi=True,
                placeholder="Seleccione tipo(s)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Nombre maleza"),
            dcc.Dropdown(
                id='filtro-name',
                options=crear_opciones_filtro('weed_name'),
                multi=True,
                placeholder="Seleccione nombre(s)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Especie cultivo"),
            dcc.Dropdown(
                id='filtro-crop',
                options=crear_opciones_filtro('crop_specie'),
                multi=True,
                placeholder="Seleccione especie(s)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Velocidad viento"),
            dcc.Dropdown(
                id='filtro-wind',
                options=crear_opciones_filtro('wind_speed'),
                multi=True,
                placeholder="Seleccione velocidad(es)"
            )
        ], style={'width': '24%', 'display': 'inline-block', 'margin': '5px'})
    ])
], style={'border': '1px solid #ddd', 'padding': '10px', 'margin-bottom': '20px', 'border-radius': '5px'})

# Callback para aplicar filtros
@app.callback(
    [Output('grafico-velocidad', 'figure'),
     Output('grafico-sensibilidad', 'figure'),
     Output('grafico-tamano', 'figure'),
     Output('grafico-ubicacion', 'figure'),
     Output('grafico-baldosa', 'figure'),
     Output('grafico-velocidad-viento', 'figure'),
     Output('grafico-tipo', 'figure'),
     Output('grafico-nombre', 'figure'),
     Output('grafico-especie', 'figure')],
    [Input('filtro-tile', 'value'),
     Input('filtro-sens', 'value'),
     Input('filtro-size', 'value'),
     Input('filtro-placement', 'value'),
     Input('filtro-type', 'value'),
     Input('filtro-name', 'value'),
     Input('filtro-crop', 'value'),
     Input('filtro-wind', 'value')]
)
def actualizar_graficos(tile, sens, size, placement, weed_type, weed_name, crop, wind):
    df_filtrado = df_aplico.copy()
    
    # Aplicar filtros
    if tile:
        df_filtrado = df_filtrado[df_filtrado['tile'].isin(tile)]
    if sens:
        df_filtrado = df_filtrado[df_filtrado['sensitivity'].isin(sens)]
    if size:
        # Convertir rangos de tamaño a valores numéricos para filtrar
        bins = []
        for rango in size:
            if rango == '>25':
                bins.append((25, float('inf')))
            else:
                min_val, max_val = map(float, rango.split('-'))
                bins.append((min_val, max_val))
        
        def in_selected_ranges(x):
            if pd.isna(x):
                return False
            for min_val, max_val in bins:
                if min_val <= x < max_val:
                    return True
            return False
        
        df_filtrado = df_filtrado[df_filtrado['size'].apply(in_selected_ranges)]
    if placement:
        df_filtrado = df_filtrado[df_filtrado['weed_placement'].isin(placement)]
    if weed_type:
        df_filtrado = df_filtrado[df_filtrado['weed_type'].isin(weed_type)]
    if weed_name:
        df_filtrado = df_filtrado[df_filtrado['weed_name'].isin(weed_name)]
    if crop:
        df_filtrado = df_filtrado[df_filtrado['crop_specie'].isin(crop)]
    if wind:
        # Convertir rangos de velocidad del viento a valores numéricos para filtrar
        bins = []
        for rango in wind:
            min_val, max_val = map(float, rango.split('-'))
            bins.append((min_val, max_val))
        
        def in_selected_ranges_wind(x):
            if pd.isna(x):
                return False
            for min_val, max_val in bins:
                if min_val <= x < max_val:
                    return True
            return False
        
        df_filtrado = df_filtrado[df_filtrado['wind_speed'].apply(in_selected_ranges_wind)]
    
    # Crear gráficos con datos filtrados
    fig_velocidad = crear_grafico('speed', df_filtrado.copy())
    fig_sensibilidad = crear_grafico('sensitivity', df_filtrado.copy())
    fig_tamano = crear_grafico('size', df_filtrado.copy())
    fig_ubicacion = crear_grafico('weed_placement', df_filtrado.copy())
    fig_baldosa = crear_grafico('tile', df_filtrado.copy())
    fig_velocidad_viento = crear_grafico('wind_speed', df_filtrado.copy())
    fig_tipo = crear_grafico('weed_type', df_filtrado.copy())
    fig_nombre = crear_grafico('weed_name', df_filtrado.copy())
    fig_especie = crear_grafico('crop_specie', df_filtrado.copy())
    
    return fig_velocidad, fig_sensibilidad, fig_tamano, fig_ubicacion, fig_baldosa, fig_velocidad_viento, fig_tipo, fig_nombre, fig_especie

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

    # Gráficos de aplicación con filtros
    html.H1("Análisis de Aplicación"),
    html.Hr(),
    filtros,  # Sección de filtros agregada aquí
    
    html.Div([
        html.Div([
            dcc.Graph(
                id='grafico-velocidad'
            )
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(
                id='grafico-sensibilidad'
            )
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='grafico-tamano')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafico-ubicacion')
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='grafico-baldosa')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafico-velocidad-viento')
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='grafico-tipo')
        ], style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='grafico-especie')
        ], style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='grafico-nombre')
        ], style={'width': '49%', 'display': 'inline-block'})
    ])
])

# Ejecutar
if __name__ == '__main__':
    app.run(debug=True)