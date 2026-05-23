from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from better_profanity import profanity
import os
import sys
import json
import uuid
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError:
    Database = None

app = Flask(__name__)
CORS(app)

profanity.load_censor_words()

# ============================================
# SERVIR ARCHIVOS ESTATICOS (CSS, JS, HTML)
# ============================================

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_html(filename):
    if filename.endswith('.html'):
        return send_from_directory('.', filename)
    return send_from_directory('.', filename)

# ============================================
# PALABRAS CLAVE PARA FLASHCARDS
# ============================================

PALABRAS_CLAVE = {
    '¿Qué es la Física?': ['fisica', 'materia', 'energia', 'espacio', 'tiempo', 'metodo cientifico'],
    'MRU': ['velocidad', 'distancia', 'tiempo', 'uniforme', 'rectilineo', 'constante'],
    'MRUA': ['aceleracion', 'velocidad', 'tiempo', 'desplazamiento', 'caida libre'],
    'Leyes de Newton': ['newton', 'inercia', 'fuerza', 'masa', 'aceleracion'],
    'Energía': ['cinetica', 'potencial', 'conservacion', 'trabajo', 'potencia'],
    'Vectores': ['vector', 'escalar', 'magnitud', 'direccion', 'componentes']
}

# ============================================
# FUNCION AYUDANTE
# ============================================

def get_db():
    if Database:
        return Database()
    return None

# ============================================
# API - REGISTRO
# ============================================

@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not nombre or not email or not password:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Minimo 6 caracteres'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Correo ya registrado'}), 400
        
        hashed = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO usuarios (id, nombre, email, password_hash) VALUES (%s, %s, %s, %s)",
            (user_id, nombre, email, hashed)
        )
        db.pg_conn.commit()
        cursor.close()
        return jsonify({'success': True, 'usuario_id': user_id})
    except Exception as e:
        print(f"ERROR REGISTRO: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al registrar'}), 500

# ============================================
# API - LOGIN
# ============================================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, nombre, password_hash FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
        
        return jsonify({'success': True, 'usuario_id': str(user['id']), 'nombre': user['nombre']})
    except Exception as e:
        print(f"ERROR LOGIN: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al iniciar sesion'}), 500

# ============================================
# API - TEMAS (ESTA ES LA QUE FALLA)
# ============================================

@app.route('/api/temas', methods=['GET'])
def obtener_temas():
    db = get_db()
    if not db:
        print("ERROR: No se pudo conectar a la base de datos")
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, nombre, orden, descripcion FROM temas ORDER BY orden")
        temas = cursor.fetchall()
        cursor.close()
        print(f"DEBUG: Se encontraron {len(temas)} temas")
        return jsonify({'success': True, 'temas': temas})
    except Exception as e:
        print(f"ERROR TEMAS: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================
# API - SUBTEMAS
# ============================================

@app.route('/api/temas/<int:tema_id>/subtemas', methods=['GET'])
def obtener_subtemas(tema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT id, tema_id, nombre, orden, contenido_html FROM subtemas WHERE tema_id = %s ORDER BY orden",
            (tema_id,)
        )
        subtemas = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'subtemas': subtemas})
    except Exception as e:
        print(f"ERROR SUBTEMAS: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================
# API - CONTENIDO
# ============================================

@app.route('/api/contenido/<int:subtema_id>', methods=['GET'])
def obtener_contenido(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, tema_id, nombre, orden, contenido_html FROM subtemas WHERE id = %s", (subtema_id,))
        subtema = cursor.fetchone()
        
        usuario_id = request.args.get('usuario_id')
        leido = False
        if usuario_id:
            cursor.execute(
                "SELECT leido FROM progreso WHERE usuario_id = %s::uuid AND subtema_id = %s",
                (usuario_id, subtema_id)
            )
            prog = cursor.fetchone()
            leido = prog['leido'] if prog else False
        
        cursor.close()
        
        if not subtema:
            return jsonify({'success': False, 'message': 'Subtema no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'subtema': subtema,
            'contenido': {
                'titulo': subtema['nombre'],
                'contenido_html': subtema['contenido_html'] or '<p>Contenido en construccion...</p>'
            },
            'leido': leido
        })
    except Exception as e:
        print(f"ERROR CONTENIDO: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================
# API - FLASHCARDS
# ============================================

@app.route('/api/flashcards/<int:subtema_id>', methods=['GET'])
def obtener_flashcards(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT nombre FROM subtemas WHERE id = %s", (subtema_id,))
        tema_info = cursor.fetchone()
        
        cursor.execute("""
            SELECT f.*, u.nombre as creador_nombre 
            FROM flashcards f 
            LEFT JOIN usuarios u ON f.creado_por = u.id
            WHERE f.subtema_id = %s AND f.estado = 'aprobada'
            ORDER BY f.es_oficial DESC, f.creado_en
        """, (subtema_id,))
        flashcards = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'flashcards': flashcards,
            'tema_nombre': tema_info['nombre'] if tema_info else '',
            'total': len(flashcards)
        })
    except Exception as e:
        print(f"ERROR FLASHCARDS: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/flashcards/crear', methods=['POST'])
def crear_flashcard():
    data = request.get_json()
    subtema_id = data.get('subtema_id')
    pregunta = data.get('pregunta', '').strip()
    respuesta = data.get('respuesta', '').strip()
    usuario_id = data.get('usuario_id')
    
    if not subtema_id or not pregunta or not respuesta:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        es_oficial = not usuario_id
        
        cursor.execute("""
            INSERT INTO flashcards (subtema_id, pregunta, respuesta, es_oficial, creado_por, estado)
            VALUES (%s, %s, %s, %s, %s::uuid, %s)
        """, (subtema_id, pregunta, respuesta, es_oficial, usuario_id if usuario_id else None, 'aprobada' if es_oficial else 'pendiente'))
        
        db.pg_conn.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Flashcard creada'})
    except Exception as e:
        print(f"ERROR CREAR FLASHCARD: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al crear'}), 500

# ============================================
# API - EXAMENES
# ============================================

@app.route('/api/examen/<int:subtema_id>', methods=['GET'])
def obtener_examen(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, subtema_id, pregunta, tipo, opciones, correcta, nivel FROM examenes WHERE subtema_id = %s ORDER BY RANDOM()", (subtema_id,))
        preguntas = cursor.fetchall()
        
        for p in preguntas:
            if p['opciones']:
                try:
                    p['opciones'] = json.loads(p['opciones'])
                except:
                    p['opciones'] = []
            else:
                p['opciones'] = None
        
        cursor.close()
        return jsonify({'success': True, 'preguntas': preguntas, 'total': len(preguntas)})
    except Exception as e:
        print(f"ERROR EXAMEN: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/examen/guardar-resultado', methods=['POST'])
def guardar_resultado():
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    subtema_id = data.get('subtema_id')
    aciertos = data.get('aciertos')
    total = data.get('total')
    
    if not all([usuario_id, subtema_id, aciertos is not None, total]):
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400
    
    porcentaje = (aciertos / total) * 100 if total > 0 else 0
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("""
            INSERT INTO resultados_examenes (usuario_id, subtema_id, aciertos, total, porcentaje)
            VALUES (%s::uuid, %s, %s, %s, %s)
        """, (usuario_id, subtema_id, aciertos, total, porcentaje))
        db.pg_conn.commit()
        cursor.close()
        return jsonify({'success': True, 'porcentaje': round(porcentaje, 2)})
    except Exception as e:
        print(f"ERROR GUARDAR RESULTADO: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al guardar'}), 500

# ============================================
# API - PROGRESO
# ============================================

@app.route('/api/progreso/<int:subtema_id>/marcar-leido', methods=['POST'])
def marcar_leido(subtema_id):
    data = request.get_json() or {}
    usuario_id = data.get('usuario_id')
    
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Usuario no identificado'}), 401
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexion'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT id FROM progreso WHERE usuario_id = %s::uuid AND subtema_id = %s",
            (usuario_id, subtema_id)
        )
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute(
                "UPDATE progreso SET leido = TRUE, ultimo_acceso = CURRENT_TIMESTAMP WHERE usuario_id = %s::uuid AND subtema_id = %s",
                (usuario_id, subtema_id)
            )
        else:
            cursor.execute(
                "INSERT INTO progreso (usuario_id, subtema_id, leido) VALUES (%s::uuid, %s, TRUE)",
                (usuario_id, subtema_id)
            )
        
        db.pg_conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"ERROR PROGRESO: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/progreso/general', methods=['GET'])
def progreso_general():
    return jsonify({'temas_leidos': 0, 'total_temas': 0, 'porcentaje': 0, 'detalle': []})

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
