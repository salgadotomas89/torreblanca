from rest_framework import viewsets, permissions
from .models import (
    CodigoDewey, Editorial, Autor, MaterialBibliografico,
    Ejemplar, Libro, Revista, Tesis, Fanzine,
    CampoAdicional, Prestamo
)
from .serializers import (
    CodigoDeweySerializer, EditorialSerializer, AutorSerializer,
    MaterialBibliograficoSerializer, MaterialBibliograficoCreateSerializer,
    EjemplarSerializer, LibroSerializer, RevistaSerializer,
    TesisSerializer, FanzineSerializer, CampoAdicionalSerializer,
    PrestamoSerializer
)

class CodigoDeweyViewSet(viewsets.ModelViewSet):
    queryset = CodigoDewey.objects.all()
    serializer_class = CodigoDeweySerializer
    permission_classes = [permissions.IsAuthenticated]

class EditorialViewSet(viewsets.ModelViewSet):
    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer
    permission_classes = [permissions.IsAuthenticated]

class AutorViewSet(viewsets.ModelViewSet):
    queryset = Autor.objects.all()
    serializer_class = AutorSerializer
    permission_classes = [permissions.IsAuthenticated]

class MaterialBibliograficoViewSet(viewsets.ModelViewSet):
    queryset = MaterialBibliografico.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MaterialBibliograficoCreateSerializer
        return MaterialBibliograficoSerializer

class EjemplarViewSet(viewsets.ModelViewSet):
    queryset = Ejemplar.objects.all()
    serializer_class = EjemplarSerializer
    permission_classes = [permissions.IsAuthenticated]

class LibroViewSet(viewsets.ModelViewSet):
    queryset = Libro.objects.all()
    serializer_class = LibroSerializer
    permission_classes = [permissions.IsAuthenticated]

class RevistaViewSet(viewsets.ModelViewSet):
    queryset = Revista.objects.all()
    serializer_class = RevistaSerializer
    permission_classes = [permissions.IsAuthenticated]

class TesisViewSet(viewsets.ModelViewSet):
    queryset = Tesis.objects.all()
    serializer_class = TesisSerializer
    permission_classes = [permissions.IsAuthenticated]

class FanzineViewSet(viewsets.ModelViewSet):
    queryset = Fanzine.objects.all()
    serializer_class = FanzineSerializer
    permission_classes = [permissions.IsAuthenticated]

class CampoAdicionalViewSet(viewsets.ModelViewSet):
    queryset = CampoAdicional.objects.all()
    serializer_class = CampoAdicionalSerializer
    permission_classes = [permissions.IsAuthenticated]

class PrestamoViewSet(viewsets.ModelViewSet):
    queryset = Prestamo.objects.all()
    serializer_class = PrestamoSerializer
    permission_classes = [permissions.IsAuthenticated] 