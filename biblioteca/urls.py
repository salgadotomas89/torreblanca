from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api

router = DefaultRouter()
router.register(r'codigos-dewey', api.CodigoDeweyViewSet)
router.register(r'editoriales', api.EditorialViewSet)
router.register(r'autores', api.AutorViewSet)
router.register(r'materiales', api.MaterialBibliograficoViewSet)
router.register(r'ejemplares', api.EjemplarViewSet)
router.register(r'libros', api.LibroViewSet)
router.register(r'revistas', api.RevistaViewSet)
router.register(r'tesis', api.TesisViewSet)
router.register(r'fanzines', api.FanzineViewSet)
router.register(r'campos-adicionales', api.CampoAdicionalViewSet)
router.register(r'prestamos', api.PrestamoViewSet)

urlpatterns = [
    path('', views.biblioteca, name="biblioteca"),
    path('reservation', views.horario_computadores, name="biblioteca_computadores"),
    path('agregar-material/', views.agregar_material, name='agregar_material'),
    path('obtener-editoriales/', views.obtener_editoriales, name='obtener_editoriales'),
    #urls del dewey libros
    path('consultar_dewey/', views.consultar_dewey, name='consultar_dewey'),
    path('guardar_dewey', views.guardar_dewey, name="guardar_dewey"),
    path('search_books', views.search_books, name="search_books"),
    path('google_books/', views.google_books, name='google_books'),

    path('openai_recommendation/', views.openai_recommendation, name="openai_recommendation"),

    path('guardar-libro/', views.guardar_libro, name='guardar_libro'),
    path('buscar-editoriales/', views.buscar_editorial, name='buscar_editoriales'),
    path('pedidos', views.biblioteca_pedidos, name="biblioteca_pedidos"),
    path('libros', views.libros, name='libros'),
    path('get_google_book_details/', views.get_google_book_details, name='get_google_book_details'),
    path('eliminar-libro/', views.eliminar_libro, name='eliminar_libro'),

    path('buscar_alumnos/', views.buscar_alumnos, name='buscar_alumnos'),
    path('registrar_prestamo/', views.registrar_prestamo, name='registrar_prestamo'),

    path('eliminar_reserva/', views.eliminar_reserva, name='eliminar_reserva'),
    path('dar_baja_reserva/', views.dar_baja_reserva, name='dar_baja_reserva'),
    path('agregar_codigo_dewey/', views.agregar_codigo_dewey, name='agregar_codigo_dewey'),
    path('actualizar_cantidad/<int:libro_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('buscar_autores/', views.buscar_autores, name='buscar_autores'),

    path('verificar-titulo/', views.verificar_titulo, name='verificar_titulo'),

    path('agregar-editorial/', views.agregar_editorial, name='agregar_editorial'),

    path('actualizar-editorial/', views.actualizar_editorial, name='actualizar_editorial'),
    path('eliminar-editorial/', views.eliminar_editorial, name='eliminar_editorial'),

    path('actualizar-edad/', views.actualizar_edad, name='actualizar_edad'),

    path('verificar-isbn/', views.verificar_isbn, name='verificar_isbn'),

    path('obtener-ejemplares/<int:material_id>/', views.obtener_ejemplares, name='obtener_ejemplares'),

    path('obtener-prestamos/', views.obtener_prestamos, name='obtener_prestamos'),

    path('registrar-devolucion/', views.registrar_devolucion, name='registrar_devolucion'),

    path('verificar-clave-usuario/', views.verificar_clave_usuario, name='verificar_clave_usuario'),

    path('obtener-estadisticas-prestamos/', views.obtener_estadisticas_prestamos, name='obtener_estadisticas_prestamos'),

    path('verificar-deweys/', views.verificar_deweys, name='verificar_deweys'),
    path('cargar-deweys/', views.cargar_deweys, name='cargar_deweys'),

    path('obtener-anos-prestamos/', views.obtener_anos_prestamos, name='obtener_anos_prestamos'),

    path('obtener-info-libro/<int:libro_id>/', views.obtener_info_libro, name='obtener_info_libro'),

    path('actualizar-foto-libro/', views.actualizar_foto_libro, name='actualizar_foto_libro'),


    path('reservar', views.reservar, name='reservar'),

    path('horario/', views.horario_computadores, name='horario_computadores'),
    path('obtener_reservas/', views.obtener_reservas, name='obtener_reservas'),
    path('ranking/lectores/', views.ranking_lectores, name='ranking_lectores'),
    # URLs de la API
    path('api/', include(router.urls)),
]