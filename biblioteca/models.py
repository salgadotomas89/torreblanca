from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from colegio.models import Alumno

class CodigoDewey(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

class Editorial(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    
    class Meta:
        verbose_name = "Editorial"
        verbose_name_plural = "Editoriales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Autor(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class MaterialBibliografico(models.Model):
    EDAD_CHOICES = [
        ('5-6', '5 a 6 años'),
        ('7-8', '7 a 8 años'),
        ('9-10', '9 a 10 años'),
        ('11-12', '11 a 12 años'),
        ('13+', '13 años en adelante'),
    ]

    titulo = models.CharField(max_length=255)
    autores = models.ManyToManyField('Autor', related_name='materiales')
    editorial = models.ForeignKey('Editorial', on_delete=models.SET_NULL, null=True, blank=True)
    anio = models.IntegerField()
    resumen = models.TextField(blank=True)
    foto = models.ImageField(upload_to='materiales', blank=True)
    edad_recomendada = models.CharField(max_length=10, blank=True, default='0')
    dewey = models.ForeignKey(CodigoDewey, on_delete=models.SET_NULL, null=True)
    volumen = models.PositiveIntegerField(null=True, blank=True, help_text="Número de volumen si es una obra de varios tomos")
    total_copias = models.PositiveIntegerField(default=1)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    contenido_especifico = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"

    def get_tipo_display(self):
        if self.contenido_especifico:
            return self.contenido_especifico._meta.model_name.capitalize()
        return "Material General"

class Ejemplar(models.Model):
    material = models.ForeignKey(MaterialBibliografico, on_delete=models.CASCADE, related_name='ejemplares')
    numero_copia = models.PositiveIntegerField()
    estado = models.CharField(max_length=50, default='disponible')
    fecha_adquisicion = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)

    class Meta:
        unique_together = ('material', 'numero_copia')

    def __str__(self):
        return f"{self.material.titulo} - Ejemplar {self.numero_copia}"

class Libro(models.Model):
    material = models.OneToOneField(MaterialBibliografico, on_delete=models.CASCADE, related_name='libro')
    isbn = models.CharField(max_length=13, unique=True)
    paginas = models.IntegerField(null=True, blank=True)

class Revista(models.Model):
    material = models.OneToOneField(MaterialBibliografico, on_delete=models.CASCADE, related_name='revista')
    issn = models.CharField(max_length=8, unique=True)
    volumen = models.CharField(max_length=50, blank=True)
    numero = models.CharField(max_length=50, blank=True)

class Tesis(models.Model):
    material = models.OneToOneField(MaterialBibliografico, on_delete=models.CASCADE, related_name='tesis')
    institucion = models.CharField(max_length=255)
    grado = models.CharField(max_length=100)

class Fanzine(models.Model):
    material = models.OneToOneField(MaterialBibliografico, on_delete=models.CASCADE, related_name='fanzine')
    numero_edicion = models.CharField(max_length=50, blank=True)
    tema = models.CharField(max_length=100)

class CampoAdicional(models.Model):
    material = models.ForeignKey(MaterialBibliografico, on_delete=models.CASCADE, related_name='campos_adicionales')
    nombre = models.CharField(max_length=100)
    valor = models.TextField()

    class Meta:
        unique_together = ('material', 'nombre')

class Prestamo(models.Model):
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.CASCADE, related_name='prestamos')
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='prestamos')
    fecha_prestamo = models.DateTimeField(default=timezone.now)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=50, default='prestado')

    def __str__(self):
        return f"Préstamo de {self.ejemplar.material.titulo} (Ejemplar {self.ejemplar.numero_copia}) a {self.alumno.nombre}"

class Reserva(models.Model):
    BLOQUES_CHOICES = [
        ('1', '8:30 - 10:00'),
        ('2', '10:20 - 11:45'),
        ('3', '12:00 - 13:30'),
        ('4', '14:15 - 15:45'),
    ]

    nombre_profesor = models.CharField(max_length=100)
    apellido_profesor = models.CharField(max_length=100)
    fecha = models.DateField()
    bloque = models.CharField(max_length=1, choices=BLOQUES_CHOICES)
    necesita_computadores = models.BooleanField(default=False, verbose_name="¿Necesita computadores?")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fecha', 'bloque')
        ordering = ['fecha', 'bloque']

    def __str__(self):
        return f"{self.nombre_profesor} {self.apellido_profesor} - {self.fecha} Bloque {self.get_bloque_display()}"