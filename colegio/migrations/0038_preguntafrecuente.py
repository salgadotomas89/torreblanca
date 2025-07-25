# Generated by Django 5.0.6 on 2025-07-08 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colegio', '0037_menuitem_solo_usuarios_logueados'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreguntaFrecuente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pregunta', models.CharField(help_text='La pregunta que será mostrada', max_length=500)),
                ('respuesta', models.TextField(help_text='La respuesta a la pregunta')),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden de aparición (menor número aparece primero)')),
                ('activa', models.BooleanField(default=True, help_text='Si está activa se mostrará en el sitio web')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Pregunta Frecuente',
                'verbose_name_plural': 'Preguntas Frecuentes',
                'ordering': ['orden', 'fecha_creacion'],
            },
        ),
    ]
