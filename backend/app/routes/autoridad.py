from flask import Blueprint, request, jsonify, current_app
from app.db import mysql
import bcrypt
import json

autoridad_bp = Blueprint('autoridad', __name__)

@autoridad_bp.route('/autoridad/pendientes', methods=['GET'])
def demandas_pendientes():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, folio, tipo_accion, fecha_creacion, pretensiones
            FROM demandas
            WHERE autoridad_asignada_id IS NULL
            ORDER BY fecha_creacion DESC
        """)
        demandas = cur.fetchall()
        return jsonify({'demandas': demandas}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    





@autoridad_bp.route('/autoridad/asignar/<int:demanda_id>', methods=['PUT'])
def asignar_autoridad(demanda_id):
    try:
        data = request.get_json()
        autoridad_id = data.get('autoridad_id')

        if not autoridad_id:
            return jsonify({'error': 'ID de autoridad requerido'}), 400

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE demandas
            SET autoridad_asignada_id = %s
            WHERE id = %s
        """, (autoridad_id, demanda_id))
        mysql.connection.commit()
        return jsonify({'message': 'Demanda asignada correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@autoridad_bp.route('/autoridad/activos/<int:autoridad_id>', methods=['GET'])
def casos_activos(autoridad_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, folio, tipo_accion, estatus
            FROM demandas
            WHERE autoridad_asignada_id = %s
            ORDER BY fecha_creacion DESC
        """, (autoridad_id,))
        demandas = cur.fetchall()
        return jsonify({'demandas': demandas}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
