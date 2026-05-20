document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const subtemaId = urlParams.get('id');
    
    console.log('ID del subtema:', subtemaId);
    
    if (!subtemaId) {
        mostrarError('No se especifico ningun subtema');
        return;
    }
    
    await cargarContenido(subtemaId);
});

async function cargarContenido(subtemaId) {
    const body = document.getElementById('contenido-body');
    const titulo = document.getElementById('contenido-titulo');
    const tag = document.getElementById('tema-tag');
    const actions = document.getElementById('contenido-actions');
    const usuarioId = localStorage.getItem('usuario_id');
    
    try {
        let url = `/api/contenido/${subtemaId}`;
        if (usuarioId) {
            url += `?usuario_id=${usuarioId}`;
        }
        
        const res = await fetch(url);
        const data = await res.json();
        
        if (!data.success) {
            mostrarError(data.message || 'Error al cargar');
            return;
        }
        
        if (tag) tag.textContent = data.subtema.tema_nombre || data.subtema.tema || 'Tema';
        if (titulo) titulo.textContent = data.contenido.titulo || 'Sin titulo';
        
        if (body) body.innerHTML = data.contenido.contenido_html || '<p>Sin contenido</p>';
        
        if (data.leido) {
            if (actions) {
                actions.innerHTML = `
                    <div class="mensaje-completado">
                        <div class="completado-icon">✅</div>
                        <h3>Ya completaste este tema</h3>
                        <p>¿Quieres seguir practicando?</p>
                        <div class="completado-botones">
                            <a href="/flashcards.html?subtema=${subtemaId}" class="btn-flashcards">
                                🃏 Estudiar con Flashcards
                            </a>
                            <button onclick="window.location.reload()" class="btn-volver">
                                🔄 Volver a leer
                            </button>
                        </div>
                    </div>
                `;
            }
        } else if (usuarioId && actions) {
            actions.innerHTML = `
                <button class="btn-marcar" onclick="marcarLeido(${subtemaId})" id="btn-leido">
                    ✅ Marcar como leido
                </button>
            `;
        } else if (actions) {
            actions.innerHTML = `<p style="color: #9ca3af;">Inicia sesion para guardar tu progreso</p>`;
        }
        
    } catch (error) {
        console.error('Error completo:', error);
        mostrarError('Error de conexion con el servidor: ' + error.message);
    }
}

async function marcarLeido(subtemaId) {
    const usuarioId = localStorage.getItem('usuario_id');
    const btn = document.getElementById('btn-leido');
    
    if (!usuarioId) {
        alert('Debes iniciar sesion primero');
        return;
    }
    
    try {
        btn.disabled = true;
        btn.textContent = '⏳ Guardando...';
        
        const res = await fetch(`/api/progreso/${subtemaId}/marcar-leido`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({usuario_id: parseInt(usuarioId)})
        });
        
        const data = await res.json();
        
        if (data.success) {
            const actions = document.getElementById('contenido-actions');
            actions.innerHTML = `
                <div class="mensaje-completado">
                    <div class="completado-icon">🎉</div>
                    <h3>¡Tema completado!</h3>
                    <p>¿Quieres reforzar lo aprendido antes del examen?</p>
                    <div class="completado-botones">
                        <a href="/flashcards.html?subtema=${subtemaId}" class="btn-flashcards">
                            🃏 Estudiar con Flashcards
                        </a>
                        <button onclick="window.location.reload()" class="btn-volver">
                            🔄 Volver a leer
                        </button>
                    </div>
                </div>
            `;
        } else {
            btn.disabled = false;
            btn.textContent = '✅ Marcar como leido';
            alert('Error: ' + data.message);
        }
        
    } catch (error) {
        console.error('Error:', error);
        btn.disabled = false;
        btn.textContent = '✅ Marcar como leido';
        alert('Error de conexion');
    }
}

function mostrarError(mensaje) {
    const body = document.getElementById('contenido-body');
    if (body) {
        body.innerHTML = `
            <div style="text-align: center; padding: 60px; color: #dc2626;">
                <h2>😕 ${mensaje}</h2>
                <a href="/" style="color: #16a34a; margin-top: 20px; display: inline-block;">Volver al inicio</a>
            </div>
        `;
    }
}