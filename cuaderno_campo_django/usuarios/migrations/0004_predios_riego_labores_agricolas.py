from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0003_cosecha_fertilizacion_riego"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS predios (
                id BIGSERIAL PRIMARY KEY,
                usuario_id BIGINT NOT NULL REFERENCES usuarios(id),
                nombre_predio VARCHAR(100) NOT NULL,
                ubicacion VARCHAR(150),
                superficie NUMERIC(10,2),
                descripcion TEXT,
                estado BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS cuarteles (
                id BIGSERIAL PRIMARY KEY,
                predio_id BIGINT NOT NULL REFERENCES predios(id),
                nombre_cuartel VARCHAR(100) NOT NULL,
                tipo_cultivo VARCHAR(100),
                variedad VARCHAR(100),
                forma_riego VARCHAR(50),
                anio_plantacion INTEGER,
                superficie NUMERIC(10,2),
                descripcion TEXT,
                estado BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS riego (
                id BIGSERIAL PRIMARY KEY,
                cuartel_id BIGINT NOT NULL REFERENCES cuarteles(id),
                fecha_riego DATE NOT NULL,
                tipo_riego VARCHAR(100),
                horas_riego NUMERIC(10,2),
                caudal NUMERIC(10,2),
                observaciones TEXT,
                estado BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS fertilizacion (
                id BIGSERIAL PRIMARY KEY,
                cuartel_id BIGINT NOT NULL REFERENCES cuarteles(id),
                fecha_aplicacion DATE NOT NULL,
                producto VARCHAR(150),
                dosis NUMERIC(10,2),
                unidad VARCHAR(50),
                metodo_aplicacion VARCHAR(100),
                observaciones TEXT,
                estado BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS cosechas (
                id BIGSERIAL PRIMARY KEY,
                cuartel_id BIGINT NOT NULL REFERENCES cuarteles(id),
                fecha_cosecha DATE NOT NULL,
                tipo_cosecha VARCHAR(100),
                cantidad_kg NUMERIC(12,2),
                cantidad_bins NUMERIC(10,2),
                calidad VARCHAR(50),
                destino VARCHAR(100),
                observaciones TEXT,
                estado BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            ALTER TABLE predios
            ADD COLUMN IF NOT EXISTS superficie_hectareas NUMERIC(10,2),
            ADD COLUMN IF NOT EXISTS inscripcion_cbr VARCHAR(255),
            ADD COLUMN IF NOT EXISTS inscripcion_agua TEXT,
            ADD COLUMN IF NOT EXISTS geolocalizacion_lat NUMERIC(10,7),
            ADD COLUMN IF NOT EXISTS geolocalizacion_lng NUMERIC(10,7);

            UPDATE predios
            SET superficie_hectareas = superficie
            WHERE superficie_hectareas IS NULL AND superficie IS NOT NULL;

            ALTER TABLE riego
            ADD COLUMN IF NOT EXISTS minutos_riego NUMERIC(10,2);

            UPDATE riego
            SET minutos_riego = ROUND(horas_riego * 60, 2)
            WHERE minutos_riego IS NULL AND horas_riego IS NOT NULL;

            CREATE TABLE IF NOT EXISTS labores_agricolas (
                id BIGSERIAL PRIMARY KEY,
                usuario_id BIGINT NOT NULL,
                predio_id BIGINT NOT NULL,
                cuartel_id BIGINT NOT NULL,
                fecha DATE NOT NULL,
                tipo_labor VARCHAR(50) NOT NULL,
                subtipo VARCHAR(80),
                responsable VARCHAR(120),
                descripcion TEXT,
                observaciones TEXT,
                estado BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_labores_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                CONSTRAINT fk_labores_predio FOREIGN KEY (predio_id) REFERENCES predios(id),
                CONSTRAINT fk_labores_cuartel FOREIGN KEY (cuartel_id) REFERENCES cuarteles(id)
            );

            CREATE INDEX IF NOT EXISTS idx_labores_fecha ON labores_agricolas(fecha);
            CREATE INDEX IF NOT EXISTS idx_labores_predio ON labores_agricolas(predio_id);
            CREATE INDEX IF NOT EXISTS idx_labores_cuartel ON labores_agricolas(cuartel_id);
            CREATE INDEX IF NOT EXISTS idx_labores_tipo ON labores_agricolas(tipo_labor);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS labores_agricolas;
            ALTER TABLE riego DROP COLUMN IF EXISTS minutos_riego;
            ALTER TABLE predios
            DROP COLUMN IF EXISTS superficie_hectareas,
            DROP COLUMN IF EXISTS inscripcion_cbr,
            DROP COLUMN IF EXISTS inscripcion_agua,
            DROP COLUMN IF EXISTS geolocalizacion_lat,
            DROP COLUMN IF EXISTS geolocalizacion_lng;
            """,
        ),
    ]
