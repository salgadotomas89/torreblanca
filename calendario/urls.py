from django.urls import path
from . import views


urlpatterns = [
    path('get/<int:curso_id>', views.calendario),
    path('guardar_evaluacion/', views.guardar_evaluacion, name='guardar_evaluacion'),
    path('eliminar_evaluacion/', views.eliminar_evaluacion, name='eliminar_evaluacion'),
    path('generar_pdf/<int:curso_id>/<int:month>', views.generar_pdf, name='generar_pdf'),
]
