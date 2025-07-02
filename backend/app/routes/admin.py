from flask import Blueprint, request, jsonify, current_app
from app.db import mysql
import bcrypt
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/usuarios-pendientes', methods = ['GET'])
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
    

# ---> El administrador asigna un rol a un nuevo usuario 
@admin_bp.route('/asignar-rol', methods = ['POST'])
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
    

# ---> El administrador elimina un usuario del sistema 
@admin_bp.route('/desactivar-usuario', methods = ['POST'])
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