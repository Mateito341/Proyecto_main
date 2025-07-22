import pandas as pd
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

def main():

    archivos = abrir_carpeta("input_planillas")
    if not archivos:
        return
    
    dataframes_procesados = verificar(archivos)
    if dataframes_procesados:  # Solo continuar si hay DataFrames procesados
        subir(dataframes_procesados)



#FUNCIONES VERIFICAR
def abrir_carpeta(carpeta): #hecho
    """
    Abre la carpeta que contiene la planilla de los distintos clientes en formato (.csv).
    
    Args:
        carpeta: carpeta donde se encuentran los archivos
    """
    archivos = glob.glob(f"{carpeta}/*.csv")

    if not archivos:
        print(f"⚠️ No se encontraron archivos en la carpeta '{carpeta}/'.")
        return []

    return archivos

def verificar(archivos):
    """
    Verifica los archivos y devuelve los DataFrames con columnas estandarizadas
    """
    dataframes_procesados = {}
    
    for archivo in archivos:
        try:
            df = pd.read_csv(archivo)
        except Exception as e:
            print(f"❌ Error al leer el archivo {archivo}: {e}")
            continue

        print(f"\n📄 Archivo leído: {archivo}")
        verificar_columnas(df)  # Esta función modifica el DataFrame directamente
        dataframes_procesados[archivo] = df
    
    return dataframes_procesados


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

    for col in COLUMNAS_A_BUSCAR:
        col_lower = col.lower()
        if col_lower in columnas_normalizadas:
            # Renombrar siempre a la versión exacta de COLUMNAS_A_BUSCAR
            col_original = mapeo_columnas[col_lower]
            if col_original != col:  # Solo renombrar si es diferente
                df.rename(columns={col_original: col}, inplace=True)
            cantidad_nulls = df[col].isnull().sum()
            print(f"✅ '{col}' está presente. Valores nulos: {cantidad_nulls}")
            verificar_tipo_dato(df, col, col)
        else:
            resultado = busqueda_profunda(col, columnas_normalizadas, df)
            if resultado:
                col_encontrada, nulos = resultado
                print(f"✅🔄 '{col}' fue encontrado como '{col_encontrada}' y renombrado. Valores nulos: {nulos}")
                verificar_tipo_dato(df, col, col)
            else:
                print(f"❌ '{col}' NO está presente.")


def verificar_tipo_dato(df, col_original, col_normalizado):
    """
    Verifica que los valores de una columna sean del tipo esperado.
    Para columnas numéricas ('weed diameter', 'size', 'height') debe ser float.
    Ademas verificar que la columna 'weed applied' sea del tipo correcto.
    
    Args:
        df: DataFrame
        col_original: nombre original (como está en el archivo)
        col_normalizado: nombre limpio (minúscula y sin espacios)
    """
    columnas_flotantes = ['weed diameter', 'size', 'height']

    if col_normalizado in columnas_flotantes:
        for idx, valor in df[col_original].items():
            if pd.notna(valor):
                try:
                    float(valor)
                except (ValueError, TypeError):
                    print(f"⚠️ Valor no flotante en '{col_original}' (fila {idx}): '{valor}'")

    elif col_normalizado == 'weed applied':
        valores_unicos = df[col_original].dropna().unique()
        for valor in valores_unicos:
            if valor not in [0, 1, '0', '1', None]:
                print(f"⚠️ Valor inesperado en 'weed applied': '{valor}'. Solo se permiten 0 y 1.")


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

#FUNCIONES SUBIR
def subir(dataframes_procesados):
    """
    Le pregunta al usuario si a partir de la información ofrecida quiere subir los datos a
    la base de datos. En caso de que si lo sube, sino, termina el programa.
    
    Args:
        archivos: archivos a subir
    """
    
    print("\n¿Deseás subirlo a la base de datos? (S/N)")
    respuesta = input().strip().upper()

    if respuesta == 'S':
        print("Subiendo a la base de datos...")
        base_datos_subir(dataframes_procesados)
    else:
        print("No se subieron los datos a la base de datos.")

def base_datos_subir(dataframes_procesados):
    """
    Sube los datos a la base de datos finalmente.
    
    Args:
        archivos: archivos a subir
    """ 

    #crear los archivos estandarizados
    archivos_estandarizados(dataframes_procesados)

    #funcion que los junta y sube a la base de datos
    df_unificado = juntar()

'''
    print("\n¿Estas seguo de que queres subir los datos a la base de datos? (S/N)")
    respuesta = input().strip().upper()

    if respuesta == 'S':
        subir_bd()
    else:
        print("No se subieron los datos a la base de datos.")
'''

def juntar(path_carpeta='output_planillas'):
    """
    Junta todos los archivos CSV de la carpeta dada y devuelve un DataFrame unificado.
    """
    archivos = glob.glob(os.path.join(path_carpeta, "*.csv"))
    if not archivos:
        print(f"⚠️ No se encontraron archivos CSV en {path_carpeta}")
        return None
    
    print(f"\nSe encontraron {len(archivos)} archivos para juntarlos...")
    
    lista_dfs = []
    
    for archivo in archivos:
        try:
            df = pd.read_csv(archivo)
            lista_dfs.append(df)
            print(f"🔵 Cargado archivo: {archivo}")
        except Exception as e:
            print(f"❌ Error al cargar {archivo}: {e}")
    
    if not lista_dfs:
        print("⚠️ No se cargó ningún archivo correctamente.")
        return None
    
    df_unificado = pd.concat(lista_dfs, ignore_index=True)
    
    # Crear carpeta base_datos si no existe
    carpeta_bd = 'base_datos'
    if not os.path.exists(carpeta_bd):
        os.makedirs(carpeta_bd)
    
    nombre_salida = f"Datos_unificados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ruta_salida = os.path.join(carpeta_bd, nombre_salida)
    df_unificado.to_csv(ruta_salida, index=False)
    print(f"✅ Archivo unificado guardado en: {ruta_salida}")
    
    return df_unificado


def subir_bd(df):
    """
    Sube el DataFrame a la base de datos SQLite.
    """

    conn = sqlite3.connect('mi_base_de_datos.db')
    try:
        df.to_sql('tabla_weeds', conn, if_exists='append', index=False)
    except Exception as e:
        print(f"❌ Error al subir a la base de datos: {e}")
    finally:
        conn.close()

def archivos_estandarizados(dataframes_procesados):
    """
    Crea los archivos estandarizados con sus respectivos datos, además de la fecha, 
    el nombre del cliente y quien lo subió (estos últimos dados por el usuario).
    Los guarda en la carpeta 'output_planillas'.
    
    El estándar incluye:
    - Columnas base: 'weed_count', 'date', 'client', 'user'
    - Columnas de datos: 'weed_diameter', 'size', 'height', 'weed_placement','weed_type', 'weed_name', 'weed_applied'
    
    Args:
        archivos: archivos a estandarizar
    """
    
    if not os.path.exists('output_planillas'):
        os.makedirs('output_planillas')
    
    for archivo, df in dataframes_procesados.items():
        print(f"\n📄 Procesando archivo: {archivo}")
        
        # Obtener metadatos
        while True:
            fecha = input("Ingrese la fecha del estudio (formato YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
                break
            except ValueError:
                print("Formato de fecha incorrecto. Use YYYY-MM-DD")
        
        cliente = input("Ingrese el nombre del cliente: ").strip()
        usuario = input("Ingrese su nombre: ").strip()
        
        # Crear DataFrame estandarizado
        df_estandar = pd.DataFrame()
        df_estandar['weed_count'] = range(1, len(df) + 1)
        df_estandar['date'] = fecha
        df_estandar['client'] = cliente
        df_estandar['user'] = usuario
        
        # Verificar columnas en el DataFrame ya procesado
        for col in COLUMNAS_A_BUSCAR:
            if col in df.columns:
                if col == "weed applied":
                    df_estandar[col] = df[col].apply(estandarizar_applied).astype("Int64")
                elif col == "weed placement":
                    df_estandar[col] = df[col].apply(traducir_surco).astype(str)
                else:
                    df_estandar[col] = df[col]
            else:
                df_estandar[col] = pd.NA
                print(f"⚠️ Columna '{col}' no encontrada, se llenará con valores nulos")

        # Guardar archivo
        nombre_salida = f"[estandarizado_{fecha}_{cliente}]_{os.path.basename(archivo)}"
        ruta_salida = os.path.join('output_planillas', nombre_salida)
        df_estandar.to_csv(ruta_salida, index=False)
        print(f"✅ Archivo guardado: {ruta_salida}")

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
        return pd.NA
    
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

    print(f"⚠️ Valor inválido en 'weed applied': '{valor}' → será reemplazado por vacío")
    return pd.NA

if __name__ == "__main__":
    main()
