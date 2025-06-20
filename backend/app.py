from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import bcrypt
import json
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://angelesc03.github.io"}})
 

# Configuración de MySQL (ajusta estos valores)
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYS_QLUSER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DATABASE')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/api/registro', methods=['POST'])
def registro():
    try:
        data = request.get_json()
        
        # Validación de campos obligatorios
        required_fields = [
            'nombre', 'apellido_paterno', 'curp', 'telefono', 
            'email', 'contrasena', 'domicilio'
        ]
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Faltan campos obligatorios'}), 400

        # Validar estructura del domicilio
        domicilio_required = ['calle', 'numero', 'colonia', 'municipio', 'estado', 'cp']
        if not all(key in data['domicilio'] for key in domicilio_required):
            return jsonify({'error': 'Domicilio incompleto'}), 400

        # Construir nombre completo
        nombre_completo = f"{data['nombre']} {data['apellido_paterno']}"
        if data.get('apellido_materno'):
            nombre_completo += f" {data['apellido_materno']}"

        # Convertir domicilio a JSON
        domicilio_json = json.dumps(data['domicilio'])

        # Hash de contraseña
        hashed_password = bcrypt.hashpw(data['contrasena'].encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()

        # Verificar si el email ya existe
        cur.execute("SELECT id FROM personas WHERE email = %s", (data['email'],))
        if cur.fetchone():
            return jsonify({'error': 'El email ya está registrado'}), 400

        # Verificar si la CURP ya existe
        cur.execute("SELECT id FROM personas WHERE curp = %s", (data['curp'],))
        if cur.fetchone():
            return jsonify({'error': 'La CURP ya está registrada'}), 400

        # Insertar persona (adaptado a tu estructura de base de datos)
        cur.execute("""
            INSERT INTO personas (
                nombre, apellido_paterno, apellido_materno, curp, rfc,
                calle, numero_exterior, numero_interior, colonia,
                municipio, estado, codigo_postal, telefono, email, grupo_vulnerable
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['nombre'],
            data['apellido_paterno'],
            data.get('apellido_materno'),
            data['curp'],
            data.get('rfc'),
            data['domicilio']['calle'],
            data['domicilio']['numero'],
            data['domicilio'].get('interior'),
            data['domicilio']['colonia'],
            data['domicilio']['municipio'],
            data['domicilio']['estado'],
            data['domicilio']['cp'],
            data['telefono'],
            data['email'],
            data.get('grupo_vulnerable', False)
        ))

        persona_id = cur.lastrowid

        # Insertar usuario (sin rol)
        cur.execute("""
            INSERT INTO usuarios (
                persona_id, contrasena_hash, activo
            ) VALUES (%s, %s, TRUE)
        """, (persona_id, hashed_password))

        usuario_id = cur.lastrowid  # Obtener el ID del usuario recién insertado

        # Insertar en la tabla usuarios_roles con rol_id fijo (por ejemplo 4)
        cur.execute("""
            INSERT INTO usuarios_roles (
                usuario_id, rol_id
            ) VALUES (%s, %s)
        """, (usuario_id, 4))
        mysql.connection.commit()
        cur.close()

        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'persona_id': persona_id
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        app.logger.error(f"Error en registro: {str(e)}")
        return jsonify({
            'error': 'Error en el servidor',
            'details': str(e)
        }), 500

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK', 'service': 'Sistema Jurídico Legal API'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)