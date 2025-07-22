from django.db.models import Q, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.template.loader import render_to_string
from django.db.models import Q
# Desde cualquier archivo dentro de tus apps
from colegio.models import AppearanceSettings, Asignatura, Colegio, Curso, CursoAsignatura, Evento, HeroSettings, HeroImage, Menu, MenuItem, PreguntaFrecuente, UserProfile, ColegioSubscription, Profesor, Administrativo, Asistente, Alumno, Apoderado
from comunicados.models import Comunicado, Comunicados
from noticias.models import Images, Noticia
from .forms import AppearanceSettingsForm, CustomUserForm, FormEvento, HeroSettingsForm, MenuForm, MenuItemForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import default_storage
import os
from .forms import MenuItemForm, MenuForm  # Agrega esto a tus imports si no lo tienes
from django.db.models import Max  # Agregar al inicio del archivo
from django.conf import settings
from django.contrib.auth import logout, login, authenticate


def not_found(request, exception):
    error_message = "Lo sentimos, la página que estás buscando no se encuentra disponible."
    return render(request, '404.html', {'error_message': error_message}, status=404)

#datos de acceso a admin salgadotomas, miercoles

from django.core import serializers


#funcion para registrar un profesor
def registro_profesor(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            # Guardar los datos del formulario
            form.save()
            # Puedes devolver una respuesta JSON con un mensaje de éxito
            return JsonResponse({"message": "Profesor guardado con éxito"})
        else:
            # Si el formulario no es válido, devuelve un error
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": "Solicitud no válida"}, status=400)





def nuevo_formato(fecha):
    print('hola')


def calendario(request):
    cursos = Curso.objects.all()
    print(cursos)
    context = {
        "cursos": cursos,
    }
    return render(request, 'calendario_evaluaciones_2.html', context)



from rest_framework import viewsets
from .models import Administrativo, Alumno, Apoderado, Asistente, Evento, Profesor, UserRole
from .serializers import EventoSerializer

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer



def directiva(request):
    context = {'lista': ['directiva','misión', 'visión', 'direccion', 'reglamentos']
}
    return render(request, 'directiva.html', context)

#devuelve la vista para ver a todos los profesores del colegio
def profesores(request):
    return render(request, 'profesores.html')

def inicio(request):
    #se extraen los 3  eventos con fecha mas cercana
    eventos = Evento.objects.all().order_by('-fecha')[:3]

    #traigo a 4 profesores desde la base de datos
    profesores = UserProfile.objects.filter(role='profesor')[:3]

    noticias = Noticia.objects.all()
    form = CustomUserForm()  # Crear una instancia del formulario

    try:
        seccion_comunicado = Comunicados.objects.get()
    except Comunicados.DoesNotExist:
        seccion_comunicado = None

    # Obtener preguntas frecuentes activas
    preguntas_frecuentes = PreguntaFrecuente.objects.filter(activa=True).order_by('orden', 'fecha_creacion')[:6]

    # Obtener configuraciones de apariencia para el número de WhatsApp
    try:
        appearance_settings = AppearanceSettings.objects.first()
    except AppearanceSettings.DoesNotExist:
        appearance_settings = None

    # Obtener configuración del hero
    hero = HeroSettings.get_or_create_default()

    context = {
               'comunicado': seccion_comunicado,
               'noticias': noticias,
               'eventos': eventos,
               'form_usuario' : form,
               'profesores': profesores,
               'preguntas_frecuentes': preguntas_frecuentes,
               'appearance_settings': appearance_settings,
               'hero': hero,
               }
    
    return render(request, 'inicio/home.html', context)



def registro(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            return redirect('inicio')  # Redirige a la pgina de inicio después del registro
    else:
        form = CustomUserForm()
    return render(request, 'registration/form.html', {'form': form})



def guardar_evento(request):
    if request.method == 'POST':
        # Acceder a los datos del comunicado enviados en la solicitud
        evento = FormEvento(request.POST)
        if evento.is_valid():
            evento.save()
            print('evento creado')
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Método de solicitud no válido'})






@csrf_exempt
def registro_usuario(request):
    if request.method == 'POST':
        # Asegurarnos que el rol sea válido
        role = request.POST.get('role')
        valid_roles = dict(UserProfile.ROLES).keys()
        if role not in valid_roles:
            return JsonResponse({
                "success": False,
                "error": {
                    "role": ["Rol no válido. Opciones válidas: " + ", ".join(valid_roles)]
                }
            })

        form = CustomUserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Crear el UserProfile con el rol
                user_profile = UserProfile.objects.create(user=user, role=role)
                
                # Debug: Verificar si hay archivos en la request
                print(f"FILES en request: {request.FILES}")
                print(f"Foto en FILES: {'foto' in request.FILES}")
                
                # Procesar la foto si se subió una
                if 'foto' in request.FILES:
                    foto = request.FILES['foto']
                    print(f"Archivo recibido: {foto.name}, Tipo: {foto.content_type}, Tamaño: {foto.size}")
                    
                    # Validar el archivo
                    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
                    if foto.content_type in allowed_types and foto.size <= 5 * 1024 * 1024:  # 5MB máximo
                        user_profile.foto = foto
                        user_profile.save()
                        print(f"Foto guardada correctamente: {user_profile.foto.url}")
                    else:
                        print(f"Archivo no válido - Tipo: {foto.content_type}, Tamaño: {foto.size}")
                else:
                    print("No se encontró archivo de foto en la request")
                
                return JsonResponse({
                    "success": True, 
                    "message": "Usuario creado correctamente",
                    "foto_guardada": bool('foto' in request.FILES and user_profile.foto)
                })
            except Exception as e:
                # Si algo falla, eliminar el usuario creado
                if 'user' in locals():
                    user.delete()
                print(f"Error al crear usuario: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": {"general": [str(e)]}
                })
        else:
            return JsonResponse({
                "success": False,
                "error": form.errors
            })
    return JsonResponse({"success": False, "error": {"general": ["Método no permitido"]}})


def guardar_color_comunicados(request):
    if request.method == 'POST':
        try:
            color = request.POST.get('color')
            # Obtener o crear la configuración de apariencia
            appearance_settings = AppearanceSettings.objects.first()
            if not appearance_settings:
                appearance_settings = AppearanceSettings()
            
            # Guardar el color en el campo comunicados_background
            appearance_settings.comunicados_background = color
            appearance_settings.save()
            
            return JsonResponse({
                'success': True,
                'color': color
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

def guardar_color_profesores(request):
    if request.method == 'POST':
        try:
            color = request.POST.get('color')
            appearance_settings = AppearanceSettings.objects.first()
            if not appearance_settings:
                appearance_settings = AppearanceSettings()
            
            appearance_settings.profesores_background = color
            appearance_settings.save()
            
            return JsonResponse({
                'success': True,
                'color': color
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


def contacto(request):
    return render(request, 'contacto.html')







# Vistas para los templates del megamenú
def vision(request):
    """Vista para mostrar la página de visión del colegio"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/vision.html', context)

def mision(request):
    """Vista para mostrar la página de misión del colegio"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/mision.html', context)

def valores(request):
    """Vista para mostrar la página de valores del colegio"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/valores.html', context)

def proyecto_educativo(request):
    """Vista para mostrar la página del proyecto educativo del colegio"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/proyecto_educativo.html', context)

def reglamentos(request):
    """Vista para mostrar la página de reglamentos del colegio"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/reglamentos.html', context)

def directiva_megamenu(request):
    """Vista para mostrar la página de directiva del colegio desde el megamenú"""
    colegio = Colegio.objects.first()
    context = {
        'colegio': colegio,
    }
    return render(request, 'megamenu/directiva.html', context)


def admision(request):
    return render(request, 'admision.html')