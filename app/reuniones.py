from flask import Blueprint, jsonify, request
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

reuniones_bp = Blueprint('reuniones', __name__)

asignaciones_mapping = {
    'Presidencia': 1,
    'Oración': 2,
    'Tesoros de la Biblia': 3,
    'Perlas Escondidas': 4,
    'Lectura de la Biblia': 5,
    'Empiece Conversaciones': 6,
    'Haga Revisitas': 7,
    'Haga Discípulos': 8,
    'Explique Creencias': 9,
    'Amo/a de casa': 10,
    'Discurso': 11,
    'Análisis Seamos Mejores Maestros': 12,
    'Nuestra Vida Cristiana': 13,
    'Estudio Bíblico de congregación': 14,
    'Lectura libro': 15,
    'Necesidades de la congregación': 16
}

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('SUPABASE_DB_NAME'),
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        host=os.getenv('SUPABASE_DB_HOST'),
        port=os.getenv('SUPABASE_DB_PORT')
    )

@reuniones_bp.route('/reuniones', methods=['GET'])
def gestionar_reuniones():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT reuniones.fecha, reuniones.sala, 
                   asignaciones.nombre_asign AS Asignacion, 
                   hermanos_titular.nombre_hermano || ' ' || hermanos_titular.apellido_hermano AS Titular, 
                   CASE WHEN reuniones.ayudante IS NULL THEN ' ' ELSE hermanos_suplente.nombre_hermano || ' ' || hermanos_suplente.apellido_hermano END AS Ayudante 
            FROM reuniones 
            INNER JOIN asignaciones ON reuniones.id_Asign = asignaciones.id_asign 
            INNER JOIN hermanos AS Hermanos_titular ON reuniones.id_hermano = Hermanos_titular.id_hermano 
            LEFT JOIN hermanos AS Hermanos_suplente ON reuniones.ayudante = Hermanos_suplente.id_hermano
        ''')
        reuniones = cursor.fetchall()
        conn.close()

        reuniones_info = []
        for reunion in reuniones:
            reunion_info = {
                'Fecha': reunion[0],
                'Sala': reunion[1],
                'Asignacion': reunion[2],
                'Titular': reunion[3],
                'Ayudante': reunion[4]
            }
            reuniones_info.append(reunion_info)

        return jsonify(reuniones_info)


@reuniones_bp.route('/reuniones-semana-actual', methods=['GET'])
def obtener_reuniones_semana_actual():
    return obtener_reuniones_por_semana(0)

@reuniones_bp.route('/reuniones-semana-siguiente', methods=['GET'])
def obtener_reuniones_semana_siguiente():
    return obtener_reuniones_por_semana(1)

def obtener_reuniones_por_semana(semana_offset):
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=semana_offset)
    next_monday = monday + timedelta(days=7)

    cursor.execute('''
        SELECT reuniones.fecha, reuniones.sala, 
               asignaciones.nombre_asign AS Asignacion, 
               hermanos_titular.nombre_hermano || ' ' || hermanos_titular.apellido_hermano AS Titular, 
               CASE WHEN reuniones.ayudante IS NULL THEN ' ' ELSE hermanos_suplente.nombre_hermano || ' ' || hermanos_suplente.apellido_hermano END AS Ayudante 
        FROM reuniones 
        INNER JOIN asignaciones ON reuniones.id_Asign = asignaciones.id_asign 
        INNER JOIN hermanos AS Hermanos_titular ON reuniones.id_hermano = Hermanos_titular.id_hermano 
        LEFT JOIN hermanos AS Hermanos_suplente ON reuniones.ayudante = Hermanos_suplente.id_hermano
        WHERE reuniones.fecha >= %s AND reuniones.fecha < %s
    ''', (monday.date(), next_monday.date()))

    reuniones = cursor.fetchall()
    conn.close()

    reuniones_info = []
    for reunion in reuniones:
        reunion_info = {
            'Fecha': reunion[0],
            'Sala': reunion[1],
            'Asignacion': reunion[2],
            'Titular': reunion[3],
            'Ayudante': reunion[4]
        }
        reuniones_info.append(reunion_info)

    if not reuniones_info:
        return jsonify({'message': 'No hay reuniones programadas para esa semana.'}), 404

    return jsonify(reuniones_info), 200