// Estilos CSS (agregar al archivo CSS del proyecto o en un <style> en el HTML)
const styles = `
.tags-input-container {
    border: 1px solid #ced4da;
    padding: 5px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
}
.tag-item {
    background-color: #e9ecef;
    color: #212529;
    padding: 2px 4px;
    border-radius: 2px;
    display: flex;
    align-items: center;
}
.tag-item .close {
    margin-left: 5px;
    cursor: pointer;
}
.tags-input {
    flex-grow: 1;
    padding: 5px;
    border: none;
    outline: none;
}
#autores-suggestions {
    position: absolute;
    border: 1px solid #ced4da;
    border-top: none;
    border-radius: 0 0 5px 5px;
    max-height: 150px;
    overflow-y: auto;
    background-color: white;
    width: 100%;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.suggestion-item {
    padding: 5px 10px;
    cursor: pointer;
}
.suggestion-item:hover {
    background-color: #f8f9fa;
}
`;

document.addEventListener('DOMContentLoaded', function() {
    // Agregar estilos
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);

    const originalInput = document.getElementById('autores');
    const tagsContainer = document.createElement('div');
    tagsContainer.className = 'tags-input-container';
    originalInput.parentNode.insertBefore(tagsContainer, originalInput);
    originalInput.style.display = 'none';

    const inputElement = document.createElement('input');
    inputElement.type = 'text';
    inputElement.className = 'tags-input';
    inputElement.placeholder = 'Agregar autor...';

    const sugerenciasDiv = document.getElementById('autores-suggestions') || document.createElement('div');
    sugerenciasDiv.id = 'autores-suggestions';
    tagsContainer.parentNode.insertBefore(sugerenciasDiv, tagsContainer.nextSibling);

    tagsContainer.appendChild(inputElement);

    let tags = [];

    function addTag(text) {
        const tag = document.createElement('span');
        tag.className = 'tag-item';
        tag.textContent = text;
        const closeBtn = document.createElement('span');
        closeBtn.className = 'close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = function() {
            tagsContainer.removeChild(tag);
            tags = tags.filter(t => t !== text);
            updateOriginalInput();
        };
        tag.appendChild(closeBtn);
        tagsContainer.insertBefore(tag, inputElement);
        tags.push(text);
        updateOriginalInput();
    }

    function updateOriginalInput() {
        originalInput.value = tags.join(', ');
    }

    inputElement.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && this.value) {
            e.preventDefault();
            addTag(this.value.trim());
            this.value = '';
            sugerenciasDiv.innerHTML = '';
        }
    });

    inputElement.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length < 2) {
            sugerenciasDiv.innerHTML = '';
            return;
        }

        fetch(`/biblioteca/buscar_autores/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                sugerenciasDiv.innerHTML = '';
                data.forEach(autor => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    div.textContent = autor.nombre;
                    div.addEventListener('click', function() {
                        addTag(autor.nombre);
                        inputElement.value = '';
                        sugerenciasDiv.innerHTML = '';
                    });
                    sugerenciasDiv.appendChild(div);
                });
            });
    });

    // Cerrar las sugerencias si se hace clic fuera del input
    document.addEventListener('click', function(e) {
        if (e.target !== inputElement && e.target !== sugerenciasDiv) {
            sugerenciasDiv.innerHTML = '';
        }
    });

    // Manejar el pegado de texto en el input
    inputElement.addEventListener('paste', function(e) {
        e.preventDefault();
        const pastedText = (e.clipboardData || window.clipboardData).getData('text');
        const autores = pastedText.split(',').map(autor => autor.trim());
        autores.forEach(autor => {
            if (autor && !tags.includes(autor)) {
                addTag(autor);
            }
        });
    });

    // Nuevo código agregado
    $(document).ready(function() {
        // Manejar la adición de un nuevo código Dewey
        $('#guardar-codigo-dewey').click(function() {
            let codigoDewey = $('#codigo_dewey_nuevo').val();
            let descripcionDewey = $('#descripcion_dewey_nueva').val();
            
            if (codigoDewey && descripcionDewey) {
                $.ajax({
                    url: '/biblioteca/agregar_codigo_dewey/',
                    type: 'POST',
                    data: {
                        'codigo': codigoDewey,
                        'descripcion': descripcionDewey,
                        'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                    },
                    success: function(response) {
                        if (response.success) {
                            let newOption = new Option(codigoDewey + ' - ' + descripcionDewey, response.id);
                            $('#codigo_dewey').append(newOption);
                            $('#codigo_dewey').val(response.id);
                            $('#nuevoCodigoDewey').modal('hide');
                            
                            // Limpiar el formulario
                            $('#codigo_dewey_nuevo').val('');
                            $('#descripcion_dewey_nueva').val('');
                            
                            alert('Código Dewey agregado con éxito.');
                        } else {
                            alert('Error al agregar el código Dewey: ' + response.error);
                        }
                    },
                    error: function() {
                        alert('Error al procesar la solicitud.');
                    }
                });
            } else {
                alert('Por favor, complete todos los campos.');
            }
        });

        // ... (código anterior sin cambios)

$('#btn-recomendacion').click(function() {
    console.log('hola');
    var titulo = $('#titulo').val();
    console.log($('#titulo').val());

    console.log($('#autores').val());
    var autores = $('#autores').val();

    if (!titulo || !autores) {
        alert("Por favor, ingrese el título y los autores antes de obtener recomendaciones.");
        return;
    }

    $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cargando...');

    $.ajax({
        url: '/biblioteca/openai_recommendation/',
        type: 'POST',
        data: {
            'title': titulo,
            'authors': autores,
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response && response.age_recommended && response.dewey_code && response.description) {
                $('#recomendacion-edad').text(response.age_recommended);
                $('#recomendacion-dewey').text(response.dewey_code);
                $('#resumen').val(response.description);
                
                var recomendacionesTexto = '<strong>Edad recomendada:</strong> ' + response.age_recommended + '<br>';
                recomendacionesTexto += '<strong>Código Dewey sugerido:</strong> ' + response.dewey_code;
                $('#recomendaciones-texto').html(recomendacionesTexto);
                $('#recomendaciones-alert').slideDown();

                // Seleccionar automáticamente el rango de edad
                var edadRecomendada = response.age_recommended.split(' ')[0]; // Asumiendo que viene en formato "X-Y años"
                $('#edad_recomendada').val(edadRecomendada);

                // Buscar y seleccionar el código Dewey
                var deweyCode = response.dewey_code.split(' ')[0]; // Asumiendo que viene en formato "XXX.XX - Descripción"
                var deweySelect = $('#codigo_dewey');
                var deweyOption = deweySelect.find('option').filter(function() {
                    return $(this).text().startsWith(deweyCode);
                });

                if (deweyOption.length) {
                    deweySelect.val(deweyOption.val());
                } else {
                    // Si no se encuentra el código exacto, buscar la parte entera
                    var deweyEntero = Math.floor(parseFloat(deweyCode)).toString();
                    var deweyOptionEntero = deweySelect.find('option').filter(function() {
                        return $(this).text().startsWith(deweyEntero);
                    });

                    if (deweyOptionEntero.length) {
                        deweySelect.val(deweyOptionEntero.val());
                    }
                    // Si no se encuentra la parte entera, no se hace nada más
                }
            } else {
                console.error("Respuesta incompleta del servidor:", response);
                alert("La respuesta del servidor no contiene toda la información necesaria. Por favor, intente de nuevo.");
            }
        },
        error: function(xhr, status, error) {
            console.error("Error en la solicitud:", error);
        },
        complete: function() {
            $('#btn-recomendacion').prop('disabled', false).html('Obtener Recomendaciones');
        }
    });
});

// ... (resto del código sin cambios)
    
        $('#tipo').change(function() {
            $('.campos-especificos').hide();
            $('#campos-' + $(this).val()).show();
        });

        $('#guardar-editorial').click(function() {
            var nombreEditorial = $('#nueva-editorial-nombre').val();
            if (!nombreEditorial) {
                alert("Por favor, ingrese el nombre de la editorial.");
                return;
            }
    
            $.ajax({
                url: '/biblioteca/agregar-editorial/',
                type: 'POST',
                data: {
                    'nombre': nombreEditorial,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        // Agregar la nueva editorial al select
                        $('#editorial').append($('<option>', {
                            value: response.id,
                            text: response.nombre
                        }));
                        
                        // Seleccionar la nueva editorial
                        $('#editorial').val(response.id);
                        
                        // Cerrar el modal
                        $('#nuevaEditorialModal').modal('hide');
                        
                        // Limpiar el campo del modal
                        $('#nueva-editorial-nombre').val('');
                        
                        // Mostrar un mensaje de éxito
                        alert("Editorial agregada con éxito.");
                        
                        // Actualizar la lista completa de editoriales (opcional)
                        actualizarListaEditoriales();
                    } else {
                        alert("Error al agregar la editorial: " + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error en la solicitud:", error);
                    alert("Hubo un error al agregar la editorial. Por favor, intente de nuevo.");
                }
            });
        });
    
        function actualizarListaEditoriales() {
            $.ajax({
                url: 'biblioteca/obtener_editoriales/',
                type: 'GET',
                success: function(response) {
                    if (response.success) {
                        var select = $('#editorial');
                        select.empty();
                        select.append($('<option>', {
                            value: "",
                            text: "Seleccione una editorial"
                        }));
                        $.each(response.editoriales, function(index, editorial) {
                            select.append($('<option>', {
                                value: editorial.id,
                                text: editorial.nombre
                            }));
                        });
                    } else {
                        console.error("Error al obtener la lista de editoriales:", response.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error en la solicitud de editoriales:", error);
                }
            });
        }


        

    });
});