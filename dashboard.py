# Importar librerías necesarias
from dash import Dash, html, dash_table, dcc, callback, Input, Output, State, no_update
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

# Función para obtener datos de malezas
def obtener_datos_malezas():
    conn = sqlite3.connect("ensayos.db")
    query = """
    SELECT 
        r.ensayo_id,
        r.uploader,
        r.weed_diameter,
        r.size,
        r.height,
        r.weed_placement,
        r.weed_type,
        r.weed_name,
        r.weed_applied,
        p.speed,
        m.sens AS sensitivity,
        m.tile,
        c.crop_specie,
        ca.wind_speed,
        e.test_date AS fecha_ensayo,
        cli.name AS cliente,
        cli.modules_id,
        u.farm
    FROM resultados_malezas r
    LEFT JOIN ensayos e ON r.ensayo_id = e.ensayo_id
    LEFT JOIN clientes cli ON e.cliente_id = cli.cliente_id
    LEFT JOIN ubicacion u ON e.ensayo_id = u.ensayo_id
    LEFT JOIN pulverizadora p ON e.ensayo_id = p.ensayo_id
    LEFT JOIN modelo_deteccion m ON e.ensayo_id = m.ensayo_id
    LEFT JOIN condiciones_ambientales ca ON e.ensayo_id = ca.ensayo_id
    LEFT JOIN cultivo c ON e.ensayo_id = c.ensayo_id
    WHERE r.weed_applied IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Función para obtener datos del mapa
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

# Función para obtener datos de aplicación
def obtener_datos_aplico():
    conn = sqlite3.connect("ensayos.db")
    query = """
                SELECT 
                    p.speed,
                    m.sens AS sensitivity,
                    m.tile,
                    r.weed_applied,
                    r.weed_diameter,
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
    df = df.copy()
    df.loc[:, 'sensitivity'] = pd.to_numeric(df['sensitivity'], errors='coerce')
    df = df.loc[df['sensitivity'].isin([1, 2, 3]) | df['sensitivity'].isna()]

    if 'tile' in df.columns:
        df.loc[:, 'tile'] = pd.to_numeric(df['tile'], errors='coerce')
        df = df.loc[df['tile'].isin([1, 2, 3]) | df['tile'].isna()]
    return df

# Función auxiliar para aplicar filtros
def aplicar_filtros(df, tile=None, sens=None, size=None, placement=None,
                   weed_type=None, weed_name=None, crop=None, wind=None, speed=None, fecha_inicio=None, fecha_fin=None, modulo=None, weed_diameter=None):
    df_filtrado = df.copy()
    
    def parse_range(rango):
        """Helper function to parse range strings safely"""
        if not rango:
            return None
        
        parts = rango.split('-')
        if len(parts) == 2:
            try:
                min_val = float(parts[0])
                max_val = float(parts[1])
                return (min_val, max_val)
            except (ValueError, TypeError):
                return None
        elif rango.startswith('>'):
            try:
                min_val = float(rango[1:])
                return (min_val, float('inf'))
            except (ValueError, TypeError):
                return None
        return None
    
    if tile:
        df_filtrado = df_filtrado.loc[df_filtrado['tile'].isin(tile)]
    if sens:
        df_filtrado = df_filtrado.loc[df_filtrado['sensitivity'].isin(sens)]
    if size:
        bins = []
        for rango in size:
            parsed = parse_range(rango)
            if parsed:
                bins.append(parsed)
        
        if bins:
            df_filtrado = df_filtrado.loc[df_filtrado['size'].apply(
                lambda x: any(min_val <= x < max_val for min_val, max_val in bins) if pd.notna(x) else False)]
    if placement:
        df_filtrado = df_filtrado.loc[df_filtrado['weed_placement'].isin(placement)]
    if weed_type:
        df_filtrado = df_filtrado.loc[df_filtrado['weed_type'].isin(weed_type)]
    if weed_name:
        df_filtrado = df_filtrado.loc[df_filtrado['weed_name'].isin(weed_name)]
    if crop:
        df_filtrado = df_filtrado.loc[df_filtrado['crop_specie'].isin(crop)]
    if wind:
        wind_bins = []
        for rango in wind:
            parsed = parse_range(rango)
            if parsed:
                wind_bins.append(parsed)
        
        if wind_bins:
            df_filtrado = df_filtrado.loc[df_filtrado['wind_speed'].apply(
                lambda x: any(min_val <= x < max_val for min_val, max_val in wind_bins) if pd.notna(x) else False)]
    if speed:
        speed_bins = []
        for rango in speed:
            parsed = parse_range(rango)
            if parsed:
                speed_bins.append(parsed)
        
        if speed_bins:
            df_filtrado = df_filtrado.loc[df_filtrado['speed'].apply(
                lambda x: any(min_val <= x < max_val for min_val, max_val in speed_bins) if pd.notna(x) else False)]
            
    if weed_diameter:
        diameter_bins = []
        for rango in weed_diameter:
            if rango == '0-15':
                diameter_bins.append((0, 15))
            elif rango == '15-30':
                diameter_bins.append((15, 30))
            elif rango == '>=30':
                diameter_bins.append((30, 1000))

        df_filtrado['weed_diameter'] = pd.to_numeric(df_filtrado['weed_diameter'], errors='coerce')
        df_filtrado = df_filtrado[df_filtrado['weed_diameter'].notna()]

        if diameter_bins:
            df_filtrado = df_filtrado[df_filtrado['weed_diameter'].apply(
                lambda x: any(min_val <= x < max_val for min_val, max_val in diameter_bins)
            )]

    # Nuevos filtros
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado.loc[
            (df_filtrado['fecha_ensayo'] >= fecha_inicio) & 
            (df_filtrado['fecha_ensayo'] <= fecha_fin)
        ]
    if modulo:
        df_filtrado = df_filtrado.loc[df_filtrado['modules_id'].isin(modulo)]


    print(f'Filtrado por diámetro: {weed_diameter}')
    print(f'Tamaño df_filtrado: {len(df_filtrado)}')
    print(df_filtrado['weed_diameter'].unique())

    
    return df_filtrado

# Obtener datos
df_mapa = obtener_datos_mapa()
df_aplico = obtener_datos_aplico()
df_malezas = obtener_datos_malezas()

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
        df = df.copy()
        df.loc[:, 'rango'] = pd.cut(df['speed'], bins=[0, 5, 10, 15, 20, 25], 
                                labels=["0-5", "5-10", "10-15", "15-20", "20-25"], right=False)
        titulo = f"Por velocidad de avance (km/h)"
        etiqueta_x = "Rango de velocidad de"
    elif tipo_grafico == 'sensitivity':
        df = df.dropna(subset=['sensitivity']).copy()
        df.loc[:, 'rango'] = df['sensitivity'].astype(int).astype(str)
        titulo = f"Por sensibilidad (1-3)"
        etiqueta_x = "Nivel de sensibilidad"
    elif tipo_grafico == 'size':
        df = df.copy()
        df.loc[:, 'size'] = pd.to_numeric(df['size'], errors='coerce')
        df = df.dropna(subset=['size']).copy()

        bins = [0, 5, 10, 15, 20, 25, float('inf')]
        labels = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        df.loc[:, 'rango'] = pd.cut(df['size'], bins=bins, labels=labels, right=False)

        titulo = f"Por tamaño de maleza (cm)"
        etiqueta_x = "Tamaño"

        orden_size = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        df.loc[:, 'rango'] = pd.Categorical(df['rango'], categories=orden_size, ordered=True)
    elif tipo_grafico == 'weed_placement':
        df = df.dropna(subset=['weed_placement']).copy() 
        df.loc[:, 'rango'] = df['weed_placement'].astype(str) 
        titulo = f"Por ubicación de maleza"
        etiqueta_x = "Ubicación"
    elif tipo_grafico == 'tile':
        df = df.dropna(subset=['tile']).copy()
        df.loc[:, 'rango'] = df['tile'].astype(int).astype(str)
        titulo = f"Por baldosa (1-3)"
        etiqueta_x = "Nivel de baldosa"
    elif tipo_grafico == 'wind_speed':
        df = df.copy()
        df.loc[:, 'rango'] = pd.cut(df['wind_speed'], bins=[0, 5, 10, 15, 20, 25], 
                                  labels=["0-5", "5-10", "10-15", "15-20", "20-25"], right=False) 
        titulo = f"Por velocidad del viento (km/h)"
        etiqueta_x = "Rango de velocidad"
    elif tipo_grafico == 'weed_type':
        df = df.dropna(subset=['weed_type']).copy()  
        df.loc[:, 'rango'] = df['weed_type'].astype(str)
        titulo = f"Por tipo de maleza"
        etiqueta_x = "Tipo"
    elif tipo_grafico == 'weed_name':
        df = df.dropna(subset=['weed_name']).copy()
        df.loc[:, 'rango'] = df['weed_name'].astype(str)
        titulo = f"Por nombre de maleza"
        etiqueta_x = "Nombre de maleza"
    elif tipo_grafico == 'crop_specie':
        df = df.dropna(subset=['crop_specie']).copy()
        df.loc[:, 'rango'] = df['crop_specie'].astype(str)
        titulo = f"Por especie de cultivo"
        etiqueta_x = "Especie de cultivo"
    elif tipo_grafico == 'weed_diameter':
        df = df.copy()
        df.loc[:, 'rango'] = pd.cut(df['weed_diameter'], 
                                bins=[0, 15, 30, float('inf')], 
                                labels=["0-15", "15-30", ">=30"], 
                                right=False)
        titulo = f"Por diámetro de maleza (cm)"
        etiqueta_x = "Rango de diámetro"
        # Asegurar el orden correcto
        orden_diameter = ["0-15", "15-30", ">=30"]
        df.loc[:, 'rango'] = pd.Categorical(df['rango'], categories=orden_diameter, ordered=True)

    df = df.dropna(subset=['rango', variable_analisis]).copy()

    if variable_analisis == 'weed_applied':
        metricas = df.groupby('rango', observed=False)[variable_analisis].mean() * 100
    else:
        metricas = df.groupby('rango', observed=False)[variable_analisis].mean()
    
    counts = df.groupby('rango', observed=False).size()
    
    if tipo_grafico == 'sensitivity':
        niveles_completos = ['1', '2', '3']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    elif tipo_grafico == 'weed_type':
        niveles_completos = ['HA', 'G']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    elif tipo_grafico == 'tile':
        niveles_completos = ['1', '2', '3']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    elif tipo_grafico == 'weed_placement':
        niveles_completos = ['ROW', 'FURROW']
        metricas = metricas.reindex(niveles_completos, fill_value=0)
        counts = counts.reindex(niveles_completos, fill_value=0)
    
    plot_data = pd.DataFrame({
        'rango': metricas.index.astype(str).str.strip(),
        'valor': metricas.values,
        'count': counts.values
    })

    if tipo_grafico == 'size':
        orden_size = ["0-5", "5-10", "10-15", "15-20", "20-25", ">25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_size, ordered=True)
        plot_data = plot_data.sort_values('rango')
    elif tipo_grafico == 'speed':
        orden_speed = ["0-5", "5-10", "10-15", "15-20", "20-25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_speed, ordered=True)
        plot_data = plot_data.sort_values('rango')
    elif tipo_grafico == 'wind_speed':
        orden_wind = ["0-5", "5-10", "10-15", "15-20", "20-25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_wind, ordered=True)
        plot_data = plot_data.sort_values('rango')
    elif tipo_grafico == 'weed_diameter':
        orden_diameter = ["0-15", "15-30", ">=30"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_diameter, ordered=True)
        plot_data = plot_data.sort_values('rango')
    
    fig = go.Figure()


    if variable_analisis == 'weed_applied':
        colors = []
        for val in plot_data['valor']:
            if val >= 90:
                colors.append('#4CAF50')  # Verde suave
            elif 80 <= val < 90:
                colors.append('#FFC107')  # Ámbar suave
            else:
                colors.append('#F44336')  # Rojo suave
    else:
        colors = '#2196F3'  # Azul para otras métricas
    
    fig.add_trace(go.Bar(
        x=plot_data['rango'],
        y=plot_data['valor'],
        marker_color=colors,
        text=[f"{v:.1f}%" if variable_analisis == 'weed_applied' else f"{v:.1f}" for v in plot_data['valor']],
        textposition='auto',
        textfont=dict(size=12, color='white'),
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

    for i, row in enumerate(plot_data.itertuples()):
        fig.add_annotation(
            x=i,
            y=-2,
            text=f"{int(row.count)} malezas",
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

    if tipo_grafico == 'sensitivity':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['1', '2', '3']
        )
    elif tipo_grafico == 'tile':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['1', '2', '3']
        )
    elif tipo_grafico == 'weed_placement':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['ROW', 'FURROW']
        )
    elif tipo_grafico == 'weed_type':
        fig.update_xaxes(
            type='category',
            categoryorder='array',
            categoryarray=['HA', 'G']
        )

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
    if columna == 'sensitivity':
        return [{'label': '1', 'value': 1}, 
                {'label': '2', 'value': 2},
                {'label': '3', 'value': 3}]
    elif columna == 'tile':
        return [{'label': '1', 'value': 1}, 
                {'label': '2', 'value': 2},
                {'label': '3', 'value': 3}]
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
    elif columna == 'weed_diameter':
        return [{'label': '0-15 cm', 'value': '0-15'}, 
                {'label': '15-30 cm', 'value': '15-30'},
                {'label': '>=30 cm', 'value': '>=30'},]
    elif columna == 'speed':
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
    
    # Fila 1
    html.Div([
        html.Div([
            html.Label("Baldosa"),
            dcc.Dropdown(
                id='filtro-tile',
                options=crear_opciones_filtro('tile'),
                multi=True,
                placeholder="Seleccione baldosa(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Sensibilidad"),
            dcc.Dropdown(
                id='filtro-sens',
                options=crear_opciones_filtro('sensitivity'),
                multi=True,
                placeholder="Seleccione sensibilidad(es)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Tamaño maleza"),
            dcc.Dropdown(
                id='filtro-size',
                options=crear_opciones_filtro('size'),
                multi=True,
                placeholder="Seleccione tamaño(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Ubicación maleza"),
            dcc.Dropdown(
                id='filtro-placement',
                options=crear_opciones_filtro('weed_placement'),
                multi=True,
                placeholder="Seleccione ubicación(es)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),
    ]),
    
    # Fila 2
    html.Div([
        html.Div([
            html.Label("Tipo de maleza"),
            dcc.Dropdown(
                id='filtro-type',
                options=crear_opciones_filtro('weed_type'),
                multi=True,
                placeholder="Seleccione tipo(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Nombre maleza"),
            dcc.Dropdown(
                id='filtro-name',
                options=crear_opciones_filtro('weed_name'),
                multi=True,
                placeholder="Seleccione nombre(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Especie cultivo"),
            dcc.Dropdown(
                id='filtro-crop',
                options=crear_opciones_filtro('crop_specie'),
                multi=True,
                placeholder="Seleccione especie(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Velocidad de avance"),
            dcc.Dropdown(
                id='filtro-speed',
                options=crear_opciones_filtro('speed'),
                multi=True,
                placeholder="Seleccione velocidad(es)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),
    ]),

    # Fila 3
    html.Div([
        html.Div([
            html.Label("Velocidad viento"),
            dcc.Dropdown(
                id='filtro-wind',
                options=crear_opciones_filtro('wind_speed'),
                multi=True,
                placeholder="Seleccione velocidad(es)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),
        
        html.Div([
            html.Label("Módulo"),
            dcc.Dropdown(
                id='filtro-modulo',
                options=[{'label': str(m), 'value': m} 
                         for m in sorted(df_malezas['modules_id'].dropna().unique())],
                multi=True,
                placeholder="Seleccione módulo(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Diametro maleza"),
            dcc.Dropdown(
                id='filtro-weed_diameter',
                options=crear_opciones_filtro('weed_diameter'),
                multi=True,
                placeholder="Seleccione diámetro(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),
    ]),
        

    # Fila 4
    html.Div([
        html.Label("Fecha desde: "),
        dcc.DatePickerSingle(
            id='filtro-fecha-desde',
            min_date_allowed=df_malezas['fecha_ensayo'].min(),
            max_date_allowed=df_malezas['fecha_ensayo'].max(),
            date=df_malezas['fecha_ensayo'].min(),                display_format='YYYY-MM-DD'
        )
    ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),
    
    html.Div([
        html.Label("Fecha hasta: "),
        dcc.DatePickerSingle(
            id='filtro-fecha-hasta',
            min_date_allowed=df_malezas['fecha_ensayo'].min(),
            max_date_allowed=df_malezas['fecha_ensayo'].max(),
            date=df_malezas['fecha_ensayo'].max(),
            display_format='YYYY-MM-DD'
        )
    ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'})


], style={'border': '1px solid #ddd', 'padding': '10px', 'margin-bottom': '20px', 'border-radius': '5px'})

# Callback para actualizar gráficos
@app.callback(
    [Output('grafico-velocidad', 'figure'),
     Output('grafico-sensibilidad', 'figure'),
     Output('grafico-tamano', 'figure'),
     Output('grafico-ubicacion', 'figure'),
     Output('grafico-baldosa', 'figure'),
     Output('grafico-velocidad-viento', 'figure'),
     Output('grafico-tipo', 'figure'),
     Output('grafico-nombre', 'figure'),
     Output('grafico-especie', 'figure'),
     Output('grafico-diameter', 'figure')],
    [Input('filtro-tile', 'value'),
     Input('filtro-sens', 'value'),
     Input('filtro-size', 'value'),
     Input('filtro-placement', 'value'),
     Input('filtro-type', 'value'),
     Input('filtro-name', 'value'),
     Input('filtro-crop', 'value'),
     Input('filtro-wind', 'value'),
     Input('filtro-speed', 'value'),
     Input('filtro-fecha-desde', 'date'),
     Input('filtro-fecha-hasta', 'date'),
     Input('filtro-modulo', 'value'),
     Input('filtro-weed_diameter', 'value')],
)
def actualizar_graficos(tile, sens, size, placement, weed_type, weed_name, crop, wind, speed, start_date, end_date, modulo, weed_diameter):
    print("Valor recibido de filtro weed_diameter:", weed_diameter)


    # Clean filter values by removing None or empty strings
    def clean_filter(value):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [v for v in value if v is not None and v != '']
        return value
    
    wind = clean_filter(wind)
    speed = clean_filter(speed)

    df_filtrado = aplicar_filtros(df_malezas, tile, sens, size, placement, weed_type, weed_name, crop, wind, speed, start_date, end_date, modulo, weed_diameter)
    
    fig_velocidad = crear_grafico('speed', df_filtrado.copy())
    fig_sensibilidad = crear_grafico('sensitivity', df_filtrado.copy())
    fig_tamano = crear_grafico('size', df_filtrado.copy())
    fig_ubicacion = crear_grafico('weed_placement', df_filtrado.copy())
    fig_baldosa = crear_grafico('tile', df_filtrado.copy())
    fig_velocidad_viento = crear_grafico('wind_speed', df_filtrado.copy())
    fig_tipo = crear_grafico('weed_type', df_filtrado.copy())
    fig_nombre = crear_grafico('weed_name', df_filtrado.copy())
    fig_especie = crear_grafico('crop_specie', df_filtrado.copy())
    fig_diametro = crear_grafico('weed_diameter', df_filtrado.copy())

    
    return (fig_velocidad, fig_sensibilidad, fig_tamano, fig_ubicacion, 
            fig_baldosa, fig_velocidad_viento, fig_tipo, fig_nombre, fig_especie, fig_diametro)

# Callback para descargar malezas filtradas
@app.callback(
    Output("download-malezas-filtradas", "data"),
    Input("btn-descargar-malezas", "n_clicks"),
    [State('filtro-tile', 'value'),
     State('filtro-sens', 'value'),
     State('filtro-size', 'value'),
     State('filtro-placement', 'value'),
     State('filtro-type', 'value'),
     State('filtro-name', 'value'),
     State('filtro-crop', 'value'),
     State('filtro-wind', 'value'),
     State('filtro-speed', 'value'),
     State('filtro-fecha-desde', 'date'),
     State('filtro-fecha-hasta', 'date'),
     State('filtro-modulo', 'value'),
     State('filtro-weed_diameter', 'value')],
    prevent_initial_call=True
)
def descargar_malezas_filtradas(n_clicks, tile, sens, size, placement, weed_type, weed_name, crop, wind, speed, start_date, end_date, modulo, weed_diameter):
    if n_clicks is None:
        return no_update
    
    df_filtrado = aplicar_filtros(df_malezas, tile, sens, size, placement, weed_type, weed_name, crop, wind, speed, start_date, end_date, modulo, weed_diameter)
    
    columnas_malezas = [
        'ensayo_id', 'weed_diameter', 'size', 'height', 'weed_placement',
        'weed_type', 'weed_name', 'weed_applied', 'cliente', 'farm',
        'speed', 'sensitivity', 'tile', 'crop_specie', 'wind_speed', 'fecha_ensayo'
    ]
    df_exportar = df_filtrado[columnas_malezas]
    
    fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"malezas_filtradas_{fecha_hora}.csv"
    csv_string = df_exportar.to_csv(index=False, encoding='utf-8')
    
    return dict(content=csv_string, filename=nombre_archivo)

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
    filtros,
    
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-velocidad')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='grafico-sensibilidad')
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
        ], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(id='grafico-diameter')
        ], style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.Div([
        html.Button("Descargar datos de malezas filtrados", 
                  id="btn-descargar-malezas",
                  style={'margin': '10px', 'padding': '10px',
                         'background-color': '#008148', 'color': 'white',
                         'border': 'none', 'border-radius': '5px',
                         'cursor': 'pointer'}),
        dcc.Download(id="download-malezas-filtradas")
    ], style={'text-align': 'center', 'margin': '20px'})
])

# Ejecutar
if __name__ == '__main__':
    app.run(debug=True, port=8050)