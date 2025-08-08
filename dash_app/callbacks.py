# Lógica de callbacks de Dash
from dash import Output, Input, State, no_update
from filters import aplicar_filtros
from visualization import crear_grafico
from datetime import datetime

def register_callbacks(app, df_malezas):
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
         Input('filtro-weed_diameter', 'value')]
    )
    def actualizar_graficos(tile, sens, size, placement, weed_type, weed_name, 
                          crop, wind, speed, start_date, end_date, modulo, weed_diameter):
        # Clean filter values by removing None or empty strings
        def clean_filter(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return [v for v in value if v is not None and v != '']
            return value
        
        wind = clean_filter(wind)
        speed = clean_filter(speed)

        df_filtrado = aplicar_filtros(
            df_malezas, tile, sens, size, placement, weed_type, weed_name, crop,
            wind, speed, start_date, end_date, modulo, weed_diameter
        )
        
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

        return (
            fig_velocidad, fig_sensibilidad, fig_tamano, fig_ubicacion,
            fig_baldosa, fig_velocidad_viento, fig_tipo, fig_nombre, fig_especie, fig_diametro
        )

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