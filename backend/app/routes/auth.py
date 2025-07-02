from flask import Blueprint, request, jsonify, current_app
from app.db import mysql
import bcrypt
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['POST'])
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

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        contrasena = data.get('contrasena')

        if not email or not contrasena:
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400

        cur = mysql.connection.cursor()

        # Verificar si el email existe y obtener datos adicionales
        cur.execute("""
            SELECT 
                u.id, 
                u.persona_id, 
                u.contrasena_hash, 
                ur.rol_id,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno
            FROM usuarios u
            JOIN personas p ON u.persona_id = p.id
            LEFT JOIN usuarios_roles ur ON u.id = ur.usuario_id
            WHERE p.email = %s
        """, (email,))
        
        usuario = cur.fetchone()
        cur.close()

        if not usuario:
            return jsonify({'error': 'Usuario no encontrado', 'codigo': 1}), 404

        # Verificar si el rol es 4 (no aprobado)
        if usuario['rol_id'] == 4:
            return jsonify({
                'error': 'Usuario en validación',
                'message': 'Sus credenciales se encuentran en proceso de validación. En poco tiempo podrá acceder al sistema',
                'codigo': 2
            }), 403

        # Verificar contraseña
        if not bcrypt.checkpw(contrasena.encode('utf-8'), usuario['contrasena_hash'].encode('utf-8')):
            return jsonify({'error': 'Credenciales inválidas', 'codigo': 3}), 401

        # Construir nombre completo
        nombre_completo = f"{usuario['nombre']} {usuario['apellido_paterno']}"
        if usuario['apellido_materno']:
            nombre_completo += f" {usuario['apellido_materno']}"

        # Determinar tipo de usuario según el rol
        tipo_usuario = ""
        if usuario['rol_id'] == 1:
            tipo_usuario = "Administrador"
        elif usuario['rol_id'] == 2:
            tipo_usuario = "Autoridad"
        elif usuario['rol_id'] == 3:
            tipo_usuario = "Usuario"

        # Login exitoso
        return jsonify({
            'success': True,
            'message': 'Bienvenido al sistema',
            'persona_id': usuario['persona_id'],
            'usuario_id': usuario['id'],
            'nombre_completo': nombre_completo,
            'tipo_usuario': tipo_usuario,
            'rol_id': usuario['rol_id']
        }), 200

    except Exception as e:
        app.logger.error(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error en el servidor', 'details': str(e)}), 500

@auth_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK', 'service': 'Sistema Jurídico Legal API'})
