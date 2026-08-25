from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0009_ensure_logs_actividad_table"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS aplicaciones_quimicas (
                    id BIGSERIAL PRIMARY KEY,
                    cuartel_id BIGINT NOT NULL REFERENCES cuarteles(id),
                    fecha_aplicacion DATE NOT NULL,
                    producto VARCHAR(150) NOT NULL,
                    tipo_producto VARCHAR(100),
                    dosis NUMERIC(10,2),
                    unidad VARCHAR(50),
                    metodo_aplicacion VARCHAR(100),
                    responsable VARCHAR(120),
                    observaciones TEXT,
                    estado BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_aplicaciones_quimicas_cuartel ON aplicaciones_quimicas(cuartel_id);
                CREATE INDEX IF NOT EXISTS idx_aplicaciones_quimicas_fecha ON aplicaciones_quimicas(fecha_aplicacion);
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS aplicaciones_quimicas;
            """,
        ),
    ]
