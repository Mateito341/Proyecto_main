# Carga y estandarización de CSV
import pandas as pd
import streamlit as st
from verificarStem import verificar_columnas, archivos_estandarizados

def process_csv(csv_file):
    if not csv_file:
        return None, {"archivo": ["No se cargó un archivo CSV."]}

    try:
        df_csv = pd.read_csv(csv_file)
        dataframe_procesado, errores = verificar_columnas(df_csv)
        return dataframe_procesado, errores
    except Exception as e:
        return None, {"lectura": [str(e)]}

def confirm_csv(dataframe):
    if dataframe is not None:
        return archivos_estandarizados(dataframe)
    return None
