from rest_framework import serializers
from .models import (
    CodigoDewey, Editorial, Autor, MaterialBibliografico,
    Ejemplar, Libro, Revista, Tesis, Fanzine,
    CampoAdicional, Prestamo
)

class CodigoDeweySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodigoDewey
        fields = ['id', 'codigo', 'descripcion']

class EditorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = ['id', 'nombre']

class AutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nombre']

class CampoAdicionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampoAdicional
        fields = ['id', 'nombre', 'valor']

class LibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = ['isbn', 'paginas']

class RevistaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revista
        fields = ['issn', 'volumen', 'numero']

class TesisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tesis
        fields = ['institucion', 'grado']

class FanzineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fanzine
        fields = ['numero_edicion', 'tema']

class EjemplarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ejemplar
        fields = ['id', 'material', 'numero_copia', 'estado', 'fecha_adquisicion', 'notas']

class PrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestamo
        fields = ['id', 'ejemplar', 'alumno', 'fecha_prestamo', 'fecha_devolucion', 'estado']

class MaterialBibliograficoSerializer(serializers.ModelSerializer):
    autores = AutorSerializer(many=True, read_only=True)
    editorial = EditorialSerializer(read_only=True)
    dewey = CodigoDeweySerializer(read_only=True)
    campos_adicionales = CampoAdicionalSerializer(many=True, read_only=True)
    ejemplares = EjemplarSerializer(many=True, read_only=True)
    libro = LibroSerializer(read_only=True)
    revista = RevistaSerializer(read_only=True)
    tesis = TesisSerializer(read_only=True)
    fanzine = FanzineSerializer(read_only=True)

    class Meta:
        model = MaterialBibliografico
        fields = [
            'id', 'titulo', 'autores', 'editorial', 'anio', 'resumen',
            'foto', 'edad_recomendada', 'dewey', 'volumen', 'total_copias',
            'campos_adicionales', 'ejemplares', 'libro', 'revista',
            'tesis', 'fanzine'
        ]

class MaterialBibliograficoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialBibliografico
        fields = [
            'titulo', 'autores', 'editorial', 'anio', 'resumen',
            'foto', 'edad_recomendada', 'dewey', 'volumen', 'total_copias'
        ] 