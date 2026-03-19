-- Tabla para almacenar las metas de clientes internacionales
-- Reemplaza Google Sheets con base de datos PostgreSQL en Supabase

CREATE TABLE IF NOT EXISTS metas_clientes (
    id BIGSERIAL PRIMARY KEY,
    año VARCHAR(4) NOT NULL,
    cliente_id VARCHAR(50) NOT NULL,
    cliente_nombre TEXT,
    agrovet DECIMAL(15, 2) DEFAULT 0,
    petmedica DECIMAL(15, 2) DEFAULT 0,
    avivet DECIMAL(15, 2) DEFAULT 0,
    total DECIMAL(15, 2) GENERATED ALWAYS AS (agrovet + petmedica + avivet) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint: cada cliente solo puede tener una meta por año
    CONSTRAINT unique_cliente_año UNIQUE (año, cliente_id)
);

-- Índices para mejorar rendimiento de consultas
CREATE INDEX IF NOT EXISTS idx_metas_año ON metas_clientes(año);
CREATE INDEX IF NOT EXISTS idx_metas_cliente_id ON metas_clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_metas_año_cliente ON metas_clientes(año, cliente_id);

-- Comentarios para documentación
COMMENT ON TABLE metas_clientes IS 'Almacena las metas de venta por cliente internacional y línea comercial';
COMMENT ON COLUMN metas_clientes.año IS 'Año fiscal de la meta (formato: YYYY)';
COMMENT ON COLUMN metas_clientes.cliente_id IS 'ID del cliente en Odoo (res.partner)';
COMMENT ON COLUMN metas_clientes.cliente_nombre IS 'Nombre del cliente para referencia';
COMMENT ON COLUMN metas_clientes.agrovet IS 'Meta para línea AGROVET en USD';
COMMENT ON COLUMN metas_clientes.petmedica IS 'Meta para línea PETMEDICA en USD';
COMMENT ON COLUMN metas_clientes.avivet IS 'Meta para línea AVIVET en USD';
COMMENT ON COLUMN metas_clientes.total IS 'Suma automática de las tres líneas comerciales';

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_metas_clientes_updated_at
    BEFORE UPDATE ON metas_clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilitar Row Level Security (RLS) - opcional pero recomendado
ALTER TABLE metas_clientes ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones con service_role key
CREATE POLICY "Enable all operations for service role"
    ON metas_clientes
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Política para permitir lectura pública con anon key
CREATE POLICY "Enable read for anon"
    ON metas_clientes
    FOR SELECT
    TO anon
    USING (true);
