# Funciones para crear gráficos y figuras
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def crear_mapa(df_mapa):
    fig = px.scatter_map(
        df_mapa,
        lat="latitude",
        lon="longitude",
        hover_name="cliente",
        hover_data=["farm"],
        zoom=4,
        height=500
    )
    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    return fig

def crear_grafico(tipo_grafico, df, variable_analisis='weed_applied'):
    if tipo_grafico == 'speed':
        df = df.copy()
        df.loc[:, 'rango'] = pd.cut(df['speed'], bins=[0, 5, 10, 15, 20, 25], 
                                labels=["0-5", "5-10", "10-15", "15-20", "20-25"], right=False)
        titulo = f"Por velocidad de avance (km/h)"
        etiqueta_x = "Rango de velocidad"

    elif tipo_grafico == 'sensitivity':
        df = df.dropna(subset=['sensitivity']).copy()
        df.loc[:, 'rango'] = df['sensitivity'].astype(int).astype(str)
        titulo = f"Por sensibilidad (1-3)"
        etiqueta_x = "Nivel de sensibilidad"


    elif tipo_grafico == 'size':
        df = df.copy()
        df.loc[:, 'rango'] = pd.cut(df['size'], 
                                bins=[0, 3.5, 5.5, 7.5, 9.5, 15.5, 20.5, 25.5, float('inf')], 
                                labels=["3", "5", "7", "9", "15", "20", "25", ">25"], 
                                right=False)
        titulo = f"Por tamaño de maleza (cm)"
        etiqueta_x = "Rango de tamaño"
        # Asegurar el orden correcto
        orden_tamano = ["3", "5", "7", "9", "15", "20", "25", ">25"]
        df.loc[:, 'rango'] = pd.Categorical(df['rango'], categories=orden_tamano, ordered=True)


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
        etiqueta_x = "Tipo de maleza"

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
        orden_tamano = ["3", "5", "7", "9", "15", "20", "25", ">25"]
        plot_data['rango'] = pd.Categorical(plot_data['rango'], categories=orden_tamano, ordered=True)
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