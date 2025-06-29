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
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT'))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_SSL_MODE'] = 'REQUIRED' 
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


# -----> END POITN PARA EL LOGIN DEL USUARIO ------------
@app.route('/api/login', methods=['POST'])
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


##  ------------------ END-POINTS PARA LA GESTIÓN DE USUARIOS POR PARTE DEL ADMINISTRADOR ---------
@app.route('/api/admin/usuarios-pendientes', methods=['GET'])
def obtener_usuarios_pendientes():
    try:
        cur = mysql.connection.cursor()
        
        # Obtener usuarios con rol 4 (pendientes)
        cur.execute("""
            SELECT 
                p.id,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.curp,
                p.rfc,
                u.id as usuario_id
            FROM personas p
            JOIN usuarios u ON p.id = u.persona_id
            JOIN usuarios_roles ur ON u.id = ur.usuario_id
            WHERE ur.rol_id = 4 AND u.activo = TRUE
        """)
        
        usuarios = cur.fetchall()
        cur.close()
        
        return jsonify({'success': True, 'usuarios': usuarios}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/asignar-rol', methods=['POST'])
def asignar_rol():
    try:
        data = request.get_json()
        usuario_id = data.get('usuario_id')
        nuevo_rol_id = data.get('rol_id')
        
        if not usuario_id or not nuevo_rol_id:
            return jsonify({'error': 'Datos incompletos'}), 400
            
        cur = mysql.connection.cursor()
        
        # Actualizar rol
        cur.execute("""
            UPDATE usuarios_roles 
            SET rol_id = %s 
            WHERE usuario_id = %s
        """, (nuevo_rol_id, usuario_id))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Rol actualizado correctamente'}), 200
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/desactivar-usuario', methods=['POST'])
def desactivar_usuario():
    try:
        usuario_id = request.json.get('usuario_id')
        
        if not usuario_id:
            return jsonify({'error': 'ID de usuario requerido'}), 400
            
        cur = mysql.connection.cursor()
        
        # Desactivar usuario (borrado lógico)
        cur.execute("""
            UPDATE usuarios 
            SET activo = FALSE 
            WHERE id = %s
        """, (usuario_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Usuario desactivado correctamente'}), 200
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500




# ---------------- END POINTS PARA EL LEVANTAMIENTO DE UNA DEMANDA --------------------------
@app.route('/api/demandas/generar-folio', methods=['GET'])
def generar_folio():
    try:
        cur = mysql.connection.cursor()
        
        # Obtener el último folio
        cur.execute("SELECT COUNT(*) as total FROM demandas")
        total = cur.fetchone()['total']
        nuevo_numero = total + 1
        folio = f"DEM-{datetime.now().year}-{nuevo_numero:04d}"
        
        return jsonify({'success': True, 'folio': folio}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/demandas/buscar-demandado', methods=['POST'])
def buscar_demandado():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        apellido_paterno = data.get('apellido_paterno')
        apellido_materno = data.get('apellido_materno')
        
        if not nombre or not apellido_paterno:
            return jsonify({'error': 'Nombre y apellido paterno son requeridos'}), 400
            
        cur = mysql.connection.cursor()
        
        query = """
            SELECT id FROM personas 
            WHERE nombre = %s 
            AND apellido_paterno = %s
        """
        params = [nombre, apellido_paterno]
        
        if apellido_materno:
            query += " AND apellido_materno = %s"
            params.append(apellido_materno)
        
        cur.execute(query, params)
        persona = cur.fetchone()
        cur.close()
        
        if not persona:
            return jsonify({'error': 'No se encontró al demandado'}), 404
            
        return jsonify({'success': True, 'persona_id': persona['id']}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/demandas/crear', methods=['POST'])
def crear_demanda():
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['folio', 'demandante_id', 'demandado_id', 'pretensiones', 'hechos', 'fundamento_derecho', 'tipo_accion']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Faltan campos obligatorios'}), 400
            
        cur = mysql.connection.cursor()
        
        # Insertar demanda
        cur.execute("""
            INSERT INTO demandas (
                folio, demandante_id, demandado_id, pretensiones, 
                hechos, fundamento_derecho, tipo_accion, estatus
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'registrada')
        """, (
            data['folio'],
            data['demandante_id'],
            data['demandado_id'],
            data['pretensiones'],
            data['hechos'],
            data['fundamento_derecho'],
            data['tipo_accion']
        ))
        
        mysql.connection.commit()
        demanda_id = cur.lastrowid
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Demanda creada exitosamente',
            'demanda_id': demanda_id
        }), 201
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    


    # ------ END POINTS PARA VER EL SEGUIMIENTO DE UNA DEMANDA DESDE EL PERFIL DEL USUARIO -----
@app.route('/api/demandas/mis-demandas', methods=['GET'])
def obtener_mis_demandas():
    try:
        persona_id = request.args.get('persona_id')
        if not persona_id:
            return jsonify({'error': 'ID de persona requerido'}), 400

        cur = mysql.connection.cursor()
        
        # Obtener demandas donde el usuario es demandante o demandado
        cur.execute("""
            SELECT 
                d.folio,
                d.tipo_accion,
                d.estatus,
                CONCAT(dp.nombre, ' ', dp.apellido_paterno) as demandante,
                CONCAT(dd.nombre, ' ', dd.apellido_paterno) as demandado,
                CONCAT(a.nombre, ' ', a.apellido_paterno) as autoridad
            FROM demandas d
            JOIN personas dp ON d.demandante_id = dp.id
            JOIN personas dd ON d.demandado_id = dd.id
            LEFT JOIN personas a ON d.autoridad_asignada_id = a.id
            WHERE d.demandante_id = %s OR d.demandado_id = %s
            ORDER BY d.fecha_creacion DESC
        """, (persona_id, persona_id))
        
        demandas = cur.fetchall()
        cur.close()
        
        # Si no hay autoridad asignada, mostrar "Por asignar"
        for demanda in demandas:
            if not demanda['autoridad']:
                demanda['autoridad'] = "Por asignar"
            if not demanda['estatus']:
                demanda['estatus'] = "Vigente"
        
        return jsonify({'success': True, 'demandas': demandas}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500