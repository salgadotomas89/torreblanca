from django.db import models

from colegio.models import Curso

# Create your models here.


class Evaluacion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    fecha = models.DateField()
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.titulo} - {self.curso}"

    class Meta:
        ordering = ['fecha']