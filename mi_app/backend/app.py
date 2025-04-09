from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import time

app = Flask(__name__)
CORS(app)

def get_connection():
    return psycopg2.connect(
        host="db",
        dbname="testdb",
        user="postgres",
        password="postgres"
    )

def esperar_base_de_datos(max_intentos=10, espera_segundos=2):
    intentos = 0
    while intentos < max_intentos:
        try:
            conn = get_connection()
            conn.close()
            print("✅ Base de datos disponible.")
            return True
        except Exception as e:
            print(f"⏳ Esperando base de datos... intento {intentos+1}/{max_intentos}")
            time.sleep(espera_segundos)
            intentos += 1
    print("❌ No se pudo conectar a la base de datos después de varios intentos.")
    return False

def crear_tabla_usuarios():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabla 'usuarios' verificada o creada al iniciar")
    except Exception as e:
        print(f"❌ Error al crear la tabla 'usuarios': {e}")

@app.route('/')
def home():
    return "Hola desde el backend Flask"

@app.route('/db')
def db_test():
    try:
        conn = get_connection()
        conn.close()
        return "Conexión a base de datos exitosa"
    except Exception as e:
        return f"Error de conexión: {e}"

@app.route('/usuarios', methods=['POST'])
def agregar_usuario():
    data = request.get_json()
    nombre = data.get('nombre')
    correo = data.get('correo')
    if not nombre or not correo:
        return "Faltan campos", 400
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo = %s;", (correo,))
        existente = cur.fetchone()
        if existente:
            return f"El correo '{correo}' ya está registrado con ID {existente[0]}", 409
        cur.execute(
            "INSERT INTO usuarios (nombre, correo) VALUES (%s, %s) RETURNING id;",
            (nombre, correo)
        )
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"id": nuevo_id, "nombre": nombre, "correo": correo})
    except Exception as e:
        return f"Error al insertar usuario: {e}", 500

@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM usuarios;")
        usuarios = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(usuarios)
    except Exception as e:
        return f"Error al obtener usuarios: {e}", 500

if __name__ == '__main__':
    if esperar_base_de_datos():
        crear_tabla_usuarios()
    app.run(host='0.0.0.0')
