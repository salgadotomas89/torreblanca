from os import path
from biblioteca.models import Autor, CodigoDewey, Editorial, Libro, MaterialBibliografico, Prestamo, Ejemplar, Reserva
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
from googleapiclient.discovery import build
from django.shortcuts import render
from django.db.models import Count
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import openai
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import F, Count
from datetime import timedelta, datetime
import json
import os
import re
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

# Funciones de utilidad para invalidación de cache
def invalidate_dewey_cache():
    """Invalida el cache de códigos Dewey"""
    from django.core.cache import cache
    cache.delete('biblioteca_dewey_list')

def invalidate_book_cache():
    """Invalida caches relacionados con libros si se implementaran en el futuro"""
    # Aquí se pueden agregar más invalidaciones de cache si se implementan
    pass

def biblioteca(request):
    return render(request, 'biblioteca.html')

def horario_computadores(request):
    return render(request, 'computadores/horario.html')


#vista para que los profesores puedan reservar computadores
@require_http_methods(["POST"])
def reservar(request):
    try:
        nombre_profesor = request.POST.get('nombre_profesor')
        apellido_profesor = request.POST.get('apellido_profesor')
        fecha = request.POST.get('fecha')
        bloque = request.POST.get('bloque')
        necesita_computadores = request.POST.get('necesita_computadores') == 'true'

        # Validar que todos los campos necesarios estén presentes
        if not all([nombre_profesor, apellido_profesor, fecha, bloque]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos son requeridos'
            })

        # Validar que la fecha sea un día de semana
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
        if fecha_obj.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden hacer reservas de lunes a viernes'
            })

        # Validar que las reservas con computadores sean con al menos un día de antelación
        if necesita_computadores:
            hoy = datetime.now().date()
            fecha_reserva = fecha_obj.date()
            if fecha_reserva <= hoy:
                return JsonResponse({
                    'success': False,
                    'error': 'Las reservas con computadores deben hacerse con al menos un día de antelación'
                })

        # Verificar si ya existe una reserva para esa fecha y bloque
        if Reserva.objects.filter(
            fecha=fecha, 
            bloque=bloque
        ).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este bloque ya está reservado para la fecha seleccionada'
            })

        # Crear la reserva
        reserva = Reserva.objects.create(
            nombre_profesor=nombre_profesor,
            apellido_profesor=apellido_profesor,
            fecha=fecha,
            bloque=bloque,
            necesita_computadores=necesita_computadores
        )

        return JsonResponse({
            'success': True,
            'message': 'Reserva creada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def obtener_reservas(request):
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
        
        # Obtener reservas del mes seleccionado
        reservas = Reserva.objects.filter(
            fecha__year=year,
            fecha__month=month
        )
        
        # Formatear datos para la respuesta
        reservas_list = [{
            'fecha': reserva.fecha.strftime('%Y-%m-%d'),
            'bloque': reserva.bloque,
            'nombre_profesor': reserva.nombre_profesor,
            'apellido_profesor': reserva.apellido_profesor,
            'necesita_computadores': reserva.necesita_computadores
        } for reserva in reservas]
        
        return JsonResponse(reservas_list, safe=False)
    
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

def search_books(request):
    from django.db.models import Count, Case, When, IntegerField, Prefetch
    
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        return JsonResponse({'results': [], 'error': 'La búsqueda debe contener al menos 3 caracteres'})
    
    # Optimizar la consulta con select_related y prefetch_related
    materiales = MaterialBibliografico.objects.filter(
        Q(titulo__icontains=query) | 
        Q(autores__nombre__icontains=query) |
        Q(resumen__icontains=query) |
        Q(libro__isbn__icontains=query)
    ).distinct().select_related(
        'libro', 'dewey', 'editorial'
    ).prefetch_related(
        'autores',
        Prefetch(
            'ejemplares',
            queryset=Ejemplar.objects.select_related('material')
        )
    ).annotate(
        # Calcular ejemplares disponibles en la base de datos
        ejemplares_disponibles_count=Count(
            Case(
                When(ejemplares__estado='disponible', then=1),
                output_field=IntegerField()
            )
        )
    )

    results = []
    for material in materiales:
        if hasattr(material, 'libro'):
            libro = material.libro
            authors = ', '.join([autor.nombre for autor in material.autores.all()])
            
            result = {
                'id': material.id,
                'nombre': material.titulo,
                'autor': authors,
                'editorial': material.editorial.nombre if material.editorial else '',
                'cantidad': material.ejemplares_disponibles_count,
                'tema': getattr(libro, 'tema', ''),
                'isbn': libro.isbn,
                'resumen': material.resumen,
                'foto': material.foto.url if material.foto else '',
                'anio': material.anio,
                'dewey': material.dewey.codigo if material.dewey else '',
                'edad': material.edad_recomendada,
                'volumen': material.volumen,
                'total_ejemplares': material.total_copias,
                'ejemplares_disponibles': material.ejemplares_disponibles_count,
                'esta_disponible': material.ejemplares_disponibles_count > 0
            }
            results.append(result)

    return JsonResponse({'results': results})


#vista para mostrar los libros disponibles en la biblioteca
def libros(request):
    from django.db.models import Count, Case, When, IntegerField, Prefetch
    from django.core.cache import cache
    
    # Implementar cache simple para la lista de códigos Dewey
    cache_key = 'biblioteca_dewey_list'
    dewey_list = cache.get(cache_key)
    if dewey_list is None:
        dewey_list = list(CodigoDewey.objects.all().order_by('codigo'))
        cache.set(cache_key, dewey_list, 300)  # Cache por 5 minutos
    
    # Optimizar la consulta con select_related y prefetch_related para evitar consultas N+1
    materiales = MaterialBibliografico.objects.filter(
        libro__isnull=False
    ).select_related(
        'libro', 'editorial', 'dewey'
    ).prefetch_related(
        'autores',
        Prefetch(
            'ejemplares',
            queryset=Ejemplar.objects.select_related('material').order_by('numero_copia')
        )
    ).annotate(
        # Calcular ejemplares disponibles en la base de datos, no en Python
        ejemplares_disponibles_count=Count(
            Case(
                When(ejemplares__estado='disponible', then=1),
                output_field=IntegerField()
            )
        )
    ).order_by('titulo')

    # Usar paginación directa en el QuerySet para mejorar rendimiento
    paginator = Paginator(materiales, 20)
    page = request.GET.get('page', 1)

    try:
        libros_paginados = paginator.page(page)
    except PageNotAnInteger:
        libros_paginados = paginator.page(1)
    except EmptyPage:
        libros_paginados = paginator.page(paginator.num_pages)

    context = {
        'libros': libros_paginados,
        'codigos': dewey_list,
    }
    return render(request, 'libros.html', context)


#vista para buscar libros en google books
@csrf_exempt
def google_books(request):
    if request.method == 'POST':
        query = request.POST.get('q', '')
        if query:
            try:
                service = build('books', 'v1', developerKey='AIzaSyAbYHVbR3Iq7LKy-l5ryXTA1ve3Qb82Qfw')
                response = service.volumes().list(q=query, maxResults=10).execute()
                return JsonResponse({'results': response.get('items', [])})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'No se proporcionó una consulta de búsqueda.'}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)




#vista para obtener la edad recomendada, resumen y codigo dewey para un libro usando openai
@csrf_exempt
def openai_recommendation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            authors = data.get('authors', '')

            # Verificar suscripción antes de usar OpenAI
            from colegio.models import ColegioSubscription
            subscription = ColegioSubscription.get_instance()
            subscription.reset_monthly_usage()
            
            if not subscription.can_use_openai('biblioteca'):
                return JsonResponse({
                    'error': 'Funcionalidad de IA no disponible - Suscripción requerida'
                }, status=403)

            # Configurar la clave de la API de OpenAI
            openai.api_key = settings.OPENAI_API_KEY

            # Crear el prompt para la consulta a OpenAI
            prompt = f"""
            Título del libro: '{title}'
            Autor(es): {authors}

            Por favor, proporciona la siguiente información:
            1. Un resumen breve del libro (aproximadamente 2-3 oraciones).
            2. El rango de edad recomendado para este libro (5-6, 7-8, 9-10, 11-12, o 13+ años).
            3. El código decimal Dewey más apropiado para este libro (incluye el número y la descripción).
            4. El año de publicación del libro (solo el año, si no estás seguro, indica el año más probable).

            Presenta tus respuestas en el siguiente formato:
            Resumen: [resumen del libro]
            Edad recomendada: [rango de edad]
            Código Dewey: [código con descripción]
            Año: [año de publicación]
            """

            try:
                # Realizar la consulta a la API de OpenAI
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un bibliotecario experto en clasificación de libros."},
                        {"role": "user", "content": prompt}
                    ]
                )

                # Procesar la respuesta
                content = response.choices[0].message['content'].strip()
                
                # Extraer información de la respuesta
                resumen_match = re.search(r'Resumen:(.*?)(?=Edad recomendada:|$)', content, re.DOTALL)
                edad_match = re.search(r'Edad recomendada:(.*?)(?=Código Dewey:|$)', content, re.DOTALL)
                dewey_match = re.search(r'Código Dewey:(.*?)(?=Año:|$)', content, re.DOTALL)
                anio_match = re.search(r'Año:(.*?)$', content, re.DOTALL)

                # Preparar la respuesta
                result = {
                    'description': resumen_match.group(1).strip() if resumen_match else '',
                    'age_recommended': edad_match.group(1).strip() if edad_match else '',
                    'dewey_code': dewey_match.group(1).strip() if dewey_match else '',
                    'publication_year': anio_match.group(1).strip() if anio_match else ''
                }

                # Incrementar uso si la llamada fue exitosa
                subscription.increment_usage()

                return JsonResponse(result)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

#vista para guardar un libro en la base de datos
@transaction.atomic
def guardar_libro(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Extraer datos del POST
        titulo = request.POST.get('titulo')
        autores = request.POST.get('autores').split(',')
        isbn = request.POST.get('isbn')
        editorial_nombre = request.POST.get('editorial')
        resumen = request.POST.get('resumen')
        anio = request.POST.get('anio')
        edad_recomendada = request.POST.get('edad_recomendada')
        foto_url = request.POST.get('foto_url')
        dewey_id = request.POST.get('dewey')

        # Obtener o crear la editorial
        editorial, _ = Editorial.objects.get_or_create(nombre=editorial_nombre)

        # Obtener el objeto CodigoDewey
        codigo_dewey = CodigoDewey.objects.get(id=dewey_id)

        # Crear el MaterialBibliografico
        material = MaterialBibliografico.objects.create(
            titulo=titulo,
            editorial=editorial,
            resumen=resumen,
            anio=anio,
            cantidad=1,
            dewey=codigo_dewey,
            edad_recomendada=edad_recomendada
        )

        # Añadir autores
        for autor_nombre in autores:
            autor, _ = Autor.objects.get_or_create(nombre=autor_nombre.strip())
            material.autores.add(autor)

        # Crear el Libro
        libro = Libro.objects.create(
            material=material,
            isbn=isbn
        )

        # Manejar la foto
        if foto_url and foto_url != 'Imagen no disponible':
            response = requests.get(foto_url)
            if response.status_code == 200:
                nombre_archivo = f'{isbn}.jpg'
                material.foto.save(nombre_archivo, ContentFile(response.content), save=True)
        
        return JsonResponse({'mensaje': 'Libro guardado correctamente', 'id': material.id}, status=201)
        
    except CodigoDewey.DoesNotExist:
        return JsonResponse({'error': 'Código Dewey no válido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        # Invalidar cache al guardar libro
        invalidate_book_cache()


@transaction.atomic
def agregar_material(request):
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            
            # Obtener autores del nuevo formato con tags
            autores_ids = request.POST.get('autores_ids')
            autores_nuevos = request.POST.get('autores_nuevos')
            # Mantener compatibilidad con el formato anterior
            autores_nombres = [nombre.strip() for nombre in request.POST.get('autores', '').split(',') if nombre.strip()]
            
            editorial_id = request.POST.get('editorial')
            editorial_nombre = request.POST.get('editorial_nombre')
            anio = request.POST.get('anio')
            volumen = request.POST.get('volumen')
            numero_ejemplares = int(request.POST.get('numero_ejemplares', 1))
            isbn = request.POST.get('isbn')

            # Manejar la editorial
            if editorial_id:
                editorial = Editorial.objects.get(id=editorial_id)
            elif editorial_nombre:
                editorial, _ = Editorial.objects.get_or_create(
                    nombre=editorial_nombre.strip()
                )
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Se requiere una editorial válida'
                })

            # Verificar si ya existe un material con el mismo ISBN
            libro_existente = None
            if isbn:
                libro_existente = Libro.objects.filter(isbn=isbn).first()

            if libro_existente:
                # Si el libro existe, agregar nuevos ejemplares
                material = libro_existente.material
                ultimo_ejemplar = material.ejemplares.order_by('-numero_copia').first()
                siguiente_numero = (ultimo_ejemplar.numero_copia + 1) if ultimo_ejemplar else 1

                # Crear nuevos ejemplares
                for i in range(numero_ejemplares):
                    Ejemplar.objects.create(
                        material=material,
                        numero_copia=siguiente_numero + i
                    )

                # Actualizar el total de ejemplares
                material.total_copias = material.ejemplares.count()
                material.save()

            else:
                # Crear nuevo material bibliográfico
                material = MaterialBibliografico.objects.create(
                    titulo=titulo,
                    editorial=editorial,
                    anio=anio,
                    resumen=request.POST.get('resumen'),
                    edad_recomendada=request.POST.get('edad_recomendada'),
                    dewey_id=request.POST.get('codigo_dewey'),
                    volumen=volumen if volumen else None,
                    total_copias=numero_ejemplares
                )

                # Agregar autores del nuevo formato
                if autores_ids:
                    import json
                    ids_list = json.loads(autores_ids)
                    for autor_id in ids_list:
                        try:
                            autor = Autor.objects.get(id=autor_id)
                            material.autores.add(autor)
                        except Autor.DoesNotExist:
                            pass
                
                if autores_nuevos:
                    import json
                    nombres_list = json.loads(autores_nuevos)
                    for autor_nombre in nombres_list:
                        autor, _ = Autor.objects.get_or_create(nombre=autor_nombre.strip())
                        material.autores.add(autor)
                
                # Mantener compatibilidad con el formato anterior
                for autor_nombre in autores_nombres:
                    autor, _ = Autor.objects.get_or_create(nombre=autor_nombre)
                    material.autores.add(autor)

                # Manejar la foto
                if request.FILES.get('foto'):
                    material.foto = request.FILES['foto']
                    material.save()

                # Crear el libro
                if request.POST.get('tipo') == 'libro':
                    libro = Libro.objects.create(
                        material=material,
                        isbn=isbn
                    )

                # Crear los ejemplares
                for i in range(numero_ejemplares):
                    Ejemplar.objects.create(
                        material=material,
                        numero_copia=i + 1
                    )

            return JsonResponse({
                'success': True,
                'message': f'Material bibliográfico guardado con {numero_ejemplares} ejemplar(es)'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Invalidar cache al agregar nuevo material
    invalidate_book_cache()
    
    context = {
        'editoriales': Editorial.objects.all().order_by('nombre'),
        'codigos_dewey': CodigoDewey.objects.all().order_by('codigo'),
    }
    return render(request, 'agregar_material.html', context)



from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

@require_POST
@csrf_protect
def agregar_codigo_dewey(request):
    codigo = request.POST.get('codigo')
    descripcion = request.POST.get('descripcion')
    
    if codigo and descripcion:
        try:
            # Verificar si ya existe un código igual
            if CodigoDewey.objects.filter(codigo=codigo).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un código Dewey con ese número'
                })

            nuevo_codigo = CodigoDewey.objects.create(
                codigo=codigo,
                descripcion=descripcion
            )
            return JsonResponse({
                'success': True,
                'id': nuevo_codigo.id,
                'codigo': nuevo_codigo.codigo,
                'descripcion': nuevo_codigo.descripcion
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Código y descripción son requeridos'
        })



def consultar_dewey(request):
    openai.api_key = settings.OPENAI_API_KEY

    if request.method == 'POST':
        title = request.POST.get('title')
        authors = request.POST.get('authors')
        prompt = f"Este libro se titula '{title}', escrito por {authors}. Proporcioname el código decimal Dewey con el género al que pertenece, por ejemplo: 823 novelistica inglesa. Ademas de la edad recomendada y un resumen de no mas de 300 carcateres"

        # Realizar la consulta a la API de OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a library assistant, skilled in assigning Dewey Decimal Codes."},
                {"role": "user", "content": prompt}
            ]
        )

        # Obtener la respuesta de OpenAI
        dewey_code = response.choices[0].message['content'].strip()

        return JsonResponse({'dewey_code': dewey_code})

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

def guardar_dewey(request):
    if request.method == 'POST':
        dewey_code = request.POST.get('dewey_code')
        dewey_description = request.POST.get('dewey_description')

        # Guardar el código Dewey en la base de datos
        CodigoDewey.objects.create(codigo=dewey_code, descripcion=dewey_description)
        
        # Invalidar cache de códigos Dewey
        invalidate_dewey_cache()

        codigos = list(CodigoDewey.objects.order_by('codigo').values('id', 'codigo', 'descripcion'))
        return JsonResponse(codigos, safe=False)


    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)


def biblioteca_pedidos(request):
    # Obtener todos los préstamos, ordenados por fecha de préstamo (más reciente primero)
    prestamos = Prestamo.objects.select_related('material', 'alumno').order_by('-fecha_prestamo')

    # Preparar los datos de los préstamos para el contexto
    pedidos_data = []
    for prestamo in prestamos:
        material = prestamo.material
        libro = material.libro if hasattr(material, 'libro') else None

        pedido_info = {
            'id': prestamo.id,
            'titulo': material.titulo,
            'tipo_material': material.get_tipo_display(),
            'alumno': prestamo.alumno.nombre,
            'fecha_prestamo': prestamo.fecha_prestamo,
            'fecha_devolucion': prestamo.fecha_devolucion,
            'estado': prestamo.estado,
            'isbn': libro.isbn if libro else 'N/A',
            'autor': ', '.join([autor.nombre for autor in material.autores.all()]),
        }
        pedidos_data.append(pedido_info)

    context = {
        'pedidos': pedidos_data
    }
    return render(request, "biblioteca_pedidos.html", context)





import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def get_google_book_details(request):
    book_id = request.GET.get('book_id')
    if not book_id:
        return JsonResponse({'error': 'No book ID provided'}, status=400)

    url = f'https://www.googleapis.com/books/v1/volumes/{book_id}'
    response = requests.get(url)
    
    if response.status_code == 200:
        book_data = response.json()
        volume_info = book_data.get('volumeInfo', {})
        
        # Extraer el ISBN (preferiblemente ISBN-13)
        isbn = ''
        industry_identifiers = volume_info.get('industryIdentifiers', [])
        for identifier in industry_identifiers:
            if identifier.get('type') == 'ISBN_13':
                isbn = identifier.get('identifier')
                break
        if not isbn and industry_identifiers:
            isbn = industry_identifiers[0].get('identifier', '')

        return JsonResponse({
            'title': volume_info.get('title', ''),
            'authors': volume_info.get('authors', []),
            'publisher': volume_info.get('publisher', ''),
            'publishedDate': volume_info.get('publishedDate', ''),
            'description': volume_info.get('description', ''),
            'isbn': isbn,
            'pageCount': volume_info.get('pageCount', ''),
            'categories': volume_info.get('categories', []),
            'language': volume_info.get('language', ''),
            'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', '')
        })
    else:
        return JsonResponse({'error': 'Failed to fetch book details'}, status=response.status_code)
    
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def eliminar_libro(request):
    print("Eliminando libro")
    libro_id = request.POST.get('libro_id')
    print(f"ID del libro a eliminar: {libro_id}")
    try:
        material = MaterialBibliografico.objects.get(id=libro_id)
        print(f"Material encontrado: {material}")
        #eliminamos el material
        material.delete()
        # Invalidar cache relacionado
        invalidate_book_cache()
        print("Material eliminado")
        return JsonResponse({'success': True})
    except MaterialBibliografico.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Libro no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from colegio.models import Alumno

def buscar_alumnos(request):
    query = request.GET.get('query', '').strip()
    print(f"Búsqueda de alumnos con query: '{query}'")  # Debug
    
    try:
        if not query:
            # Si no hay query, devolver todos los alumnos
            alumnos = Alumno.objects.all().order_by('nombre', 'paterno')[:50]
        else:
            # Búsqueda con filtros
            alumnos = Alumno.objects.filter(
                Q(nombre__icontains=query) | 
                Q(paterno__icontains=query) | 
                Q(materno__icontains=query)
            ).order_by('nombre', 'paterno')[:50]
        
        data = []
        for alumno in alumnos:
            apellidos = f"{alumno.paterno or ''} {alumno.materno or ''}".strip()
            data.append({
                'id': alumno.id, 
                'nombre': alumno.nombre,
                'apellido': apellidos,
                'curso': str(alumno.curso) if hasattr(alumno, 'curso') and alumno.curso else ''
            })
        
        print(f"Alumnos encontrados: {len(data)}")  # Debug
        print(f"Primer alumno encontrado: {data[0] if data else 'ninguno'}")  # Debug
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        print(f"Error en búsqueda de alumnos: {str(e)}")  # Debug
        return JsonResponse({
            'error': f'Error en la búsqueda: {str(e)}'
        }, status=500)


@require_POST
@csrf_protect
def registrar_prestamo(request):
    try:
        libro_id = request.POST.get('libro_id')
        alumno_id = request.POST.get('alumno_id')
        ejemplar_numero = request.POST.get('ejemplar_numero')
        
        material = MaterialBibliografico.objects.get(id=libro_id)
        alumno = Alumno.objects.get(id=alumno_id)
        ejemplar = material.ejemplares.get(numero_copia=ejemplar_numero)
        
        # Verificar si el ejemplar está disponible
        if ejemplar.estado != 'disponible':
            return JsonResponse({
                'success': False,
                'error': 'El ejemplar seleccionado no está disponible'
            })
        
        # Crear el préstamo
        prestamo = Prestamo.objects.create(
            ejemplar=ejemplar,
            alumno=alumno,
            estado='prestado'
        )
        
        # Actualizar estado del ejemplar
        ejemplar.estado = 'prestado'
        ejemplar.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Préstamo registrado correctamente'
        })
        
    except (MaterialBibliografico.DoesNotExist, Alumno.DoesNotExist, Ejemplar.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Libro, alumno o ejemplar no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



@require_POST
@csrf_protect
def eliminar_reserva(request):
    pedido_id = request.POST.get('pedido_id')
    try:
        prestamo = Prestamo.objects.get(id=pedido_id)
        material = prestamo.material
        material.cantidad += 1
        material.save()
        prestamo.delete()
        return JsonResponse({'success': True})
    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Préstamo no encontrado.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@csrf_protect
def dar_baja_reserva(request):
    pedido_id = request.POST.get('pedido_id')
    try:
        prestamo = Prestamo.objects.get(id=pedido_id)
        material = prestamo.material
        material.cantidad += 1
        material.save()
        prestamo.estado = 'Devuelto'
        prestamo.fecha_devolucion = timezone.now()
        prestamo.save()
        return JsonResponse({'success': True})
    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Préstamo no encontrado.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_POST
@csrf_protect
def actualizar_cantidad(request, libro_id):
    try:
        libro = Libro.objects.get(id=libro_id)
        nueva_cantidad = int(request.POST.get('cantidad', 0))
        libro.cantidad = nueva_cantidad
        libro.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def buscar_autores(request):
    query = request.GET.get('q', '')
    autores = Autor.objects.filter(nombre__icontains=query)[:5]  # Limitar a 5 resultados
    data = [{'id': autor.id, 'nombre': autor.nombre} for autor in autores]
    return JsonResponse(data, safe=False)


def verificar_titulo(request):
    query = request.GET.get('q', '').strip()
    if len(query) >= 2:
        try:
            materiales = MaterialBibliografico.objects.filter(
                titulo__icontains=query
            ).select_related('editorial', 'dewey').prefetch_related('autores')[:5]
            
            resultados = []
            for material in materiales:
                # Obtener el libro si existe
                libro = None
                isbn = ""
                if hasattr(material, 'libro'):
                    libro = material.libro
                    isbn = libro.isbn

                # Crear el resultado con todos los campos necesarios
                resultado = {
                    'id': material.id,
                    'titulo': material.titulo,
                    'autor': ', '.join([autor.nombre for autor in material.autores.all()]),
                    'autores_lista': [autor.nombre for autor in material.autores.all()],
                    'editorial': material.editorial.nombre if material.editorial else '',
                    'editorial_id': material.editorial.id if material.editorial else None,
                    'anio': material.anio,
                    'resumen': material.resumen,
                    'edad_recomendada': material.edad_recomendada,
                    'dewey_id': material.dewey.id if material.dewey else None,
                    'dewey_codigo': material.dewey.codigo if material.dewey else '',
                    'dewey_descripcion': material.dewey.descripcion if material.dewey else '',
                    'volumen': material.volumen,
                    'total_ejemplares': material.total_copias,
                    'isbn': isbn,
                    'foto_url': material.foto.url if material.foto else None,
                    'tipo': 'libro' if libro else 'otro',
                }
                resultados.append(resultado)
            
            return JsonResponse({
                'exists': len(resultados) > 0,
                'resultados': resultados
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'exists': False, 'resultados': []})



@require_POST
@csrf_protect
def actualizar_editorial(request):
    try:
        editorial_id = request.POST.get('id')
        nombre = request.POST.get('nombre', '').strip()
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es requerido'
            })
        
        editorial = Editorial.objects.get(id=editorial_id)
        
        # Verificar si ya existe otra editorial con ese nombre
        if Editorial.objects.filter(nombre__iexact=nombre).exclude(id=editorial_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra editorial con ese nombre'
            })
        
        editorial.nombre = nombre
        editorial.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Editorial actualizada correctamente'
        })
    except Editorial.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Editorial no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
@csrf_protect
def eliminar_editorial(request):
    try:
        editorial_id = request.POST.get('id')
        if not editorial_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de editorial no proporcionado'
            })

        editorial = Editorial.objects.get(id=editorial_id)
        
        # Verificar si la editorial está siendo utilizada
        if MaterialBibliografico.objects.filter(editorial=editorial).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar la editorial porque está siendo utilizada por uno o más materiales'
            })
        
        nombre = editorial.nombre
        editorial.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Editorial "{nombre}" eliminada correctamente'
        })
        
    except Editorial.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Editorial no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def obtener_editoriales(request):
    """Vista para obtener todas las editoriales."""
    try:
        editoriales = Editorial.objects.all().order_by('nombre')
        return JsonResponse({
            'success': True,
            'editoriales': [{'id': e.id, 'nombre': e.nombre} for e in editoriales]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def buscar_editorial(request):
    """Vista para buscar editoriales por término."""
    try:
        term = request.GET.get('term', '').strip()
        if len(term) < 2:
            return JsonResponse([], safe=False)
            
        editoriales = Editorial.objects.filter(
            nombre__icontains=term
        ).order_by('nombre')[:10]
        
        return JsonResponse([{
            'id': e.id,
            'nombre': e.nombre
        } for e in editoriales], safe=False)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def agregar_editorial(request):
    """Vista para agregar una nueva editorial."""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        })

    try:
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es requerido'
            })

        # Verificar si ya existe una editorial con ese nombre
        if Editorial.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una editorial con ese nombre'
            })

        editorial = Editorial.objects.create(nombre=nombre)
        return JsonResponse({
            'success': True,
            'editorial_id': editorial.id,
            'message': 'Editorial agregada correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



@require_POST
@csrf_protect
def actualizar_edad(request):
    try:
        libro_id = request.POST.get('libro_id')
        nueva_edad = request.POST.get('edad')
        
        material = MaterialBibliografico.objects.get(id=libro_id)
        material.edad_recomendada = nueva_edad
        material.save()
        
        return JsonResponse({
            'success': True,
            'nombre': material.titulo,
            'autor': ', '.join([autor.nombre for autor in material.autores.all()])
        })
    except MaterialBibliografico.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Libro no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
@csrf_protect
def verificar_isbn(request):
    isbn = request.POST.get('isbn')
    try:
        libro = Libro.objects.filter(isbn=isbn).first()
        if libro:
            ejemplares = libro.material.ejemplares.all()
            return JsonResponse({
                'exists': True,
                'ejemplares': [
                    {
                        'numero_copia': ejemplar.numero_copia,
                        'estado': ejemplar.estado
                    }
                    for ejemplar in ejemplares
                ]
            })
        return JsonResponse({'exists': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def obtener_ejemplares(request, material_id):

    try:
        material = MaterialBibliografico.objects.get(id=material_id)
        ejemplares = material.ejemplares.all().order_by('numero_copia')
        
        # Preparar la lista de ejemplares con su estado
        ejemplares_data = []
        for ejemplar in ejemplares:
            # Verificar si el ejemplar está en préstamo activo
            prestamo_activo = Prestamo.objects.filter(
                ejemplar=ejemplar, 
                fecha_devolucion__isnull=True
            ).exists()
            
            estado = 'prestado' if prestamo_activo else 'disponible'
            
            ejemplares_data.append({
                'numero_copia': ejemplar.numero_copia,
                'fecha_adquisicion': ejemplar.fecha_adquisicion.strftime('%Y-%m-%d'),
                'estado': estado
            })
        
        return JsonResponse({
            'success': True,
            'ejemplares': ejemplares_data
        })
    except MaterialBibliografico.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Material no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def obtener_prestamos(request):
    try:
        # Obtener todos los préstamos (activos y devueltos)
        prestamos = Prestamo.objects.all().select_related(
            'ejemplar', 
            'ejemplar__material',
            'alumno'
        ).order_by('-fecha_prestamo')

        prestamos_data = []
        for prestamo in prestamos:
            prestamos_data.append({
                'id': prestamo.id,
                'titulo': prestamo.ejemplar.material.titulo,
                'ejemplar': prestamo.ejemplar.numero_copia,
                'alumno': f"{prestamo.alumno.nombre} {prestamo.alumno.paterno} {prestamo.alumno.materno}".strip(),
                'fecha_prestamo': prestamo.fecha_prestamo.strftime('%d/%m/%Y'),
                'fecha_devolucion': prestamo.fecha_devolucion.strftime('%d/%m/%Y') if prestamo.fecha_devolucion else 'Pendiente',
                'estado': prestamo.estado
            })

        return JsonResponse({
            'success': True,
            'prestamos': prestamos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
@csrf_protect
def registrar_devolucion(request):
    try:
        prestamo_id = request.POST.get('prestamo_id')
        prestamo = Prestamo.objects.get(id=prestamo_id)
        
        # Actualizar el préstamo pero mantener el registro
        prestamo.estado = 'devuelto'
        prestamo.fecha_devolucion = timezone.now()
        prestamo.save()
        
        # Actualizar el estado del ejemplar
        ejemplar = prestamo.ejemplar
        ejemplar.estado = 'disponible'
        ejemplar.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Devolución registrada correctamente',
            'fecha_devolucion': prestamo.fecha_devolucion.strftime('%d/%m/%Y')
        })
    except Prestamo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Préstamo no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
@csrf_protect
def verificar_clave_usuario(request):
    try:
        clave = request.POST.get('clave')
        if not clave:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó una clave'
            })
            
        # Verificar la clave del usuario actual
        if request.user.check_password(clave):
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Clave incorrecta'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def obtener_estadisticas_prestamos(request):
    try:
        año = request.GET.get('año')
        mes = request.GET.get('mes')
        
        # Construir el filtro base
        filtro = Q()
        if año:
            filtro &= Q(fecha_prestamo__year=año)
        if mes:
            filtro &= Q(fecha_prestamo__month=mes)

        # Libro más prestado
        libros_prestados = Prestamo.objects.filter(filtro).values(
            'ejemplar__material__titulo'
        ).annotate(
            total_prestamos=Count('id')
        ).order_by('-total_prestamos')[:5]

        # Estadísticas por mes
        prestamos_por_mes = Prestamo.objects.filter(filtro).annotate(
            mes=TruncMonth('fecha_prestamo')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')

        # Tasa de devolución a tiempo
        total_prestamos = Prestamo.objects.filter(filtro).count()
        devueltos_tiempo = Prestamo.objects.filter(
            filtro,
            estado='devuelto',
            fecha_devolucion__lte=F('fecha_prestamo') + timedelta(days=7)
        ).count()

        # Alumnos más frecuentes
        alumnos_frecuentes = Prestamo.objects.filter(filtro).values(
            'alumno__nombre',
            'alumno__paterno'
        ).annotate(
            total_prestamos=Count('id')
        ).order_by('-total_prestamos')[:5]

        return JsonResponse({
            'success': True,
            'libros_mas_prestados': list(libros_prestados),
            'prestamos_por_mes': list(prestamos_por_mes),
            'tasa_devolucion': {
                'a_tiempo': devueltos_tiempo,
                'total': total_prestamos,
                'porcentaje': (devueltos_tiempo/total_prestamos*100) if total_prestamos > 0 else 0
            },
            'alumnos_frecuentes': list(alumnos_frecuentes)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def verificar_deweys(request):
    existe = CodigoDewey.objects.exists()
    return JsonResponse({'existe': existe})

@require_POST
@csrf_protect
def cargar_deweys(request):
    try:
        # Verificar si ya existen códigos
        if CodigoDewey.objects.exists():
            return JsonResponse({
                'success': False,
                'error': 'Los códigos Dewey ya están cargados'
            })

        # Leer el archivo JSON
        json_file_path = os.path.join(settings.STATIC_ROOT, 'data/dewey_codes.json')
        with open(json_file_path, 'r', encoding='utf-8') as file:
            dewey_data = json.load(file)

        # Crear los registros en la base de datos
        for dewey in dewey_data['dewey_codes']:
            if dewey['descripcion']:  # Solo crear si hay descripción
                CodigoDewey.objects.create(
                    codigo=dewey['codigo'],
                    descripcion=dewey['descripcion']
                )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def obtener_anos_prestamos(request):
    """Obtener los años disponibles para filtrar basados en los datos reales"""
    try:
        # Obtener el rango de años desde el primer préstamo hasta el último
        primer_prestamo = Prestamo.objects.order_by('fecha_prestamo').first()
        ultimo_prestamo = Prestamo.objects.order_by('-fecha_prestamo').first()
        
        if not primer_prestamo or not ultimo_prestamo:
            return JsonResponse({
                'success': True,
                'años': [],
                'primer_prestamo': None,
                'ultimo_prestamo': None
            })

        año_inicio = primer_prestamo.fecha_prestamo.year
        año_fin = ultimo_prestamo.fecha_prestamo.year
        
        # Generar lista de años
        años = list(range(año_inicio, año_fin + 1))

        # Obtener meses con préstamos para el año seleccionado
        meses_con_prestamos = Prestamo.objects.dates('fecha_prestamo', 'month').values_list('fecha_prestamo__month', flat=True).distinct()

        return JsonResponse({
            'success': True,
            'años': años,
            'meses_disponibles': list(meses_con_prestamos),
            'primer_prestamo': primer_prestamo.fecha_prestamo.strftime('%Y-%m-%d'),
            'ultimo_prestamo': ultimo_prestamo.fecha_prestamo.strftime('%Y-%m-%d')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def obtener_info_libro(request, libro_id):
    print('estoy buscando info de un libro')
    try:
        material = MaterialBibliografico.objects.select_related('libro', 'editorial', 'dewey').prefetch_related('autores', 'ejemplares').get(id=libro_id)
        
        # Obtener los ejemplares ordenados
        ejemplares = material.ejemplares.all().order_by('numero_copia')
        ejemplares_data = []
        for ejemplar in ejemplares:
            ejemplares_data.append({
                'numero_copia': ejemplar.numero_copia,
                'fecha_adquisicion': ejemplar.fecha_adquisicion.strftime('%d/%m/%Y'),
                'estado': ejemplar.estado,
                'estado_display': 'Disponible' if ejemplar.estado == 'disponible' else 'No disponible'
            })

        # Construir la respuesta
        data = {
            'success': True,
            'libro': {
                'id': material.id,
                'titulo': material.titulo,
                'autor': ', '.join([autor.nombre for autor in material.autores.all()]),
                'editorial': material.editorial.nombre if material.editorial else 'No especificada',
                'isbn': material.libro.isbn if hasattr(material, 'libro') else 'No disponible',
                'dewey': f"{material.dewey.codigo} - {material.dewey.descripcion}" if material.dewey else 'No asignado',
                'anio': str(material.anio) if material.anio else 'No disponible',
                'edad': material.edad_recomendada or 'No especificada',
                'volumen': f"Volumen {material.volumen}" if material.volumen else 'No aplica',
                'resumen': material.resumen or 'No hay resumen disponible',
                'foto_url': material.foto.url if material.foto else None,
                'ejemplares': ejemplares_data,
                'total_ejemplares': len(ejemplares_data),
                'ejemplares_disponibles': sum(1 for e in ejemplares_data if e['estado'] == 'disponible')
            }
        }
        return JsonResponse(data)
    except MaterialBibliografico.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Libro no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_POST
@csrf_protect
def actualizar_foto_libro(request):
    try:
        libro_id = request.POST.get('libro_id')
        nueva_foto = request.FILES.get('foto')
        
        if not nueva_foto:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó ninguna imagen'
            })

        # Validar el tipo de archivo
        if not nueva_foto.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser una imagen'
            })

        material = MaterialBibliografico.objects.get(id=libro_id)
        
        # Eliminar la foto anterior si existe
        if material.foto:
            material.foto.delete(save=False)
        
        # Guardar la nueva foto
        material.foto = nueva_foto
        material.save()
        
        return JsonResponse({
            'success': True,
            'foto_url': material.foto.url,
            'message': 'Foto actualizada correctamente'
        })
    except MaterialBibliografico.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Libro no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


def ranking_lectores(request):
    selected_year = request.GET.get('year', '')
    selected_month = request.GET.get('month', '')
    
    # Obtener años disponibles (desde marzo 2025)
    available_years = list(range(2025, timezone.now().year + 2))
    
    # Meses disponibles
    available_month_choices = [
        (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'),
        (11, 'Noviembre'), (12, 'Diciembre'), (1, 'Enero'), (2, 'Febrero')
    ]
    
    # Crear el diccionario de nombres de meses
    month_names = dict(available_month_choices)
    
    # Filtrar préstamos
    prestamos = Prestamo.objects.filter(estado='devuelto')
    
    if selected_year:
        prestamos = prestamos.filter(fecha_devolucion__year=int(selected_year))
    
    if selected_month:
        prestamos = prestamos.filter(fecha_devolucion__month=int(selected_month))
        selected_month = int(selected_month)
    
    # Calcular ranking de estudiantes que han leído libros
    ranking_data = prestamos.values(
        'alumno__id',
        'alumno__nombre', 
        'alumno__paterno', 
        'alumno__materno',
        'alumno__curso__nombre'
    ).annotate(
        libros_leidos=Count('id')
    ).order_by('-libros_leidos')
    
    # Calcular estadísticas
    total_students = ranking_data.count()
    
    # NUEVO: Calcular estudiantes que están leyendo actualmente
    estudiantes_leyendo_actualmente = Prestamo.objects.filter(
        estado='prestado'  # Préstamos activos
    ).values('alumno').distinct().count()
    
    # NUEVO: Calcular total de libros en circulación
    libros_en_circulacion = Prestamo.objects.filter(
        estado='prestado'
    ).count()
    
    # NUEVO: Calcular promedio de libros leídos
    if total_students > 0:
        total_libros_leidos = sum(student['libros_leidos'] for student in ranking_data)
        promedio_libros = round(total_libros_leidos / total_students, 1)
    else:
        promedio_libros = 0
    
    # NUEVO: Calcular libro más leído
    libro_mas_prestado = prestamos.values(
        'ejemplar__material__titulo'
    ).annotate(
        total_prestamos=Count('id')
    ).order_by('-total_prestamos').first()
    
    if libro_mas_prestado:
        libro_mas_prestado_info = {
            'titulo': libro_mas_prestado['ejemplar__material__titulo'],
            'prestamos': libro_mas_prestado['total_prestamos']
        }
    else:
        libro_mas_prestado_info = {
            'titulo': 'No disponible',
            'prestamos': 0
        }
    
    # NUEVO: Calcular autor más solicitado
    autor_mas_solicitado = prestamos.values(
        'ejemplar__material__autores__nombre'
    ).annotate(
        total_prestamos=Count('id')
    ).order_by('-total_prestamos').first()
    
    if autor_mas_solicitado and autor_mas_solicitado['ejemplar__material__autores__nombre']:
        autor_mas_solicitado_info = {
            'nombre': autor_mas_solicitado['ejemplar__material__autores__nombre'],
            'prestamos': autor_mas_solicitado['total_prestamos']
        }
    else:
        autor_mas_solicitado_info = {
            'nombre': 'No disponible',
            'prestamos': 0
        }
    
    context = {
        'ranking_data': ranking_data,
        'total_students': total_students,
        'estudiantes_leyendo_actualmente': estudiantes_leyendo_actualmente,  # NUEVO
        'libros_en_circulacion': libros_en_circulacion,  # NUEVO
        'promedio_libros': promedio_libros,  # NUEVO
        'libro_mas_prestado': libro_mas_prestado_info,  # NUEVO
        'autor_mas_solicitado': autor_mas_solicitado_info,  # NUEVO
        'available_years': available_years,
        'available_month_choices': available_month_choices,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_names': month_names,
    }
    
    return render(request, 'ranking_lectores.html', context)