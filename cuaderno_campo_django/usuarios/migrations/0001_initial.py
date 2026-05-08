from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rut", models.CharField(max_length=20, unique=True)),
                ("nombre", models.CharField(max_length=100)),
                ("usuario", models.CharField(max_length=50, unique=True)),
                ("password", models.CharField(max_length=255)),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("admin", "Administrador"),
                            ("tecnico", "Tecnico"),
                            ("productor", "Productor"),
                        ],
                        max_length=20,
                    ),
                ),
                ("celular", models.CharField(blank=True, max_length=20)),
                ("sector", models.CharField(blank=True, max_length=100)),
                ("estado", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Usuario",
                "verbose_name_plural": "Usuarios",
                "db_table": "usuarios",
                "ordering": ["-created_at"],
            },
        ),
    ]
