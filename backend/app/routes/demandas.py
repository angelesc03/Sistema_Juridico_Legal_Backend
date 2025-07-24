from flask import Blueprint, request, jsonify, current_app
from app.db import mysql
import bcrypt
import json
from datetime import datetime

demandas_bp = Blueprint('demandas', __name__)

# ---> Generar un nuevo folio para una demanda 
@demandas_bp.route('/generar-folio', methods=['GET'])
def generar_folio():
    try:
        cur = mysql.connection.cursor()
        
        # Obtener el total de demandas (maneja caso NULL o 0)
        cur.execute("SELECT COUNT(*) as total FROM demandas")
        result = cur.fetchone()
        total = result['total'] if result and result['total'] is not None else 0
        
        # Asegurar que el nuevo número sea 1 si no hay registros
        nuevo_numero = 1 if total == 0 else total + 1
        folio = f"DEM-{datetime.now().year}-{nuevo_numero:04d}"
        
        return jsonify({'success': True, 'folio': folio}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()  



# ---> Buscar un demandado 
@demandas_bp.route('/buscar-demandado', methods = ['POST'])
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

# ---> Generar una demanda
@demandas_bp.route('/crear', methods = ['POST'])
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
    

    
# ---> Gestión de demandas
@demandas_bp.route('/mis-demandas', methods = ['GET'])
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