# Conexión y creación de tablas
import sqlite3
from sqlite3 import Error
import streamlit as st
from config import DB_PATH

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('ensayos.db')
        return conn
    except Error as e:
        st.error(f"Error al conectar a la base de datos: {str(e)}")
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    tablas = {
        
        # Tabla clientes
        "clientes": """
        CREATE TABLE IF NOT EXISTS clientes (
            cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            sprai_id VARCHAR,
            modules_id VARCHAR
        )""",
        
        # Tabla ensayos
        "ensayos": """
        CREATE TABLE IF NOT EXISTS ensayos (
            ensayo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            test_date DATE,
            test_time TIME,
            FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
        )""",
        
        # Tabla ubicacion
        "ubicacion": """
        CREATE TABLE IF NOT EXISTS ubicacion (
            ensayo_id INTEGER PRIMARY KEY,
            farm TEXT,
            farm_address TEXT,
            field_location TEXT,
            latitude REAL,
            longitude REAL,
            soil_type TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla condiciones_ambientales
        "condiciones_ambientales": """
        CREATE TABLE IF NOT EXISTS condiciones_ambientales (
            ensayo_id INTEGER PRIMARY KEY,
            ambient_temperature REAL,
            wind_speed REAL,
            relative_humidity REAL,
            wind_direction TEXT,
            ambient_light_intensity REAL,
            cloudiness REAL,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla cultivo
        "cultivo": """
        CREATE TABLE IF NOT EXISTS cultivo (
            ensayo_id INTEGER PRIMARY KEY,
            crop_specie TEXT,
            tillage TEXT,
            row_spacing REAL,
            crop_population INTEGER,
            crop_stage TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla pulverizadora
        "pulverizadora": """
        CREATE TABLE IF NOT EXISTS pulverizadora (
            ensayo_id INTEGER PRIMARY KEY,
            sprayer_manufacturer TEXT,
            sprayer_model_number TEXT,
            sprayer_year INTEGER,
            nozzle_nomenclature TEXT,
            nozzle_droplet_classification TEXT,
            nozzle_spacing REAL,
            boom_height REAL,
            speed REAL,
            spray_pressure REAL,
            flow_rate REAL,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla colorante
        "colorante": """
        CREATE TABLE IF NOT EXISTS colorante (
            ensayo_id INTEGER PRIMARY KEY,
            dye_used TEXT,
            dye_manufacturer TEXT,
            dye_concentration_ll REAL,
            dye_concentration_gl REAL,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla personal
        "personal": """
        CREATE TABLE IF NOT EXISTS personal (
            ensayo_id INTEGER PRIMARY KEY,
            machine_operator TEXT,
            trial_testers TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla herbicida
        "herbicida": """
        CREATE TABLE IF NOT EXISTS herbicida (
            ensayo_id INTEGER PRIMARY KEY,
            herbicide TEXT,
            dose INTEGER,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla modelo_deteccion
        "modelo_deteccion": """
        CREATE TABLE IF NOT EXISTS modelo_deteccion (
            ensayo_id INTEGER PRIMARY KEY,
            model_id TEXT,
            sens INTEGER,
            tile INTEGER,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""",
        
        # Tabla resultados_malezas (simplificada para el ejemplo)
        "resultados_malezas": """
        CREATE TABLE IF NOT EXISTS resultados_malezas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ensayo_id INTEGER,
            uploader TEXT,
            weed_diameter REAL,
            size REAL,
            height REAL,
            weed_placement TEXT,
            weed_type TEXT,
            weed_name TEXT,
            weed_applied INTEGER,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )"""
    }
    for sql in tablas.values():
        cursor.execute(sql)
    conn.commit()
