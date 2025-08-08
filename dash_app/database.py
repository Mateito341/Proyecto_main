# Conexión y consultas a SQLite
import sqlite3
import pandas as pd

DB_PATH = "/home/user/Documentos/Proyecto_main/ensayos.db"

def _run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obtener_datos_malezas():
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
    df = _run_query(query)
    df['size'] = df['size'].replace(0, float('nan'))
    return df

def obtener_datos_mapa():
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
    return _run_query(query)

def obtener_datos_aplico():
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
    df = _run_query(query)
    # Limpieza de columnas (igual que en tu código)
    df.loc[:, 'sensitivity'] = pd.to_numeric(df['sensitivity'], errors='coerce')
    df = df.loc[df['sensitivity'].isin([1, 2, 3]) | df['sensitivity'].isna()]
    if 'tile' in df.columns:
        df.loc[:, 'tile'] = pd.to_numeric(df['tile'], errors='coerce')
        df = df.loc[df['tile'].isin([1, 2, 3]) | df['tile'].isna()]
    df['size'] = df['size'].replace(0, float('nan'))
    return df
