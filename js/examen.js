(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const subtemaId = urlParams.get('subtema');
    const usuarioId = localStorage.getItem('usuario_id');
    const usuarioNombre = localStorage.getItem('usuario_nombre') || 'Estudiante';

    let preguntas = [];
    let respuestas = [];
    let indiceActual = 0;
    let datosExamen = { aciertos: 0, total: 0, nombreTema: '' };

    const examenPanel = document.getElementById('examenPanel');
    const menuDiv = document.getElementById('menuPreguntas');
    const zonaPregunta = document.getElementById('zonaPregunta');
    const modalResultados = document.getElementById('modalResultados');

    document.addEventListener('DOMContentLoaded', async () => {
        console.log('Subtema ID:', subtemaId);
        console.log('Usuario ID:', usuarioId);
        
        if (!subtemaId) {
            mostrarError('No se especificó ningún subtema');
            return;
        }
        
        if (!usuarioId) {
            mostrarError('Debes iniciar sesión para realizar el examen');
            return;
        }
        
        await cargarExamen();
    });

    async function cargarExamen() {
        try {
            console.log('Cargando examen para subtema:', subtemaId);
            
            const res = await fetch(`/api/examen/${subtemaId}`);
            console.log('Status respuesta:', res.status);
            
            const data = await res.json();
            console.log('Datos recibidos:', data);
            
            if (!data.success) {
                mostrarError(data.message || 'Error al cargar el examen: ' + JSON.stringify(data));
                return;
            }
            
            preguntas = data.preguntas;
            respuestas = new Array(preguntas.length).fill(null);
            datosExamen.total = preguntas.length;
            
            if (preguntas.length === 0) {
                mostrarError('No hay preguntas disponibles para este examen');
                return;
            }
            
            try {
                const resSubtema = await fetch(`/api/contenido/${subtemaId}`);
                const dataSubtema = await resSubtema.json();
                console.log('Datos subtema:', dataSubtema);
                
                if (dataSubtema.success) {
                    datosExamen.nombreTema = dataSubtema.subtema.subtema;
                    document.getElementById('examen-titulo').textContent = 
                        `Evaluación · ${dataSubtema.subtema.tema_nombre || 'Física'} · ${datosExamen.nombreTema}`;
                }
            } catch (e) {
                console.error('Error cargando subtema:', e);
                document.getElementById('examen-titulo').textContent = 'Evaluación de Física';
            }
            
            examenPanel.style.display = 'block';
            renderMenu();
            renderPregunta(0);
            
        } catch (error) {
            console.error('Error completo:', error);
            mostrarError('Error de conexión: ' + error.message);
        }
    }

    function renderMenu() {
        let html = '';
        for (let i = 0; i < preguntas.length; i++) {
            let clase = 'btn-pregunta';
            if (respuestas[i] !== null) clase += ' respondida';
            if (i === indiceActual) clase += ' actual';
            html += `<button class="${clase}" data-index="${i}">${i+1}</button>`;
        }
        menuDiv.innerHTML = html;
        
        document.querySelectorAll('.btn-pregunta').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.target.dataset.index);
                if (!isNaN(idx)) { 
                    indiceActual = idx; 
                    renderMenu(); 
                    renderPregunta(indiceActual); 
                }
            });
        });
    }

    function renderPregunta(idx) {
        indiceActual = idx;
        const p = preguntas[idx];
        
        const contenedor = document.getElementById('zonaPregunta');
        
        if (!contenedor) {
            console.error('No se encontró zonaPregunta');
            return;
        }
        
        let opcionesHtml = '';
        
        if (p.tipo === 'vf') {
            opcionesHtml = `
                <div class="opcion-item" onclick="seleccionarRespuesta('Verdadero')">
                    <input type="radio" name="resp" value="Verdadero" id="vf_true" ${respuestas[idx]==='Verdadero'?'checked':''}> 
                    <label for="vf_true">Verdadero</label>
                </div>
                <div class="opcion-item" onclick="seleccionarRespuesta('Falso')">
                    <input type="radio" name="resp" value="Falso" id="vf_false" ${respuestas[idx]==='Falso'?'checked':''}> 
                    <label for="vf_false">Falso</label>
                </div>
            `;
        } else if (p.tipo === 'mult') {
            opcionesHtml = p.opciones.map((op, i) => `
                <div class="opcion-item" onclick="seleccionarRespuesta('${op.replace(/'/g, "\\'")}')">
                    <input type="radio" name="resp" value="${op}" id="mult_${i}" ${respuestas[idx]===op?'checked':''}> 
                    <label for="mult_${i}">${op}</label>
                </div>
            `).join('');
        } else if (p.tipo === 'codigo') {
            opcionesHtml = `
                <div class="opcion-item" onclick="seleccionarRespuesta('Bien')">
                    <input type="radio" name="resp" value="Bien" id="cod_bien" ${respuestas[idx]==='Bien'?'checked':''}> 
                    <label for="cod_bien">Bien (correcto)</label>
                </div>
                <div class="opcion-item" onclick="seleccionarRespuesta('Mal')">
                    <input type="radio" name="resp" value="Mal" id="cod_mal" ${respuestas[idx]==='Mal'?'checked':''}> 
                    <label for="cod_mal">Mal (contiene error)</label>
                </div>
            `;
        }

        const esPrimera = idx === 0;
        const esUltima = idx === preguntas.length - 1;
        
        contenedor.innerHTML = `
            <div class="pregunta-contenedor">
                <div class="numero-pregunta">Pregunta ${idx + 1} de ${preguntas.length}</div>
                <div class="pregunta-texto">${p.pregunta}</div>
                <div class="opciones-area">
                    ${opcionesHtml}
                </div>
                <div class="navegacion-examen">
                    <button class="btn-nav-examen btn-anterior" onclick="anteriorPregunta()" ${esPrimera ? 'disabled' : ''}>
                        ◀ Anterior
                    </button>
                    ${esUltima ? 
                        `<button class="btn-nav-examen btn-finalizar" onclick="finalizarExamen()">📄 Finalizar</button>` :
                        `<button class="btn-nav-examen btn-siguiente" onclick="siguientePregunta()">Siguiente ▶</button>`
                    }
                </div>
            </div>
        `;
        
        renderMenu();
    }

    window.seleccionarRespuesta = function(valor) {
        respuestas[indiceActual] = valor;
        renderPregunta(indiceActual);
    };

    window.anteriorPregunta = function() {
        if (indiceActual > 0) {
            renderPregunta(indiceActual - 1);
        }
    };

    window.siguientePregunta = function() {
        if (indiceActual < preguntas.length - 1) {
            renderPregunta(indiceActual + 1);
        }
    };

    window.finalizarExamen = async function() {
        const sinResponder = respuestas.findIndex(r => r === null);
        if (sinResponder !== -1) {
            alert(`Falta responder la pregunta ${sinResponder + 1}`);
            renderPregunta(sinResponder);
            return;
        }

        let aciertos = 0;
        for (let i = 0; i < preguntas.length; i++) {
            if (respuestas[i] === preguntas[i].correcta) {
                aciertos++;
            }
        }

        datosExamen.aciertos = aciertos;
        const porcentaje = (aciertos / preguntas.length) * 100;
        const aprobado = porcentaje >= 70;

        try {
            const res = await fetch('/api/examen/guardar-resultado', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    usuario_id: parseInt(usuarioId),
                    subtema_id: parseInt(subtemaId),
                    aciertos: aciertos,
                    total: preguntas.length
                })
            });
            const data = await res.json();
            console.log('Resultado guardado:', data);
        } catch (e) {
            console.error('Error guardando:', e);
        }

        mostrarResultados(aciertos, porcentaje, aprobado);
    };

    function mostrarResultados(aciertos, porcentaje, aprobado) {
        document.getElementById('titulo-resultado').textContent = aprobado ? '🎉 ¡Aprobado!' : '😕 No aprobado';
        
        const statsDiv = document.getElementById('stats-resultado');
        statsDiv.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Correctas:</span>
                <span class="stat-value ${aprobado ? 'aprobado' : 'reprobado'}">${aciertos}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total:</span>
                <span class="stat-value">${preguntas.length}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Porcentaje:</span>
                <span class="stat-value ${aprobado ? 'aprobado' : 'reprobado'}">${porcentaje.toFixed(1)}%</span>
            </div>
            <div class="resultado-mensaje ${aprobado ? 'aprobado' : 'reprobado'}">
                ${aprobado ? '¡Excelente! Dominas este tema. Puedes continuar con el siguiente.' : 'Necesitas más práctica. Te recomendamos repasar las flashcards y volver a intentarlo.'}
            </div>
        `;
        
        modalResultados.classList.remove('hidden');
    }

    window.descargarPDF = function() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        doc.setFontSize(18);
        doc.text('Resultado de Evaluación - Física CBIT', 20, 20);
        doc.setFontSize(12);
        doc.text(`Estudiante: ${usuarioNombre}`, 20, 35);
        doc.text(`Tema: ${datosExamen.nombreTema || 'Física'}`, 20, 42);
        doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 20, 49);

        let aciertos = datosExamen.aciertos;
        const bodyTabla = [];
        for (let i = 0; i < preguntas.length; i++) {
            const p = preguntas[i];
            const estResp = respuestas[i] || '';
            let preguntaCorta = p.pregunta.length > 40 ? p.pregunta.substring(0,40)+'…' : p.pregunta;
            bodyTabla.push([(i+1).toString(), preguntaCorta, estResp, p.correcta]);
        }

        doc.autoTable({
            head: [['#', 'Pregunta', 'Resp. estudiante', 'Correcta']],
            body: bodyTabla,
            startY: 60,
            styles: { fontSize: 8, cellPadding: 2 },
            columnStyles: {
                0: { cellWidth: 10 },
                1: { cellWidth: 70 },
                2: { cellWidth: 35 },
                3: { cellWidth: 35 }
            }
        });

        const finalY = doc.lastAutoTable.finalY + 15;
        doc.setFontSize(26);
        doc.setTextColor(aciertos >= preguntas.length * 0.7 ? 22 : 220, aciertos >= preguntas.length * 0.7 ? 163 : 38, aciertos >= preguntas.length * 0.7 ? 74 : 38);
        doc.text(`Calificación: ${aciertos} / ${preguntas.length}`, 20, finalY);

        const fileName = `evaluacion_fisica_${subtemaId}_${Date.now()}.pdf`;
        doc.save(fileName);
    };

    function mostrarError(mensaje) {
        document.body.innerHTML = `
            <div style="text-align: center; padding: 100px 20px; color: white; background: #064e3b; min-height: 100vh;">
                <h2> ${mensaje}</h2>
                <a href="/login.html" style="color: #86efac; margin-top: 20px; display: inline-block;">Iniciar sesión</a>
                <br>
                <a href="/" style="color: #86efac; margin-top: 10px; display: inline-block;">← Volver al inicio</a>
            </div>
        `;
    }
})();