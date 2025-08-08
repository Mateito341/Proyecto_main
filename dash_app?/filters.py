# Lógica para aplicar filtros y generar opciones
import pandas as pd

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
        tamano_bins = []
        for rango in size:
            if rango == '3':
                tamano_bins.append((2, 3.5))
            elif rango == '5':
                tamano_bins.append((3.5, 5.5))
            elif rango == '7':
                tamano_bins.append((5.5, 7.5))
            elif rango == '9':
                tamano_bins.append((7.5, 9.5))
            elif rango == '15':
                tamano_bins.append((9.5, 15.5))
            elif rango == '20':
                tamano_bins.append((15.5, 20.5))
            elif rango == '25':
                tamano_bins.append((20.5, 25.5))
            elif rango == '>25':
                tamano_bins.append((26, 1000))

        df_filtrado['size'] = pd.to_numeric(df_filtrado['size'], errors='coerce')
        df_filtrado = df_filtrado[df_filtrado['size'].notna()]

        if tamano_bins:
            df_filtrado = df_filtrado[df_filtrado['size'].apply(
                lambda x: any(min_val <= x < max_val for min_val, max_val in tamano_bins)
            )]

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

    return df_filtrado

def crear_opciones_filtro(df, columna):

    valores_unicos = df[columna].dropna().unique()

    if columna == 'sensitivity':
        return [{'label': '1', 'value': 1}, 
                {'label': '2', 'value': 2},
                {'label': '3', 'value': 3}]    
    elif columna == 'tile':
        return [{'label': '1', 'value': 1}, 
                {'label': '2', 'value': 2},
                {'label': '3', 'value': 3}]
    elif columna == 'size':
        return [
            {'label': '3 cm', 'value': "3"}, 
            {'label': '5 cm', 'value': "5"},
            {'label': '7 cm', 'value': "7"},
            {'label': '9 cm', 'value': "9"},
            {'label': '15 cm', 'value': "15"},
            {'label': '20 cm', 'value': "20"},
            {'label': '25 cm', 'value': "25"},
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