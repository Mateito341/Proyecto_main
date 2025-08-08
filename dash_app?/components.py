# Layouts y componentes de la interfaz (filtros, tablas, etc.)
from dash import html, dcc
from filters import crear_opciones_filtro

def filtros_layout(df_aplico, df_malezas):
    return html.Div([
    html.H3("Filtros"),
    
    # Fila 1
    html.Div([
        html.Div([
            html.Label("Baldosa"),
            dcc.Dropdown(
                id='filtro-tile',
                options=crear_opciones_filtro(df_malezas, 'tile'),
                multi=True,
                placeholder="Seleccione baldosa(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Sensibilidad"),
            dcc.Dropdown(
                id='filtro-sens',
                options=crear_opciones_filtro(df_malezas, 'sensitivity'),
                multi=True,
                placeholder="Seleccione sensibilidad(es)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Tamaño maleza"),
            dcc.Dropdown(
                id='filtro-size',
                options=crear_opciones_filtro(df_malezas, 'size'),
                multi=True,
                placeholder="Seleccione tamaño(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Ubicación maleza"),
            dcc.Dropdown(
                id='filtro-placement',
                options=crear_opciones_filtro(df_malezas,'weed_placement'),
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
                options=crear_opciones_filtro(df_malezas, 'weed_type'),
                multi=True,
                placeholder="Seleccione tipo(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Nombre maleza"),
            dcc.Dropdown(
                id='filtro-name',
                options=crear_opciones_filtro(df_malezas, 'weed_name'),
                multi=True,
                placeholder="Seleccione nombre(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Especie cultivo"),
            dcc.Dropdown(
                id='filtro-crop',
                options=crear_opciones_filtro(df_malezas, 'crop_specie'),
                multi=True,
                placeholder="Seleccione especie(s)"
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin': '5px'}),

        html.Div([
            html.Label("Velocidad de avance"),
            dcc.Dropdown(
                id='filtro-speed',
                options=crear_opciones_filtro(df_malezas, 'speed'),
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
                options=crear_opciones_filtro(df_malezas, 'wind_speed'),
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
                options=crear_opciones_filtro(df_malezas, 'weed_diameter'),
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