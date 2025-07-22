# Sistema de Color Principal - Documentación

## 📋 Resumen General

El sistema de color principal permite personalizar los colores de la interfaz desde la configuración de apariencia, aplicando automáticamente el color elegido a diferentes elementos del sitio web.

## 🏗️ Arquitectura del Sistema

### 1. **Base de Datos** (`colegio/models.py`)

```python
class AppearanceSettings(models.Model):
    # Color principal del sitio
    color_principal_texto = models.CharField(max_length=7, default="#000000")
    
    # Opción para activar/desactivar el uso del color principal en botones
    usar_color_principal = models.BooleanField(default=True, help_text="Activar para que los botones primary usen el color principal del sitio")
    
    # Otros campos de colores...
```

### 2. **Formulario** (`colegio/forms.py`)

```python
class AppearanceSettingsForm(forms.ModelForm):
    color_principal_texto = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))
    usar_color_principal = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        fields = [
            # ... otros campos
            'color_principal_texto',
            'usar_color_principal',
            # ...
        ]
```

### 3. **Variables CSS Globales** (`colegio/templates/common_styles.html`)

```css
:root {
    --color_principal_texto: {{ apariencia.color_principal_texto }};
    /* Otras variables... */
}
```

## 🎨 Clases CSS Disponibles

### **Clases Personalizadas (siempre disponibles)**

```css
/* Texto con color principal */
.text-primary-custom { color: var(--color_principal_texto) !important; }

/* Fondo con color principal */
.bg-primary-custom { background-color: var(--color_principal_texto) !important; }

/* Botones con color principal */
.btn-primary-custom { 
    background-color: var(--color_principal_texto) !important;
    border-color: var(--color_principal_texto) !important;
    color: #ffffff !important;
}

/* Botones outline con color principal */
.btn-outline-primary-custom {
    color: var(--color_principal_texto) !important;
    border-color: var(--color_principal_texto) !important;
}

/* Enlaces con color principal */
.link-primary-custom { color: var(--color_principal_texto) !important; }

/* Badges con color principal */
.badge-primary-custom { background-color: var(--color_principal_texto) !important; }

/* Headers de cards con color principal */
.card-header-primary-custom { background-color: var(--color_principal_texto) !important; }
```

### **Sobrescritura Automática de Bootstrap (condicional)**

Cuando `usar_color_principal = True`:

```css
.btn-primary {
    background-color: var(--color_principal_texto) !important;
    border-color: var(--color_principal_texto) !important;
}

.btn-outline-primary {
    color: var(--color_principal_texto) !important;
    border-color: var(--color_principal_texto) !important;
}
```

## 🔧 Configuración en Secciones Específicas

### **Eventos** (`static/css/home/secciones/nueva-eventos-carrousel.css`)

```css
/* Fecha del evento - siempre usa color principal */
.card-carousel .event-day {
    color: var(--color_principal_texto) !important;
}

/* Hover en títulos - siempre usa color principal */
.card-carousel:hover h5 {
    color: var(--color_principal_texto) !important;
}
```

### **Otros elementos que usan color principal**

- **Event cards**: Background y texto configurables por separado
- **Menú principal**: Background y texto configurables por separado
- **Mega menú**: Se sincroniza automáticamente con el menú principal

## 🎛️ Control del Usuario

### **Página de Configuración** (`/config/apariencia/`)

1. **Color Principal del Sitio**: Selector de color para elegir el color principal
2. **Checkbox "Aplicar color principal a todos los botones primary"**: 
   - ✅ **Activado**: Todos los `.btn-primary` usan el color principal
   - ❌ **Desactivado**: Los `.btn-primary` mantienen el azul Bootstrap

### **Sincronización Automática**

Cuando el usuario cambia el color del menú principal:
- El mega menú se actualiza automáticamente con los mismos colores
- Las vistas previas se actualizan en tiempo real
- Los campos del formulario se sincronizan via JavaScript

## 📝 Flujo de Aplicación

### **1. Usuario configura color**
```
Usuario elige color → Formulario → Base de datos → Variables CSS → Elementos visuales
```

### **2. Renderizado en templates**
```django
<!-- En common_styles.html -->
:root {
    --color_principal_texto: {{ apariencia.color_principal_texto }};
}

<!-- En cualquier template -->
<button class="btn btn-primary-custom">Usar color principal</button>
<h1 class="text-primary-custom">Título con color principal</h1>
```

### **3. JavaScript para sincronización** (`config/apariencia.html`)
```javascript
// Sincronizar mega menú con menú principal
function syncMegaMenuColors() {
    const menuBg = document.querySelector('[name="menu_background_color"]').value;
    const menuText = document.querySelector('[name="menu_text_color"]').value;
    
    document.querySelector('[name="mega_menu_background_color"]').value = menuBg;
    document.querySelector('[name="mega_menu_text_color"]').value = menuText;
}
```

## 🚀 Cómo Agregar Color Principal a Nuevos Elementos

### **Método 1: Usar clases existentes**
```html
<div class="bg-primary-custom text-white">Contenido</div>
<button class="btn btn-primary-custom">Botón</button>
```

### **Método 2: CSS personalizado**
```css
.mi-elemento-custom {
    color: var(--color_principal_texto) !important;
    border-color: var(--color_principal_texto) !important;
}
```

### **Método 3: CSS condicional (solo cuando está habilitado)**
```css
{% if apariencia.usar_color_principal %}
.mi-boton {
    background-color: var(--color_principal_texto) !important;
}
{% endif %}
```

## 📋 Elementos Actualmente Afectados

### **Automático (cuando usar_color_principal = True)**
- Todos los botones `.btn-primary` del sitio
- Todos los botones `.btn-outline-primary` del sitio

### **Siempre activo**
- Números de fecha en eventos (`.event-day`)
- Hover en títulos de eventos (`.card-carousel:hover h5`)
- Elementos con clases `-custom`

### **Configurable por separado**
- Fondo de tarjetas de eventos
- Texto de tarjetas de eventos
- Fondo del menú principal
- Texto del menú principal
- Fondo del mega menú (sincronizado)
- Texto del mega menú (sincronizado)

## 🔄 Mantenimiento

### **Al agregar nuevas funcionalidades:**

1. **Para elementos que SIEMPRE deben usar el color principal:**
   ```css
   .nuevo-elemento { color: var(--color_principal_texto) !important; }
   ```

2. **Para elementos que OPCIONALMENTE deben usar el color principal:**
   ```css
   {% if apariencia.usar_color_principal %}
   .nuevo-elemento { color: var(--color_principal_texto) !important; }
   {% endif %}
   ```

3. **Para nuevos campos configurables:**
   - Agregar campo al modelo `AppearanceSettings`
   - Agregar al formulario `AppearanceSettingsForm`
   - Agregar variable CSS en `common_styles.html`
   - Crear migración: `python manage.py makemigrations`

### **Comandos útiles:**
```bash
# Aplicar cambios CSS
python manage.py collectstatic --noinput

# Crear migración para nuevos campos
python manage.py makemigrations colegio

# Aplicar migraciones
python manage.py migrate
```

## ⚠️ Notas Importantes

1. **Cache del navegador**: Los cambios CSS pueden requerir limpieza de cache (Ctrl+F5)
2. **Especificidad CSS**: Usar `!important` cuando sea necesario sobrescribir Bootstrap
3. **Fallbacks**: Siempre proporcionar colores de respaldo en caso de error
4. **Accesibilidad**: Asegurar contraste adecuado entre colores de fondo y texto

## 🎯 Ejemplo Completo de Uso

```html
<!-- Template example -->
<div class="container">
    <!-- Botón que usa automáticamente el color principal (si está habilitado) -->
    <button class="btn btn-primary">Botón Automático</button>
    
    <!-- Botón que SIEMPRE usa el color principal -->
    <button class="btn btn-primary-custom">Botón Forzado</button>
    
    <!-- Texto con color principal -->
    <h2 class="text-primary-custom">Título Principal</h2>
    
    <!-- Card con header del color principal -->
    <div class="card">
        <div class="card-header card-header-primary-custom">
            <h5 class="text-white">Título</h5>
        </div>
        <div class="card-body">
            Contenido de la tarjeta
        </div>
    </div>
</div>
```

---

**📅 Última actualización**: Enero 2025  
**👤 Mantenido por**: Equipo de desarrollo  
**🔗 Archivos relacionados**: 
- `colegio/models.py`
- `colegio/forms.py` 
- `colegio/templates/common_styles.html`
- `colegio/templates/config/apariencia.html`
