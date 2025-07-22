import datetime
from django.http import JsonResponse
from django.shortcuts import render

from calendario.models import Evaluacion
from colegio.models import Curso

# Create your views here.

from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO

def generar_pdf(request, curso_id, month):
    
    template_path = 'pdf.html'
    today = datetime.date.today()
    month_start = today.replace(day=1, month=int(month))  # Utiliza el valor del mes recibido en el parámetro
    month_end = month_start.replace(month=month_start.month % 12 + 1, day=1) - datetime.timedelta(days=1)
    
    evaluaciones_filtradas = Evaluacion.objects.filter(curso_id=curso_id, fecha__range=(month_start, month_end))
    

    context = {
        'datos': evaluaciones_filtradas  # Obtén los datos de tu modelo
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="calendario.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)

    pdf_content = buffer.getvalue()
    buffer.close()

    response.write(pdf_content)
    return response

def calendario(request, curso_id):
    curso = Curso.objects.get(id=curso_id)
    evaluaciones = Evaluacion.objects.filter(curso=curso)
    eventos = []
    
    for evaluacion in evaluaciones:
        eventos.append({
            'id': evaluacion.id,
            'title': evaluacion.titulo,
            'start': evaluacion.fecha.strftime('%Y-%m-%d'),
            'description': evaluacion.descripcion,
            'color': 'blue',  # Puedes personalizar el color aquí
        })
    
    return render(request, 'calendario.html', {'eventos': eventos})

def guardar_evaluacion(request):
    if request.method == 'POST':
        eval_title = request.POST.get('eval_title')
        eval_date = request.POST.get('eval_date')
        curso_id = request.POST.get('curso_id')  # Obtener el ID del curso seleccionado
        eval_descrip = request.POST.get('eval_descrip')

        print('id del curso seleccionado')
        print(curso_id)

        if eval_title and eval_date:
            # Aquí puedes guardar la evaluación en tu modelo de Evaluacion
            # Por ejemplo:
            curso = Curso.objects.get(id=curso_id)  # Obtén el objeto Curso basado en el ID
            evaluacion = Evaluacion(titulo=eval_title, fecha=eval_date,curso=curso, descripcion = eval_descrip)
            evaluacion.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'})


def eliminar_evaluacion(request):
    print('1')
    if request.method == 'POST':
        print('2')
        event_id = request.POST.get('event_id')
        try:
            print(event_id)
            evaluacion = Evaluacion.objects.get(pk=event_id)
            evaluacion.delete()
            print('3')
            return JsonResponse({'success': True})
        except Evaluacion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'La evaluación no existe.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})