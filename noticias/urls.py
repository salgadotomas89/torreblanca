from django.urls import include, path
from . import views

urlpatterns = [
    path('<int:id>', views.noticias, name='noticias'),
    path('delete/noticia/<int:id>', views.destroy_noticia, name='delete_noticia'),
    path('generar-texto/', views.generar_texto_noticia, name='generar_texto_noticia'),
    path('crear-noticia/', views.crear_noticia, name='crear_noticia'),
]