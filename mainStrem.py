import streamlit as st
import pandas as pd
import datetime
import sqlite3
from sqlite3 import Error
from verificarStem import verificar_columnas, archivos_estandarizados

USERS = {
    "desarrollador": {
        "password": "456",  # En producción usa hashes y almacenamiento seguro
        "role": "desarrollador"
    },
    "cliente": {
        "password": "123",
        "role": "cliente"
    }
}

def login_section():
    """Muestra el formulario de login y maneja la autenticación"""
    st.title("🔑 Inicio de Sesión")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = USERS[username]["role"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# Verificar si el usuario está logueado
if "logged_in" not in st.session_state:
    login_section()
    st.stop()  # Detiene la ejecución del resto del código hasta que se loguee

# Inicializar variables de sesión para el CSV
if 'csv_confirmado' not in st.session_state:
    st.session_state['csv_confirmado'] = False
if 'df_estandarizado' not in st.session_state:
    st.session_state['df_estandarizado'] = None

# Configuración de la base de datos SQLite
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('ensayos.db')
        return conn
    except Error as e:
        st.error(f"Error al conectar a la base de datos: {str(e)}")
    return conn

def create_tables(conn):
    try:
        cursor = conn.cursor()
        
        # Tabla clientes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            sprai_id VARCHAR,
            modules_id VARCHAR
        )""")
        
        # Tabla ensayos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ensayos (
            ensayo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            test_date DATE,
            test_time TIME,
            FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
        )""")
        
        # Tabla ubicacion
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ubicacion (
            ensayo_id INTEGER PRIMARY KEY,
            farm TEXT,
            farm_address TEXT,
            field_location TEXT,
            latitude REAL,
            longitude REAL,
            soil_type TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla condiciones_ambientales
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS condiciones_ambientales (
            ensayo_id INTEGER PRIMARY KEY,
            ambient_temperature REAL,
            wind_speed REAL,
            relative_humidity REAL,
            wind_direction TEXT,
            ambient_light_intensity REAL,
            cloudiness REAL,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla cultivo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cultivo (
            ensayo_id INTEGER PRIMARY KEY,
            crop_specie TEXT,
            tillage TEXT,
            row_spacing REAL,
            crop_population INTEGER,
            crop_stage TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla pulverizadora
        cursor.execute("""
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
        )""")
        
        # Tabla colorante
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS colorante (
            ensayo_id INTEGER PRIMARY KEY,
            dye_used TEXT,
            dye_manufacturer TEXT,
            dye_concentration_ll REAL,
            dye_concentration_gl REAL,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla personal
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal (
            ensayo_id INTEGER PRIMARY KEY,
            machine_operator TEXT,
            trial_testers TEXT,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla herbicida
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS herbicida (
            ensayo_id INTEGER PRIMARY KEY,
            herbicide TEXT,
            dose INTEGER,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla modelo_deteccion
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS modelo_deteccion (
            ensayo_id INTEGER PRIMARY KEY,
            model_id TEXT,
            sens INTEGER,
            tile INTEGER,
            FOREIGN KEY (ensayo_id) REFERENCES ensayos(ensayo_id)
        )""")
        
        # Tabla resultados_malezas (simplificada para el ejemplo)
        cursor.execute("""
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
        )""")
        
        conn.commit()
    except Error as e:
        st.error(f"Error al crear tablas: {str(e)}")

# Inicializar la base de datos
conn = create_connection()
if conn is not None:
    create_tables(conn)

st.set_page_config(page_title="Formulario de Ensayos", layout="wide")

# Crear un contenedor de columnas para el encabezado
header = st.container()
with header:
    cols = st.columns([4, 1])  # 4 partes para el título, 1 para el botón
    
    with cols[0]:
        st.title("Formulario de Ensayos")
        st.write(f"Usuario: {st.session_state['username']} | Rol: {st.session_state['role']}")

    
    with cols[1]:
        # Espaciador para bajar el botón
        st.write("")  # Línea vacía
        st.write("")  # Otra línea vacía
        st.write("")  # Línea vacía
        st.write("")  # Línea vacía
        st.write("")  # Línea vacía
        
        # Botón de cerrar sesión con key único
        if st.button("🔒 Cerrar sesión", key="unique_logout_button"):
            st.session_state.clear()
            st.rerun()

# Lista de títulos de pestañas (strings)
tab_titles = [
    "🧑‍🌾 Información del Ensayo",
    "🌍 Condiciones del Lote",
    "📋 Detalles de Aplicación",
    "🛠️ Evaluación",
    "📤 Enviar"
]

# Añadir pestaña de desarrollo solo si es developer
if st.session_state.get("role") == "desarrollador":
    tab_titles.append("⚙️ Desarrollo")

# Crear las pestañas UNA SOLA VEZ
tabs = st.tabs(tab_titles)

# RECOLECTAMOS LOS DATOS FUERA DE CUALQUIER FORMULARIO
with tabs[0]:

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧾 Cliente")
        name = st.text_input("Nombre del cliente *")
        sprai_id = st.text_input("ID del sistema pulverizador")
        modules_id = st.text_input("ID de los módulo/s utilizados (SMXX0000)*")
        st.subheader("👷 Personal")
        machine_operator = st.text_input("Operador de la máquina")
        trial_testers = st.text_input("Evaluadores del ensayo *")
    with col2:
        st.subheader("🗓️ Datos del ensayo")
        test_date = st.date_input("Fecha del ensayo *", value=datetime.date.today())
        test_time = st.time_input("Hora del ensayo *", value=datetime.time(0, 0))

with tabs[1]:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📍 Ubicación")
        farm = st.text_input("Nombre de la finca")
        farm_address = st.text_input("Dirección de la finca")
        field_location = st.text_input("Ubicación del lote (link Google Maps) *")
        latitude = st.number_input("Latitud")
        longitude = st.number_input("Longitud")
        soil_type = st.text_input("Tipo de suelo")
    with col2:
        st.subheader("🌦️ Condiciones Ambientales")
        ambient_temperature = st.number_input("Temperatura ambiente (°C)")
        wind_speed = st.number_input("Velocidad del viento (km/h) *", min_value=0.0)
        relative_humidity = st.number_input("Humedad relativa (%)", min_value=0.0, max_value=100.0)
        wind_direction = st.text_input("Dirección del viento")
        ambient_light_intensity = st.number_input("Intensidad de luz (lux)", min_value=0.0)
        cloudiness = st.number_input("Nubosidad (%)", min_value=0.0, max_value=100.0, value=0.0)
    with col3:
        st.subheader("🌱 Cultivo")
        crop_specie = st.text_input("Especie del cultivo *")
        tillage = st.selectbox("¿Suelo labrado?", ["Sí", "No"])
        row_spacing = st.number_input("Distancia entre hileras(cm)", min_value=0.0)
        crop_population = st.number_input("Población por hectárea", min_value=0.0)
        crop_stage = st.text_input("Estado fenológico")

with tabs[2]:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🚜 Pulverizadora")
        sprayer_manufacturer = st.text_input("Fabricante")
        sprayer_model_number = st.text_input("Modelo")
        sprayer_year = st.text_input("Año de fabricación")
        nozzle_nomenclature = st.text_input("Nomenclatura de boquillas")
        nozzle_droplet_classification = st.text_input("Clasificación de gotas")
        nozzle_spacing = st.number_input("Espaciado de boquillas (cm)", min_value=0.0)
        boom_height = st.number_input("Altura del botalón (cm)", min_value=0.0)
        speed = st.number_input("Velocidad de avance (km/h) *", min_value=0.0)
        spray_pressure = st.number_input("Presión de aplicación (bar)", min_value=0.0)
        flow_rate = st.number_input("Caudal (L/min)", min_value=0.0)
    with col2:
        st.subheader("🧪 Colorante")
        dye_used = st.text_input("Tipo de colorante")
        dye_manufacturer = st.text_input("Fabricante", key="dye_manufacturer")
        dye_concentration_ll = st.number_input("Concentración (Líquido: l/l)", min_value=0.0)
        dye_concentration_gl = st.number_input("Concentración (Sólido: g/l)", min_value=0.0)
    with col3:
        st.subheader("💧 Herbicida")
        herbicide = st.text_input("Nombre del herbicida")
        dose = st.number_input("Dosis aplicada (l/ha)", min_value=0.0)

with tabs[3]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Resultados Malezas")
        st.write("Subí un archivo CSV con los datos de malezas *")
        csv_file = st.file_uploader("Cargar archivo CSV", type=["csv"])
        uploader = st.text_input("Persona que cargó los datos *")
    with col2:
        st.subheader("🌾 Modelo de Detección")
        model_id = st.text_input("ID del modelo de detección")
        sens = st.selectbox("Sensibilidad", [1, 2, 3])
        tile = st.selectbox("Baldosa", [1, 2, 3])

    if csv_file:
        try:
            df_csv = pd.read_csv(csv_file)
            dataframe_procesado, errores_tipo_dato = verificar_columnas(df_csv)
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")
            dataframe_procesado = None
            errores_tipo_dato = {"lectura": [str(e)]}
    else:
        dataframe_procesado = None
        errores_tipo_dato = {"archivo": ["No se cargó un archivo CSV."]}


    if st.button("Confirmar CSV y Estandarizar"):
        if dataframe_procesado is not None and not errores_tipo_dato:
            df_estandarizado = archivos_estandarizados(dataframe_procesado)
            st.session_state['df_estandarizado'] = df_estandarizado
            st.session_state['csv_confirmado'] = True
        elif dataframe_procesado is None:
            st.error("🚫 No se cargó un archivo CSV válido.")
            st.session_state['csv_confirmado'] = False
            st.session_state['df_estandarizado'] = None
        else:
            st.error("🚫 El archivo tiene errores de tipo de dato. No se puede estandarizar.")
            st.session_state['csv_confirmado'] = False
            st.session_state['df_estandarizado'] = None



with tabs[4]:
    st.subheader("Resumen")

    st.markdown("#### 🧑‍🌾 Información del Ensayo")
    st.write("**🧾 Cliente**")
    st.write(f"- Nombre: {name}")
    st.write(f"- ID Pulverizador: {sprai_id}")
    st.write(f"- ID Modulos: {modules_id}")
    st.write("**👷 Personal**")
    st.write(f"- Operador: {machine_operator}")
    st.write(f"- Evaluadores: {trial_testers}")
    st.write("**🗓️ Datos del ensayo**")
    st.write(f"- Fecha: {test_date}")
    st.write(f"- Hora: {test_time}")

    st.markdown("#### 🌍 Condiciones del Lote")
    st.write("**📍 Ubicación**")
    st.write(f"- Finca: {farm}")
    st.write(f"- Dirección: {farm_address}")
    st.write(f"- Ubicación: {field_location}")
    st.write(f"- Latitud: {latitude}")
    st.write(f"- Longitud: {longitude}")
    st.write(f"- Tipo de Suelo: {soil_type}")
    st.write("**🌦️ Condiciones Ambientales**")
    st.write(f"- Temperatura: {ambient_temperature} °C")
    st.write(f"- Velocidad del viento: {wind_speed} km/h")
    st.write(f"- Humedad relativa: {relative_humidity} %")
    st.write(f"- Dirección del viento: {wind_direction}")
    st.write(f"- Intensidad de luz: {ambient_light_intensity} (lux)")
    st.write(f"- Nubosidad: {cloudiness} %")
    st.write("**🌱 Cultivo**")
    st.write(f"- Cultivo: {crop_specie}")
    st.write(f"- Suelo labrado: {tillage}")
    st.write(f"- Distancia entre hileras: {row_spacing} cm")
    st.write(f"- Población por hectárea: {crop_population}")
    st.write(f"- Estado fenológico: {crop_stage}")

    st.markdown("#### 📋 Detalles de Aplicación")
    st.write("**🚜 Pulverizadora**")
    st.write(f"- Fabricante: {sprayer_manufacturer}")
    st.write(f"- Modelo: {sprayer_model_number}")
    st.write(f"- Año: {sprayer_year}")
    st.write(f"- Nomenclatura de boquillas: {nozzle_nomenclature}")
    st.write(f"- Clasificación de gotas: {nozzle_droplet_classification}")
    st.write(f"- Espaciado de boquillas: {nozzle_spacing} cm")
    st.write(f"- Altura del botalón: {boom_height} cm")
    st.write(f"- Velocidad: {speed} km/h")
    st.write(f"- Presión de aplicación: {spray_pressure} bar")
    st.write(f"- Caudal: {flow_rate} L/min")
    st.write("**🧪 Colorante**")
    st.write(f"- Tipo: {dye_used}")
    st.write(f"- Fabricante: {dye_manufacturer}")
    st.write(f"- Concentración: {dye_concentration_ll} (l/l)")
    st.write(f"- Sensibilidad: {dye_concentration_gl} (g/l)")
    st.write("**💧 Herbicida**")
    st.write(f"- Nombre: {herbicide}")
    st.write(f"- Dosis: {dose} (l/ha)")

    st.markdown("#### 🛠️ Evaluación")
    st.write("**🌾 Modelo de Detección**")
    st.write(f"- ID del modelo: {model_id}")
    st.write(f"- Sensibilidad: {sens}")
    st.write(f"- Baldosa: {tile}")
    if csv_file:
        st.write("- Archivo CSV cargado correctamente")

    st.subheader("Confirmar envío")

    # Solo el botón y el envío están en el formulario
    with st.form("form_envio"):
        submit_button = st.form_submit_button("Enviar Formulario Completo")
        
        if submit_button:
            errores = []
            
            if not name:
                errores.append("El nombre del cliente es obligatorio.")
            if not uploader:
                errores.append("El nombre del cargador de datos es obligatorio.")
            if not modules_id:
                errores.append("El ID de los módulos es obligatorio.")
            if not trial_testers:
                errores.append("Los evaluadores del ensayo son obligatorios.")
            if not test_date:
                errores.append("La fecha del ensayo es obligatoria.")
            if not test_time:
                errores.append("La hora del ensayo es obligatoria.")
            if not field_location:
                errores.append("La ubicación del lote es obligatoria.")
            if not wind_speed:
                errores.append("La velocidad del viento es obligatoria.")
            if not crop_specie:
                errores.append("La especie del cultivo es obligatoria.")
            if not speed:
                errores.append("La velocidad de la pulverizadora es obligatoria.")
            if not st.session_state['csv_confirmado'] or st.session_state['df_estandarizado'] is None:
                errores.append("Para enviar el formulario es obligatorio subir un archivo CSV válido y estandarizado.")


            # Mostrar errores
            if errores:
                for error in errores:
                    st.error(error)

            else:
                # Solo proceder si no hay errores y hay conexión a la BD
                if conn is not None:
                    try:
                        cursor = conn.cursor()

                        # Insertar cliente primero
                        cursor.execute(
                            "INSERT INTO clientes (name, sprai_id, modules_id) VALUES (?, ?, ?)",
                            (name, sprai_id, modules_id)
                        )

                        cliente_id = cursor.lastrowid
                        
                        # Insertar ensayo
                        cursor.execute(
                            "INSERT INTO ensayos (cliente_id, test_date, test_time) VALUES (?, ?, ?)",  # Nota la coma al final
                            (cliente_id, test_date, str(test_time))
                        )

                        ensayo_id = cursor.lastrowid 

                        # Insertar ubicación
                        cursor.execute(
                            """INSERT INTO ubicacion (
                                ensayo_id, farm, farm_address, field_location, 
                                latitude, longitude, soil_type
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (ensayo_id, farm, farm_address, field_location, 
                            latitude, longitude, soil_type)
                        )
                        
                        # Insertar condiciones ambientales
                        cursor.execute(
                            """INSERT INTO condiciones_ambientales (
                                ensayo_id, ambient_temperature, wind_speed, 
                                relative_humidity, wind_direction, ambient_light_intensity, cloudiness
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (ensayo_id, ambient_temperature, wind_speed, 
                            relative_humidity, wind_direction, ambient_light_intensity, cloudiness)
                        )
                        
                        # Insertar cultivo
                        cursor.execute(
                            """INSERT INTO cultivo (
                                ensayo_id, crop_specie, tillage, row_spacing, 
                                crop_population, crop_stage
                            ) VALUES (?, ?, ?, ?, ?, ?)""",
                            (ensayo_id, crop_specie, tillage, row_spacing, 
                            crop_population, crop_stage)
                        )
                        
                        # Insertar pulverizadora
                        cursor.execute(
                            """INSERT INTO pulverizadora (
                                ensayo_id, sprayer_manufacturer, sprayer_model_number, 
                                sprayer_year, nozzle_nomenclature, nozzle_droplet_classification, 
                                nozzle_spacing, boom_height, speed, spray_pressure, flow_rate
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (ensayo_id, sprayer_manufacturer, sprayer_model_number, 
                            sprayer_year, nozzle_nomenclature, nozzle_droplet_classification, 
                            nozzle_spacing, boom_height, speed, spray_pressure, flow_rate)
                        )
                        
                        # Insertar colorante
                        cursor.execute(
                            """INSERT INTO colorante (
                                ensayo_id, dye_used, dye_manufacturer, dye_concentration_ll, 
                                dye_concentration_gl
                            ) VALUES (?, ?, ?, ?, ?)""",
                            (ensayo_id, dye_used, dye_manufacturer, dye_concentration_ll, 
                            dye_concentration_gl)
                        )
                        
                        # Insertar personal
                        cursor.execute(
                            """INSERT INTO personal (
                                ensayo_id, machine_operator, trial_testers
                            ) VALUES (?, ?, ?)""",
                            (ensayo_id, machine_operator, trial_testers)
                        )
                        
                        # Insertar herbicida
                        cursor.execute(
                            """INSERT INTO herbicida (
                                ensayo_id, herbicide, dose
                            ) VALUES (?, ?, ?)""",
                            (ensayo_id, herbicide, dose)
                        )
                        
                        # Insertar modelo de detección
                        cursor.execute(
                            """INSERT INTO modelo_deteccion (
                                ensayo_id, model_id, sens, tile
                            ) VALUES (?, ?, ?, ?)""",
                            (ensayo_id, model_id, sens, tile)
                        )
                        
                        # Procesar archivo CSV si existe
                        df_estandarizado = st.session_state['df_estandarizado']
                        for _, row in df_estandarizado.iterrows():
                            try:
                                
                                weed_diameter = float(row.get('weed_diameter')) if pd.notnull(row.get('weed_diameter')) else None
                                size = float(row.get('size')) if pd.notnull(row.get('size')) else None
                                height = float(row.get('height')) if pd.notnull(row.get('height')) else None
                                weed_placement = str(row.get('weed_placement')) if pd.notnull(row.get('weed_placement')) else None
                                weed_type = str(row.get('weed_type')) if pd.notnull(row.get('weed_type')) else None
                                weed_name = str(row.get('weed_name')) if pd.notnull(row.get('weed_name')) else None
                                weed_applied = str(row.get('weed_applied')) if pd.notnull(row.get('weed_applied')) else None

                                cursor.execute(
                                    """INSERT INTO resultados_malezas (
                                        ensayo_id, uploader, weed_diameter, size, height,
                                        weed_placement, weed_type, weed_name, weed_applied
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ensayo_id, uploader, weed_diameter, size, height,
                                    weed_placement, weed_type, weed_name, weed_applied)
                                )
                            except Exception as row_error:
                                st.warning(f"Fila con error: {row.to_dict()} – {row_error}")
                        
                        conn.commit()
                        st.success("✅ Formulario enviado correctamente a la base de datos")
                        st.balloons()
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al enviar el formulario: {str(e)}")
                else:
                    st.error("No se pudo conectar a la base de datos. No se guardó la información.")

# Esto solo lo ve el desarrollador
if st.session_state.get("role") == "desarrollador" and len(tabs) > 5:
    with tabs[5]:
        st.header("Administración de Datos")
        
        if conn:
            # ==============================================
            # SECCIÓN PARA BORRAR ENSAYO ESPECÍFICO (CORRECCIÓN)
            # ==============================================
            st.subheader("✏️ Corregir Datos de Ensayo")

            # Obtener lista completa de ensayos con información relevante
            cursor = conn.cursor()
            query = """
            SELECT e.ensayo_id, e.test_date, c.name, e.test_time 
            FROM ensayos e
            JOIN clientes c ON e.cliente_id = c.cliente_id
            ORDER BY e.test_date DESC, e.test_time DESC
            """
            cursor.execute(query)
            ensayos = cursor.fetchall()
            
            if ensayos:
                # Crear opciones descriptivas para el selectbox
                opciones_ensayos = [
                    f"ID: {e[0]} | Fecha: {e[1]} {e[3]} | Cliente: {e[2]}"
                    for e in ensayos
                ]
                
                ensayo_seleccionado = st.selectbox(
                    "Seleccione el ensayo a corregir/eliminar:",
                    opciones_ensayos,
                    key="selector_ensayo_correccion"
                )
                
                # Extraer el ID del ensayo seleccionado
                ensayo_id = int(ensayo_seleccionado.split("ID: ")[1].split(" | ")[0]) if ensayo_seleccionado else None
                
                st.warning("ADVERTENCIA: Esta acción eliminará el ensayo de forma permanente.")
                confirmacion = st.checkbox(
                    f"Confirmar que desea eliminar el ensayo ID {ensayo_id}",
                    key=f"confirm_delete_{ensayo_id}"
                )
                
                if confirmacion and st.button("🗑️ ELIMINAR ENSAYO", key=f"delete_btn_{ensayo_id}"):
                    try:
                        # Lista de todas las tablas relacionadas con ensayos
                        tablas_relacionadas = [
                            "ubicacion", "condiciones_ambientales", "cultivo",
                            "pulverizadora", "colorante", "personal",
                            "herbicida", "modelo_deteccion", "resultados_malezas"
                        ]
                        
                        # Obtener cliente_id asociado al ensayo para posible limpieza
                        cursor.execute("SELECT cliente_id FROM ensayos WHERE ensayo_id = ?", (ensayo_id,))
                        cliente_id = cursor.fetchone()[0]
                        
                        # 1. Borrar datos en tablas relacionadas
                        for tabla in tablas_relacionadas:
                            cursor.execute(f"DELETE FROM {tabla} WHERE ensayo_id = ?", (ensayo_id,))
                        
                        # 2. Borrar el registro principal del ensayo
                        cursor.execute("DELETE FROM ensayos WHERE ensayo_id = ?", (ensayo_id,))
                        
                        # 3. Verificar si el cliente queda sin ensayos y opcionalmente borrarlo
                        cursor.execute("SELECT COUNT(*) FROM ensayos WHERE cliente_id = ?", (cliente_id,))
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("DELETE FROM clientes WHERE cliente_id = ?", (cliente_id,))
                        
                        conn.commit()
                        st.success(f"✅ Ensayo ID {ensayo_id} y todos sus datos asociados fueron eliminados correctamente")
                        st.balloons()
                        st.rerun()  # Refrescar la vista
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Error al eliminar el ensayo: {str(e)}")
            
            else:
                st.info("No hay ensayos registrados en la base de datos")

            # SECCIÓN PARA RESETEO COMPLETO (MANTENIMIENTO)
            st.markdown("---")
            st.subheader("🧹 Limpieza de Datos")

            st.warning("ADVERTENCIA: Esta acción eliminará TODOS los ensayos de forma permanente.")

            confirmar_reset = st.checkbox("Confirmar", key="confirm_reset_total")

            if confirmar_reset and st.button("🗑️ ELIMINAR TODOS LOS ENSAYOS", key="reset_btn"):
                try:
                    cursor = conn.cursor()

                    # Primero se borran las tablas hijas
                    tablas_hijas = [
                        "ubicacion", "condiciones_ambientales", "cultivo", "pulverizadora",
                        "colorante", "personal", "herbicida", "modelo_deteccion", "resultados_malezas"
                    ]
                    for tabla in tablas_hijas:
                        cursor.execute(f"DELETE FROM {tabla}")

                    # Luego las tablas principales
                    cursor.execute("DELETE FROM ensayos")
                    cursor.execute("DELETE FROM clientes")

                    conn.commit()
                    st.success("✅ Todas las tablas fueron vaciadas correctamente.")
                    st.balloons()
                    st.rerun()  # Para refrescar la interfaz
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error al resetear tablas: {str(e)}")

            # VISUALIZACIÓN DE DATOS
            st.markdown("---")
            st.subheader("🔍 Exploración de Datos")
            
            with st.expander("Ver contenido de tablas"):
                table_to_view = st.selectbox(
                    "Seleccione tabla a visualizar:",
                    [
                        "clientes", "ensayos", "ubicacion", "condiciones_ambientales",
                        "cultivo", "pulverizadora", "colorante", "personal",
                        "herbicida", "modelo_deteccion", "resultados_malezas"
                    ],
                    key="table_selector"
                )
                
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_to_view}", conn)
                    st.dataframe(df)
                    
                    # Mostrar conteo de registros
                    st.info(f"Total de registros: {len(df)}")
                    
                except Exception as e:
                    st.error(f"No se pudo leer la tabla: {str(e)}")
        
        else:
            st.error("No hay conexión a la base de datos")