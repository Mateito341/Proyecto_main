import sqlite3
from dash import Dash, html, dash_table
import pandas as pd

app = Dash(__name__)

# Conexión a la base de datos
conn = sqlite3.connect('ensayos.db')  # Asegúrate de que la ruta sea correcta

# Consulta SQL para obtener datos (ejemplo)
query = "SELECT * FROM tabla_ensayos"  # Reemplaza "tabla_ensayos" con tu tabla real
df = pd.read_sql_query(query, conn)

# Cerrar conexión
conn.close()

# Mostrar los datos en una tabla de Dash
app.layout = html.Div([
    html.H1("Datos de Ensayos"),
    dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        page_size=10
    )
])

if __name__ == '__main__':
    app.run(debug=True)