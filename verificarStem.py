import pandas as pd
import streamlit as st
import glob
import os
from datetime import datetime
import sqlite3

# Columnas que queremos verificar
COLUMNAS_A_BUSCAR = [
    "weed diameter",  # diametro (float)
    "size",           # tamaño cm2 (float)
    "height",         # altura (float)
    "weed placement", # lugar (string)
    "weed type",      # tipo (string)
    "weed name",      # nombre (string)
    "weed applied"    # aplicado (bool)
]

def verificar_columnas(df):
    """
    Verifica que contenga las columnas esenciales, y si alguna tiene un nombre distinto,
    intenta detectarla y renombrarla. En caso de que no se encuentre, avisa al usuario.
    
    Args:
        df: archivo a verificar
    """
    columnas_originales = df.columns
    columnas_normalizadas = [c.strip().lower() for c in columnas_originales]
    mapeo_columnas = dict(zip(columnas_normalizadas, columnas_originales))

    errores_tipo_dato = {}

    for col in COLUMNAS_A_BUSCAR:
        col_lower = col.lower()
        if col_lower in columnas_normalizadas:
            col_original = mapeo_columnas[col_lower]
            if col_original != col:
                df.rename(columns={col_original: col}, inplace=True)
            cantidad_nulls = df[col].isnull().sum()
            st.info(f"✅ '{col}' está presente. Valores nulos: {cantidad_nulls}")
            errores = verificar_tipo_dato(df, col, col)
            if errores:
                errores_tipo_dato[col] = errores
        else:
            resultado = busqueda_profunda(col, columnas_normalizadas, df)
            if resultado:
                col_encontrada, nulos = resultado
                st.info(f"✅🔄 '{col}' fue encontrado como '{col_encontrada}' y renombrado. Valores nulos: {nulos}")
                errores = verificar_tipo_dato(df, col, col)
                if errores:
                    errores_tipo_dato[col] = errores
            else:
                st.warning(f"❌ '{col}' NO está presente.")

    return df, errores_tipo_dato


def verificar_tipo_dato(df, col_original, col_normalizado):
    """
    Verifica que los valores de una columna sean del tipo esperado.
    - Flotantes: permiten solo números (excepto 'size' que también permite '>25')
    - 'weed applied': solo 0/1/true/false
    - 'weed placement': solo valores aceptados en el diccionario 'traducciones'
    """
    columnas_flotantes = ['weed diameter', 'size', 'height']
    errores = []

    # Diccionario de valores válidos para weed placement (normalizados en minúscula)
    traducciones = {
        'surco': 'ROW',
        'entre surco': 'FURROW',
        'entre surcos': 'FURROW',
        'fila': 'ROW',
        'entre filas': 'FURROW',
        'línea': 'ROW',
        'entre líneas': 'FURROW',
        'row': 'ROW',
        'furrow': 'FURROW',
        'between rows': 'FURROW',
        'interrow': 'FURROW',
    }
    valores_validos_placement = set(traducciones.keys())

    if col_normalizado in columnas_flotantes:
        for idx, valor in df[col_original].items():
            if pd.notna(valor):
                valor_str = str(valor).strip().lower()

                if col_normalizado == 'size' and valor_str == '>25':
                    continue  # Aceptar expresamente '>25'
                else:
                    try:
                        float(valor_str)
                    except (ValueError, TypeError):
                        errores.append(f"'{col_original}' (fila {idx}): '{valor}' no es un número válido.")

    elif col_normalizado == 'weed applied':
        valores_unicos = df[col_original].dropna().unique()
        for valor in valores_unicos:
            if valor not in [0, 1, '0', '1', 'true', 'false', 'True', 'False']:
                errores.append(f"'{col_original}': valor inválido '{valor}' (solo 0, 1, true, false).")

    elif col_normalizado == 'weed placement':
        for idx, valor in df[col_original].items():
            if pd.notna(valor):
                valor_normalizado = str(valor).strip().lower()
                if valor_normalizado not in valores_validos_placement:
                    errores.append(f"'{col_original}' (fila {idx}): valor inválido '{valor}'.")

    return errores



def busqueda_profunda(col, columnas_normalizadas, df):
    """
    Busca columnas equivalentes (en otro idioma o sinónimos) y si las encuentra,
    renombra la columna del DataFrame para que se llame como `col`.

    Args:
        col: nombre estándar buscado (normalizado)
        columnas_normalizadas: lista de columnas normalizadas (minúsculas, sin espacios)
        df: DataFrame actual

    Returns:
        tuple: (nuevo_nombre (col), cantidad_nulls) si se renombró, None si no se encontró
    """
    equivalencias = {
        'weed diameter': ['diametro', 'diameter', 'diametro maleza'],
        'size': ['tamaño', 'area', 'superficie'],
        'height': ['altura', 'alto'],
        'weed placement': ['lugar', 'ubicacion', 'posicion', 'localizacion'],
        'weed type': ['tipo', 'tipo maleza', 'clase', 'categoria'],
        'weed name': ['nombre', 'identificacion', 'nombre maleza'],
        'weed applied': ['aplicado', 'se aplicó', 'fue aplicado']
    }

    if col.lower() not in [k.lower() for k in equivalencias.keys()]:
        return None

    for posible in equivalencias[col]:
        posible_lower = posible.lower()
        if posible_lower in columnas_normalizadas:
            col_original = next((c for c in df.columns if c.strip().lower() == posible_lower), None)
            if col_original:
                cantidad_nulls = df[col_original].isnull().sum()
                df.rename(columns={col_original: col}, inplace=True)  # Renombrar al formato exacto
                return (col_original, cantidad_nulls)

    return None

def archivos_estandarizados(df):
    """
    Crea los archivos estandarizados con sus respectivos datos.
    - Reemplaza '>25' por 30 en la columna 'size'
    - Normaliza columnas clave y las renombra
    - Maneja específicamente los valores NA en weed_placement
    """
    df_estandar = pd.DataFrame()
    
    for col in COLUMNAS_A_BUSCAR:
        if col in df.columns:
            if col == "weed applied":
                df_estandar[col] = df[col].apply(estandarizar_applied).astype("Int64")
            elif col == "weed placement":
                # Convertir NA a None antes de la traducción
                df_estandar[col] = df[col].apply(lambda x: traducir_surco(x) if pd.notna(x) else None)
            elif col == "size":
                # Reemplazar '>25' por 30 antes de asignar
                df_estandar[col] = df[col].replace(">25", 30)
                df_estandar[col] = pd.to_numeric(df_estandar[col], errors='coerce')
            else:
                df_estandar[col] = df[col]
        else:
            df_estandar[col] = pd.NA
            st.warning(f"⚠️ Columna '{col}' no encontrada, se llenará con valores nulos")

    # Convertir nombres de columnas a formato estándar
    df_estandar.columns = [col.strip().lower().replace(" ", "_") for col in df_estandar.columns]

    # Asegurar que weed_placement sea tipo string con NA convertidos a None
    if 'weed_placement' in df_estandar.columns:
        df_estandar['weed_placement'] = df_estandar['weed_placement'].where(
            pd.notna(df_estandar['weed_placement']), 
            None
        )

    st.success(f"\n📄 Archivo procesado y estandarizado")
    st.dataframe(df_estandar, use_container_width=True)

    return df_estandar


def traducir_surco(valor):
    '''
    Traduce los valores de la columna 'weed placement' a un formato estándar en inglés.
    Maneja múltiples variaciones de texto y casos especiales.
    
    Args:
        valor: Valor a traducir (puede ser str, numérico o nulo)
        
    Returns:
        str: Valor traducido ('ROW', 'FURROW') o el original en mayúsculas si no hay coincidencia
        pd.NA: Para valores nulos o vacíos
    '''
    # Manejo de valores nulos o vacíos
    if pd.isna(valor) or str(valor).strip() == '':
        return None
    
    # Convertir a string y normalizar
    valor_str = str(valor).strip().lower()
    
    # Diccionario completo de traducciones
    traducciones = {
        # Español -> Inglés
        'surco': 'ROW',
        'entre surco': 'FURROW',
        'entre surcos': 'FURROW',
        'fila': 'ROW',
        'entre filas': 'FURROW',
        'línea': 'ROW',
        'entre líneas': 'FURROW',
        
        # Inglés -> Mantener formato estándar
        'row': 'ROW',
        'furrow': 'FURROW',
        'between rows': 'FURROW',
        'interrow': 'FURROW',
        
    }
    
    # Buscar coincidencia exacta
    if valor_str in traducciones:
        return traducciones[valor_str]
    
    # Manejar prefijos comunes
    if valor_str.startswith(('surco', 'fila', 'línea', 'row', 'sulco')):
        return 'ROW'
    if valor_str.startswith(('entre', 'between', 'inter')):
        return 'FURROW'
    
    # Si no se encuentra traducción, devolver el valor original en mayúsculas
    return str(valor).strip().upper()

def estandarizar_applied(valor):
    """
    Estandariza valores para la columna 'weed applied':
    - Acepta: 1, 0, 1.0, 0.0, '1', '0', '1.0', '0.0', 'true', 'false'
    - Devuelve: 1 o 0 (int)
    - Si no es válido, devuelve pd.NA
    """
    if pd.isna(valor):
        return pd.NA

    if isinstance(valor, (int, float)):
        if valor == 1 or valor == 1.0:
            return 1
        elif valor == 0 or valor == 0.0:
            return 0
    elif isinstance(valor, str):
        valor_limpio = valor.strip().lower()
        if valor_limpio in ['1', '1.0', 'true']:
            return 1
        elif valor_limpio in ['0', '0.0', 'false']:
            return 0

    st.warning(f"⚠️ Valor inválido en 'weed applied': '{valor}' → será reemplazado por vacío")
    return pd.NA