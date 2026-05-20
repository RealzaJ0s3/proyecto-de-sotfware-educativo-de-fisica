from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from better_profanity import profanity
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import Database
except ImportError:
    Database = None

app = Flask(__name__)
CORS(app)

profanity.load_censor_words()

PALABRAS_CLAVE = {
    '¿Qué es la Física?': ['física', 'materia', 'energía', 'espacio', 'tiempo', 'método científico', 'mecánica', 'electromagnetismo', 'termodinámica', 'newton', 'ley', 'fenómeno'],
    'MRU': ['velocidad', 'distancia', 'tiempo', 'uniforme', 'rectilíneo', 'constante', 'm/s', 'km/h', 'trayectoria', 'ecuación'],
    'MRUA': ['aceleración', 'velocidad', 'tiempo', 'desplazamiento', 'uniformemente', 'caída libre', 'gravedad', 'm/s²', 'ecuaciones'],
    'Leyes de Newton': ['newton', 'inercia', 'fuerza', 'masa', 'aceleración', 'acción', 'reacción', 'f=ma', 'equilibrio'],
    'Energía': ['cinética', 'potencial', 'conservación', 'trabajo', 'potencia', 'julios', 'vatios', 'mecánica', 'térmica'],
    'Vectores': ['vector', 'escalar', 'magnitud', 'dirección', 'componentes', 'suma', 'resultante', 'i', 'j', 'k']
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/contenido.html')
def contenido_page():
    return send_from_directory('.', 'contenido.html')

@app.route('/flashcards.html')
def flashcards_page():
    return send_from_directory('.', 'flashcards.html')

@app.route('/examen.html')
def examen_page():
    return send_from_directory('.', 'examen.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

def get_db():
    if Database:
        return Database()
    return None

@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not nombre or not email or not password:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Este correo ya está registrado'}), 400
        
        hashed = generate_password_hash(password)
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                      (nombre, email, hashed))
        db.connection.commit()
        return jsonify({'success': True, 'usuario_id': cursor.lastrowid})
    except Exception as e:
        print(f"Error registro: {e}")
        return jsonify({'success': False, 'message': 'Error al registrar'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contraseña obligatorios'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, nombre, password FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Email o contraseña incorrectos'}), 401
        
        return jsonify({'success': True, 'usuario_id': user['id'], 'nombre': user['nombre']})
    except Exception as e:
        print(f"Error login: {e}")
        return jsonify({'success': False, 'message': 'Error al iniciar sesión'}), 500

@app.route('/api/temas', methods=['GET'])
def obtener_temas():
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT DISTINCT tema, orden_tema FROM subtemas ORDER BY orden_tema")
        temas = cursor.fetchall()
        return jsonify({'success': True, 'temas': temas})
    except Exception as e:
        print(f"Error temas: {e}")
        return jsonify({'success': False, 'message': 'Error al cargar temas'}), 500

@app.route('/api/temas/<tema>/subtemas', methods=['GET'])
def obtener_subtemas(tema):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT id, subtema, orden_subtema FROM subtemas WHERE tema = %s ORDER BY orden_subtema", (tema,))
        subtemas = cursor.fetchall()
        return jsonify({'success': True, 'subtemas': subtemas})
    except Exception as e:
        print(f"Error subtemas: {e}")
        return jsonify({'success': False, 'message': 'Error al cargar subtemas'}), 500

@app.route('/api/contenido/<int:subtema_id>', methods=['GET'])
def obtener_contenido(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("SELECT s.*, s.tema as tema_nombre FROM subtemas s WHERE s.id = %s", (subtema_id,))
        subtema = cursor.fetchone()
        
        cursor.execute("SELECT titulo, contenido_html FROM contenidos WHERE subtema_id = %s", (subtema_id,))
        contenido = cursor.fetchone()
        
        usuario_id = request.args.get('usuario_id')
        leido = False
        if usuario_id:
            cursor.execute(
                "SELECT leido FROM progreso WHERE usuario_id = %s AND tema_id = %s",
                (int(usuario_id), subtema_id)
            )
            prog = cursor.fetchone()
            leido = prog['leido'] if prog else False
        
        if not contenido:
            return jsonify({
                'success': True,
                'subtema': subtema,
                'contenido': {
                    'titulo': subtema['subtema'],
                    'contenido_html': '<p>Contenido en construcción...</p>'
                },
                'leido': leido
            })
        
        return jsonify({
            'success': True,
            'subtema': subtema,
            'contenido': contenido,
            'leido': leido
        })
    except Exception as e:
        print(f"Error contenido: {e}")
        return jsonify({'success': False, 'message': 'Error al cargar contenido'}), 500

def validar_flashcard(pregunta, respuesta, tema_nombre):
    texto_completo = f"{pregunta} {respuesta}".lower()
    
    if profanity.contains_profanity(pregunta) or profanity.contains_profanity(respuesta):
        return {'valido': False, 'mensaje': 'La flashcard contiene lenguaje inapropiado'}
    
    if len(pregunta) < 10 or len(respuesta) < 10:
        return {'valido': False, 'mensaje': 'La pregunta y respuesta deben tener al menos 10 caracteres'}
    
    palabras_clave = PALABRAS_CLAVE.get(tema_nombre, [])
    if palabras_clave:
        tiene_palabra_clave = any(palabra in texto_completo for palabra in palabras_clave)
        if not tiene_palabra_clave:
            return {'valido': False, 'mensaje': f'La flashcard no parece relacionada con el tema. Debe incluir conceptos como: {", ".join(palabras_clave[:5])}'}
    
    return {'valido': True, 'mensaje': 'Flashcard válida'}

@app.route('/api/flashcards/<int:subtema_id>', methods=['GET'])
def obtener_flashcards(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("SELECT tema FROM subtemas WHERE id = %s", (subtema_id,))
        tema_info = cursor.fetchone()
        tema_nombre = tema_info['tema'] if tema_info else ''
        
        cursor.execute("""
            SELECT f.*, u.nombre as creador_nombre 
            FROM flashcards f 
            LEFT JOIN usuarios u ON f.creado_por = u.id
            WHERE f.subtema_id = %s AND f.estado = 'aprobada'
            ORDER BY f.es_oficial DESC, f.fecha_creacion
        """, (subtema_id,))
        flashcards = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'flashcards': flashcards,
            'tema_nombre': tema_nombre,
            'total': len(flashcards)
        })
    except Exception as e:
        print(f"Error flashcards: {e}")
        return jsonify({'success': False, 'message': 'Error al cargar flashcards'}), 500

@app.route('/api/flashcards/crear', methods=['POST'])
def crear_flashcard():
    data = request.get_json()
    subtema_id = data.get('subtema_id')
    pregunta = data.get('pregunta', '').strip()
    respuesta = data.get('respuesta', '').strip()
    usuario_id = data.get('usuario_id')
    
    if not subtema_id or not pregunta or not respuesta:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("SELECT tema FROM subtemas WHERE id = %s", (subtema_id,))
        tema_info = cursor.fetchone()
        if not tema_info:
            return jsonify({'success': False, 'message': 'Subtema no encontrado'}), 404
        
        tema_nombre = tema_info['tema']
        
        validacion = validar_flashcard(pregunta, respuesta, tema_nombre)
        if not validacion['valido']:
            return jsonify({'success': False, 'message': validacion['mensaje']}), 400
        
        es_oficial = not usuario_id
        
        cursor.execute("""
            INSERT INTO flashcards (subtema_id, pregunta, respuesta, es_oficial, creado_por, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (subtema_id, pregunta, respuesta, es_oficial, usuario_id, 'aprobada' if es_oficial else 'pendiente'))
        
        db.connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Flashcard creada correctamente' + (' (pendiente de aprobación)' if not es_oficial else ''),
            'flashcard_id': cursor.lastrowid
        })
        
    except Exception as e:
        print(f"Error crear flashcard: {e}")
        return jsonify({'success': False, 'message': 'Error al crear flashcard'}), 500

@app.route('/api/flashcards/estudiar', methods=['POST'])
def registrar_estudio():
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    flashcard_id = data.get('flashcard_id')
    la_sabe = data.get('la_sabe', False)
    
    if not usuario_id or not flashcard_id:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("""
            INSERT INTO flashcards_estudio (usuario_id, flashcard_id, la_sabe)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE la_sabe = %s, fecha_estudio = CURRENT_TIMESTAMP
        """, (int(usuario_id), flashcard_id, la_sabe, la_sabe))
        
        db.connection.commit()
        
        return jsonify({'success': True, 'message': 'Progreso guardado'})
    except Exception as e:
        print(f"Error estudio: {e}")
        return jsonify({'success': False, 'message': 'Error al guardar progreso'}), 500

@app.route('/api/flashcards/progreso/<int:subtema_id>', methods=['GET'])
def obtener_progreso_flashcards(subtema_id):
    usuario_id = request.args.get('usuario_id')
    
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Usuario no identificado'}), 401
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total FROM flashcards 
            WHERE subtema_id = %s AND estado = 'aprobada'
        """, (subtema_id,))
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as estudiadas FROM flashcards_estudio fe
            JOIN flashcards f ON fe.flashcard_id = f.id
            WHERE f.subtema_id = %s AND fe.usuario_id = %s
        """, (subtema_id, int(usuario_id)))
        estudiadas = cursor.fetchone()['estudiadas']
        
        cursor.execute("""
            SELECT COUNT(*) as sabe FROM flashcards_estudio fe
            JOIN flashcards f ON fe.flashcard_id = f.id
            WHERE f.subtema_id = %s AND fe.usuario_id = %s AND fe.la_sabe = TRUE
        """, (subtema_id, int(usuario_id)))
        sabe = cursor.fetchone()['sabe']
        
        porcentaje = round((estudiadas / total * 100), 1) if total > 0 else 0
        puede_hacer_examen = porcentaje >= 70
        
        return jsonify({
            'success': True,
            'total': total,
            'estudiadas': estudiadas,
            'sabe': sabe,
            'porcentaje': porcentaje,
            'puede_hacer_examen': puede_hacer_examen
        })
        
    except Exception as e:
        print(f"Error progreso: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener progreso'}), 500

@app.route('/api/examen/<int:subtema_id>', methods=['GET'])
def obtener_examen(subtema_id):
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión con base de datos'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM examenes WHERE subtema_id = %s", (subtema_id,))
        count = cursor.fetchone()['total']
        print(f"DEBUG: Encontradas {count} preguntas para subtema {subtema_id}")
        
        if count == 0:
            return jsonify({
                'success': True,
                'preguntas': [],
                'total': 0,
                'message': 'No hay preguntas para este subtema'
            })
        
        cursor.execute("""
            SELECT id, pregunta, tipo, opciones, correcta 
            FROM examenes 
            WHERE subtema_id = %s 
            ORDER BY RAND()
        """, (subtema_id,))
        preguntas = cursor.fetchall()
        
        for p in preguntas:
            if p['opciones']:
                try:
                    p['opciones'] = json.loads(p['opciones'])
                except json.JSONDecodeError as je:
                    print(f"ERROR parseando JSON en pregunta {p['id']}: {je}")
                    p['opciones'] = []
            else:
                p['opciones'] = None
        
        return jsonify({
            'success': True,
            'preguntas': preguntas,
            'total': len(preguntas)
        })
    except Exception as e:
        print(f"ERROR EXAMEN: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

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
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("""
            INSERT INTO resultados_examenes (usuario_id, subtema_id, aciertos, total, porcentaje)
            VALUES (%s, %s, %s, %s, %s)
        """, (int(usuario_id), subtema_id, aciertos, total, porcentaje))
        db.connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resultado guardado',
            'porcentaje': round(porcentaje, 2)
        })
    except Exception as e:
        print(f"Error guardar resultado: {e}")
        return jsonify({'success': False, 'message': 'Error al guardar'}), 500

@app.route('/api/examen/resultados/<int:subtema_id>', methods=['GET'])
def obtener_resultados(subtema_id):
    usuario_id = request.args.get('usuario_id')
    
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Usuario no identificado'}), 401
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        cursor.execute("""
            SELECT aciertos, total, porcentaje, fecha 
            FROM resultados_examenes 
            WHERE usuario_id = %s AND subtema_id = %s
            ORDER BY porcentaje DESC 
            LIMIT 1
        """, (int(usuario_id), subtema_id))
        resultado = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'tiene_resultado': resultado is not None,
            'resultado': resultado
        })
    except Exception as e:
        print(f"Error resultados: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener resultados'}), 500

@app.route('/api/progreso/<int:subtema_id>/marcar-leido', methods=['POST'])
def marcar_leido(subtema_id):
    data = request.get_json() or {}
    usuario_id = data.get('usuario_id')
    
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Usuario no identificado'}), 401
    
    db = get_db()
    if not db:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = db.get_cursor()
        
        cursor.execute(
            "SELECT id FROM progreso WHERE usuario_id = %s AND tema_id = %s",
            (int(usuario_id), subtema_id)
        )
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute(
                "UPDATE progreso SET leido = TRUE, ultimo_acceso = CURRENT_TIMESTAMP WHERE usuario_id = %s AND tema_id = %s",
                (int(usuario_id), subtema_id)
            )
        else:
            cursor.execute(
                "INSERT INTO progreso (usuario_id, tema_id, leido) VALUES (%s, %s, TRUE)",
                (int(usuario_id), subtema_id)
            )
        
        db.connection.commit()
        return jsonify({'success': True, 'message': 'Marcado como leído'})
        
    except Exception as e:
        print(f"Error progreso: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/progreso/general', methods=['GET'])
def progreso_general():
    return jsonify({'temas_leidos': 0, 'total_temas': 0, 'porcentaje': 0, 'detalle': []})

if __name__ == '__main__':
    app.run(debug=True, port=5000)