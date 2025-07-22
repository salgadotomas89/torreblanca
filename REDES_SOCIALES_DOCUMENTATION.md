# Configuración de Redes Sociales

## Descripción
Esta funcionalidad permite a los administradores del sitio web configurar las URLs de las redes sociales del colegio, las cuales aparecerán automáticamente en diferentes secciones del sitio web como el footer y la página de noticias.

## Características

### ✅ Redes Sociales Soportadas
- **Facebook**: Para la página oficial del colegio
- **Twitter/X**: Para la cuenta oficial del colegio  
- **Instagram**: Para la cuenta de Instagram del colegio
- **YouTube**: Para el canal de YouTube del colegio

### ✅ Ubicaciones donde aparecen
- **Footer principal**: En todas las páginas del sitio
- **Página de noticias**: En la sección sidebar "Síguenos"
- **Cualquier template que use el componente**: Reutilizable en toda la aplicación

## Cómo usar

### Acceder a la configuración
1. Iniciar sesión como administrador
2. Navegar a `/configuracion/redes-sociales` o acceder a través del menú de configuración
3. La página mostrará un formulario intuitivo con 4 tarjetas, una para cada red social

### Configurar las URLs
1. **Formato requerido**: Todas las URLs deben comenzar con `http://` o `https://`
2. **Ejemplos válidos**:
   - Facebook: `https://facebook.com/mi-colegio`
   - Twitter: `https://twitter.com/mi_colegio`
   - Instagram: `https://instagram.com/mi_colegio`
   - YouTube: `https://youtube.com/channel/UCxxxxxxxxxxxxx`

### Características del formulario
- **Validación en tiempo real**: Las URLs se validan automáticamente
- **Vista previa**: Botón para previsualizar cómo aparecerán en el sitio
- **Enlaces de prueba**: Si ya hay una URL configurada, aparece un botón "Vista previa" para verificar que funciona
- **Campos opcionales**: Todas las redes sociales son opcionales

## Funcionalidades técnicas

### Modelo de datos
Los campos se agregaron al modelo `AppearanceSettings`:
```python
facebook_url = models.URLField(max_length=200, blank=True, null=True)
twitter_url = models.URLField(max_length=200, blank=True, null=True)
instagram_url = models.URLField(max_length=200, blank=True, null=True)
youtube_url = models.URLField(max_length=200, blank=True, null=True)
```

### Context Processor
Se creó un context processor que hace disponibles las URLs en todos los templates:
```python
def redes_sociales_processor(request):
    # Retorna las URLs de redes sociales para uso global
```

### Componente reutilizable
Se creó un template componente en `components/redes_sociales.html` con tres estilos diferentes:
- **`style='buttons'`**: Botones coloridos (usado en footer)
- **`style='links'`**: Enlaces simples (usado en sidebar)
- **`style='icons'`**: Solo iconos circulares (para uso futuro)

### Uso del componente
```django
<!-- En el footer -->
{% include 'components/redes_sociales.html' with style='buttons' size='sm' %}

<!-- En sidebar -->
{% include 'components/redes_sociales.html' with style='links' %}

<!-- Solo iconos -->
{% include 'components/redes_sociales.html' with style='icons' %}
```

## Comportamiento dinámico

### Cuando NO hay redes sociales configuradas
- Se muestra un mensaje apropiado dependiendo del usuario:
  - **Usuarios autenticados**: "Configurar redes sociales" (enlace a configuración)
  - **Usuarios no autenticados**: "Próximamente en redes sociales"

### Cuando SÍ hay redes sociales configuradas
- Solo aparecen las redes sociales que tienen URLs configuradas
- Los enlaces se abren en nuevas pestañas (`target="_blank"`)
- Cada enlace tiene tooltips descriptivos

## Archivos modificados

### Modelos
- `colegio/models.py`: Agregados campos de redes sociales a `AppearanceSettings`

### Vistas
- `colegio/views.py`: Nueva vista `configuracion_redes_sociales`

### Templates
- `colegio/templates/config/redes_sociales.html`: Página de configuración
- `colegio/templates/components/redes_sociales.html`: Componente reutilizable
- `colegio/templates/inicio/layout_updated.html`: Footer actualizado
- `noticias/templates/noticias.html`: Sidebar actualizado

### URLs
- `colegio/urls.py`: Nueva URL `configuracion/redes-sociales`

### Configuración
- `miproyecto/settings.py`: Agregado nuevo context processor
- `colegio/context_processors.py`: Nuevo context processor para redes sociales

### Formularios
- `colegio/forms.py`: Agregados campos de redes sociales a `AppearanceSettingsForm`

## Migración de base de datos
```bash
python manage.py makemigrations colegio
python manage.py migrate
```

## Posibles mejoras futuras
1. **Métricas de clics**: Rastrear qué redes sociales son más utilizadas
2. **Más redes sociales**: LinkedIn, TikTok, WhatsApp Business
3. **Widgets integrados**: Mostrar feeds de Instagram o Twitter
4. **Validación avanzada**: Verificar que las URLs realmente existen
5. **Compartir contenido**: Botones para compartir noticias específicas

## Soporte técnico
- Requiere Django 3.0+
- Compatible con Bootstrap 5
- Usa Font Awesome para iconos de redes sociales
- Requiere autenticación para configurar

---

**Desarrollado como parte del sistema de gestión escolar**
**Última actualización**: Julio 2025
