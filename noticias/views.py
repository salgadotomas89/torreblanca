from datetime import datetime
from django.shortcuts import redirect, render
from django.http import Http404, JsonResponse
from colegio.models import Colegio
from noticias.forms import FormNoticia
from noticias.models import Images, Noticia
from .openai_utils import get_openai_response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


def chat_with_openai(request):
    prompt = request.GET.get('prompt', '')
    if not prompt:
        return JsonResponse({'error': 'No se proporcionó ningún prompt'}, status=400)
    
    response_text = get_openai_response(prompt)
    return JsonResponse({'response': response_text})


def noticias(request, id):
    otras_noticias = None
    ultima_noticia = None

    try:
        if id != 0:  # Si elegí alguna noticia en particular, la traigo con su id
            ultima_noticia = Noticia.objects.get(id=id)
            # Traigo las últimas 2 noticias excluyendo el elemento elegido por el id
            otras_noticias = Noticia.objects.exclude(id=id).order_by('-date')[:2]
        else:  # Si elegí la sección noticias
            # Comprobar si la tabla Noticias está vacía
            noticia = Noticia.objects.first()

            if noticia is None:
                print("La tabla Noticias está vacía, no hay objetos.")
            else:
                print("La tabla Noticias contiene al menos un objeto.")
                # Asigno la noticia más reciente como principal
                ultima_noticia = Noticia.objects.latest('date')
                otras_noticias = Noticia.objects.exclude(id=ultima_noticia.id)[:2]  # Puedes ajustar el número de noticias aquí

    except Noticia.DoesNotExist:
        error_message = "La noticia solicitada no existe."
        return render(request, '404.html' , {'error_message': error_message}, status=404)

    # Año actual
    currentYear = datetime.now().year
    currentMonth = datetime.now().month
    
    # Obtener archivos organizados por año y mes
    archivos_organizados = {}
    todas_las_noticias = Noticia.objects.all().order_by('-date')
    
    # Nombres de los meses en español
    meses_nombres = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    for noticia in todas_las_noticias:
        # Obtener fecha local de la noticia
        from django.utils import timezone
        fecha_local = timezone.localtime(noticia.date)
        año = fecha_local.year
        mes = fecha_local.month
        mes_nombre = meses_nombres[mes]
        
        if año not in archivos_organizados:
            archivos_organizados[año] = {}
        
        if mes_nombre not in archivos_organizados[año]:
            archivos_organizados[año][mes_nombre] = []
        
        archivos_organizados[año][mes_nombre].append({
            'id': noticia.id,
            'titulo': noticia.titulo,
            'fecha': fecha_local,
            'redactor': noticia.redactor
        })
    
    # Ordenar años de mayor a menor
    archivos_organizados = dict(sorted(archivos_organizados.items(), reverse=True))


    # Obtener el nombre completo del usuario para prellenar el campo redactor
    user_full_name = ""
    if request.user.is_authenticated and request.user.is_superuser:
        user_full_name = f"{request.user.first_name} {request.user.last_name}".strip().title()
        if not user_full_name:
            user_full_name = request.user.username.title()

    data = {
        'año': currentYear,
        'archivos_organizados': archivos_organizados,
        'noticias': otras_noticias,
        'principal': ultima_noticia,
        'user_full_name': user_full_name,
    }

    return render(request, 'noticias.html', data)


@require_http_methods(["POST"])
def destroy_noticia(request, id):
    import os
    from django.conf import settings
    
    try:
        news = Noticia.objects.get(id=id)
        
        # Eliminar archivos de imágenes asociadas
        images = news.images_set.all()
        for img in images:
            if img.image and os.path.exists(img.image.path):
                try:
                    os.remove(img.image.path)
                except Exception as e:
                    print(f"Error al eliminar imagen {img.image.path}: {str(e)}")
        
        # Eliminar archivo de audio si existe
        if news.audio and os.path.exists(news.audio.path):
            try:
                os.remove(news.audio.path)
            except Exception as e:
                print(f"Error al eliminar audio {news.audio.path}: {str(e)}")
        
        # Eliminar la noticia (esto también eliminará las entradas Images por CASCADE)
        news.delete()
        
        return JsonResponse({'message': 'Noticia y archivos adjuntos eliminados exitosamente'})
    except Noticia.DoesNotExist:
        return JsonResponse({'error': 'La noticia que intentas eliminar no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar la noticia: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # Permite peticiones POST sin verificación CSRF para esta vista específica
def generar_texto_noticia(request):
    from django.core.cache import cache
    from time import sleep
    import hashlib
    
    MAX_RETRIES = 3
    CACHE_TIMEOUT = 3600  # 1 hora
    
    try:
        # 1. Validación mejorada de entrada
        titulo = request.POST.get('titulo', '').strip()
        subtitulo = request.POST.get('subtitulo', '').strip()
        tema = request.POST.get('tema', '').strip()
        
        if not all([titulo, subtitulo]):
            return JsonResponse({
                'error': 'Campos requeridos faltantes',
                'detalles': {
                    'titulo': 'requerido' if not titulo else 'ok',
                    'subtitulo': 'requerido' if not subtitulo else 'ok'
                }
            }, status=400)
            
        # 2. Verificar cache
        cache_key = hashlib.md5(f"{titulo}:{subtitulo}".encode()).hexdigest()
        cached_response = cache.get(cache_key)
        if cached_response:
            return JsonResponse({'texto': cached_response, 'from_cache': True})
            
        # 3. Obtener información contextual
        colegio = Colegio.objects.first()
        nombre_colegio = colegio.nombre if colegio else "nuestro colegio"
        
        # 4. Construir prompt mejorado con más contexto
        prompt = f"""Escribe una noticia educativa profesional (máximo 600 caracteres) para {nombre_colegio}.
        
        Detalles de la noticia:
        - Título: {titulo}
        - Subtítulo: {subtitulo}
        - Tema principal: {tema if tema else 'Educación general'}
        
        Requisitos:
        1. Tono: Profesional y educativo
        2. Estructura: 
           - Introducción clara
           - Desarrollo conciso
           - Conclusión impactante
        3. Enfoque:
           - Relevancia educativa
           - Impacto en la comunidad escolar
           - Beneficios para estudiantes/profesores
        
        Estilo:
        - Objetivo y verificable
        - Positivo y constructivo
        - Apropiado para toda la comunidad educativa
        - Evitar jerga técnica excesiva
        
        La noticia debe ser inspiradora y motivadora, manteniendo un balance entre información y engagement."""
        
        # 5. Sistema de reintentos con backoff exponencial
        for intento in range(MAX_RETRIES):
            try:
                texto_generado = get_openai_response(prompt, 'noticias')
                
                if not texto_generado or texto_generado.startswith("Error"):
                    if intento < MAX_RETRIES - 1:
                        sleep(2 ** intento)  # Backoff exponencial
                        continue
                    return JsonResponse({'error': 'No se pudo generar el texto después de varios intentos'}, status=500)
                
                # 6. Verificación y limpieza del texto
                texto_generado = texto_generado.strip()
                
                # 7. Verificación básica de contenido apropiado
                palabras_prohibidas = ['violencia', 'muerte', 'discriminación', 'drogas']
                if any(palabra in texto_generado.lower() for palabra in palabras_prohibidas):
                    return JsonResponse({'error': 'El contenido generado no es apropiado'}, status=400)
                
                # 8. Truncar si es necesario, pero en un punto apropiado
                if len(texto_generado) > 500:
                    ultimo_punto = texto_generado[:500].rfind('.')
                    if ultimo_punto > 0:
                        texto_generado = texto_generado[:ultimo_punto + 1]
                
                # 9. Guardar en caché
                cache.set(cache_key, texto_generado, CACHE_TIMEOUT)
                
                return JsonResponse({
                    'texto': texto_generado,
                    'caracteres': len(texto_generado),
                    'from_cache': False
                })
                
            except Exception as e:
                if intento == MAX_RETRIES - 1:
                    return JsonResponse({
                        'error': 'Error en la generación de texto',
                        'detalles': str(e)
                    }, status=500)
                sleep(2 ** intento)
                
    except Exception as e:
        return JsonResponse({
            'error': 'Error interno del servidor',
            'detalles': str(e)
        }, status=500)


@require_http_methods(["POST"])
def crear_noticia(request):
    from django.utils import timezone
    
    try:
        titulo = request.POST.get('titulo')
        subtitulo = request.POST.get('subtitulo')
        texto = request.POST.get('texto')
        redactor = request.POST.get('redactor')
        galeria = request.POST.get('galeria') == 'True'
        tema = request.POST.get('tema', '')
        audio = request.FILES.get('audio')

        print('el texto es ', texto)
        print('Fecha y hora de creación:', timezone.now())

        noticia = Noticia.objects.create(
            titulo=titulo,
            subtitulo=subtitulo,
            texto=texto,
            redactor=redactor,
            galeria=galeria,
            tema=tema,
            audio=audio,
            date=timezone.now()  # Asegurar que se use la fecha/hora actual
        )

        # Guardar imágenes
        imagenes = request.FILES.getlist('imagenes')
        for img in imagenes:
            Images.objects.create(noticia=noticia, image=img)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



