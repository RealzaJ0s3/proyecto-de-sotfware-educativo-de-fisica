// Obtener parámetros de URL
const urlParams = new URLSearchParams(window.location.search);
const subtemaId = urlParams.get('subtema');

let flashcards = [];
let indiceActual = 0;
let progreso = { estudiadas: 0, sabe: 0, total: 0 };
let usuarioId = localStorage.getItem('usuario_id');

document.addEventListener('DOMContentLoaded', async () => {
    if (!subtemaId) {
        mostrarError('No se especificó ningún subtema');
        return;
    }
    
    await cargarFlashcards();
    await cargarProgreso();
});

async function cargarFlashcards() {
    try {
        const res = await fetch(`/api/flashcards/${subtemaId}`);
        const data = await res.json();
        
        if (!data.success) {
            mostrarError(data.message);
            return;
        }
        
        flashcards = data.flashcards;
        
        if (flashcards.length === 0) {
            document.querySelector('.tarjeta-wrapper').innerHTML = `
                <div style="text-align: center; padding: 60px; color: white;">
                    <h2>📭 No hay flashcards</h2>
                    <p style="margin: 16px 0;">Sé el primero en crear una</p>
                </div>
            `;
            document.getElementById('evaluacion-botones').style.display = 'none';
            document.querySelector('.navegacion-botones').style.display = 'none';
            return;
        }
        
        mostrarFlashcard(0);
        
    } catch (error) {
        console.error('Error:', error);
        mostrarError('Error al cargar flashcards');
    }
}

async function cargarProgreso() {
    if (!usuarioId) return;
    
    try {
        const res = await fetch(`/api/flashcards/progreso/${subtemaId}?usuario_id=${usuarioId}`);
        const data = await res.json();
        
        if (data.success) {
            progreso = data;
            actualizarBarraProgreso();
        }
    } catch (error) {
        console.error('Error progreso:', error);
    }
}

function actualizarBarraProgreso() {
    const fill = document.getElementById('progreso-fill');
    const texto = document.getElementById('progreso-texto');
    
    fill.style.width = `${progreso.porcentaje}%`;
    texto.textContent = `${progreso.porcentaje}% completado (${progreso.estudiadas}/${progreso.total})`;
    
    document.getElementById('nav-info').innerHTML = `
        <span class="progreso-tag">✅ ${progreso.sabe} sabidas · 📖 ${progreso.estudiadas} estudiadas</span>
    `;
}

function mostrarFlashcard(indice) {
    if (indice < 0 || indice >= flashcards.length) return;
    
    indiceActual = indice;
    const f = flashcards[indice];
    
    // Resetear tarjeta
    document.getElementById('tarjeta').classList.remove('girada');
    
    // Actualizar contenido
    document.getElementById('tarjeta-numero').textContent = `${indice + 1} / ${flashcards.length}`;
    document.getElementById('tarjeta-pregunta').textContent = f.pregunta;
    document.getElementById('tarjeta-respuesta').textContent = f.respuesta;
    
    // Botones de navegación
    document.getElementById('btn-anterior').disabled = indice === 0;
    document.getElementById('btn-siguiente').disabled = indice === flashcards.length - 1;
}

function girarTarjeta() {
    document.getElementById('tarjeta').classList.toggle('girada');
}

function anteriorFlashcard() {
    if (indiceActual > 0) {
        mostrarFlashcard(indiceActual - 1);
    }
}

function siguienteFlashcard() {
    if (indiceActual < flashcards.length - 1) {
        mostrarFlashcard(indiceActual + 1);
    }
}

async function evaluarFlashcard(laSabe) {
    if (!usuarioId) {
        alert('Debes iniciar sesión para guardar tu progreso');
        return;
    }
    
    const flashcardId = flashcards[indiceActual].id;
    
    try {
        const res = await fetch('/api/flashcards/estudiar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                usuario_id: parseInt(usuarioId),
                flashcard_id: flashcardId,
                la_sabe: laSabe
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            // Animación de feedback
            const btn = laSabe ? document.querySelector('.btn-sabe') : document.querySelector('.btn-repasar');
            btn.style.transform = 'scale(1.1)';
            setTimeout(() => btn.style.transform = '', 200);
            
            // Cargar siguiente o mostrar completado
            await cargarProgreso();
            
            if (indiceActual < flashcards.length - 1) {
                setTimeout(() => siguienteFlashcard(), 300);
            } else {
                mostrarCompletado();
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

function mostrarCompletado() {
    const modal = document.getElementById('modal-completado');
    const stats = document.getElementById('modal-stats');
    const btnExamen = document.getElementById('btn-examen');
    
    stats.innerHTML = `
        <p>📚 Total de flashcards: ${progreso.total}</p>
        <p>✅ Que sabes: ${progreso.sabe}</p>
        <p>📖 Estudiadas: ${progreso.estudiadas}</p>
        <p>📊 Dominio: ${Math.round((progreso.sabe / progreso.total) * 100)}%</p>
    `;
    
    // Solo mostrar botón de examen si tiene 70% o más
    if (progreso.porcentaje >= 70) {
        btnExamen.style.display = 'inline-block';
    } else {
        btnExamen.style.display = 'none';
        stats.innerHTML += `<p style="color: #dc2626; margin-top: 12px;">Necesitas estudiar más para hacer el examen (mínimo 70%)</p>`;
    }
    
    modal.classList.remove('hidden');
}

function cerrarModal() {
    document.getElementById('modal-completado').classList.add('hidden');
    // Volver a la primera flashcard para seguir estudiando
    mostrarFlashcard(0);
}

function irAExamen() {
    window.location.href = `/examen.html?subtema=${subtemaId}`;
}

// ========== CREAR FLASHCARD ==========

function mostrarFormularioCrear() {
    if (!usuarioId) {
        alert('Debes iniciar sesión para crear flashcards');
        return;
    }
    document.getElementById('formulario-crear').classList.remove('hidden');
}

function ocultarFormularioCrear() {
    document.getElementById('formulario-crear').classList.add('hidden');
    document.getElementById('nueva-pregunta').value = '';
    document.getElementById('nueva-respuesta').value = '';
    document.getElementById('mensaje-validacion').textContent = '';
}

async function crearFlashcard() {
    const pregunta = document.getElementById('nueva-pregunta').value.trim();
    const respuesta = document.getElementById('nueva-respuesta').value.trim();
    const mensajeDiv = document.getElementById('mensaje-validacion');
    
    if (!pregunta || !respuesta) {
        mensajeDiv.textContent = 'Escribe la pregunta y la respuesta';
        return;
    }
    
    try {
        const res = await fetch('/api/flashcards/crear', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                subtema_id: parseInt(subtemaId),
                pregunta: pregunta,
                respuesta: respuesta,
                usuario_id: parseInt(usuarioId)
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            alert(data.message);
            ocultarFormularioCrear();
            await cargarFlashcards(); // Recargar
        } else {
            mensajeDiv.textContent = data.message;
        }
        
    } catch (error) {
        console.error('Error:', error);
        mensajeDiv.textContent = 'Error de conexión';
    }
}

function mostrarError(mensaje) {
    document.querySelector('.flashcards-container').innerHTML = `
        <div style="text-align: center; padding: 100px 20px; color: white;">
            <h2>😕 ${mensaje}</h2>
            <a href="/" style="color: #86efac; margin-top: 20px; display: inline-block;">Volver al inicio</a>
        </div>
    `;
}