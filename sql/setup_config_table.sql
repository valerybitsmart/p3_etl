-- ============================================================
-- Run once to bootstrap ETL config tables in SQL Server
-- ============================================================

-- ------------------------------------------------------------
-- 1. Tenant registry  (one row per company)
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'etl_tenant_config'
)
BEGIN
    CREATE TABLE dbo.etl_tenant_config (
        tenant      NVARCHAR(50)   NOT NULL PRIMARY KEY,  -- e.g. 'tiltan'
        base_url    NVARCHAR(500)  NOT NULL,              -- full OData base URL
        auth        NVARCHAR(500)  NOT NULL,              -- 'Basic <token>'
        active      BIT            NOT NULL DEFAULT 1,
        description NVARCHAR(500)  NULL,
        created_at  DATETIME2      NOT NULL DEFAULT GETDATE(),
        updated_at  DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END;

-- Seed tenants
INSERT INTO dbo.etl_tenant_config (tenant, base_url, auth, description) VALUES
('a110123', 'https://p.priority-connect.online/odata/Priority/tabZ66F6.ini/a110123', 'Basic CHANGE_ME', 'Company A110123'),
('tiltan',  'https://p.priority-connect.online/odata/Priority/tabZ66F6.ini/tiltan',  'Basic CHANGE_ME', 'Tiltan'),
('nimbos',  'https://p.priority-connect.online/odata/Priority/tabZ66F6.ini/nimbos',  'Basic CHANGE_ME', 'Nimbos');

-- ------------------------------------------------------------
-- 2. Endpoint config  (one row per tenant × endpoint)
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'etl_api_config'
)
BEGIN
    CREATE TABLE dbo.etl_api_config (
        id            INT IDENTITY(1,1) PRIMARY KEY,
        tenant        NVARCHAR(50)   NOT NULL REFERENCES dbo.etl_tenant_config(tenant),
        endpoint      NVARCHAR(200)  NOT NULL,   -- e.g. 'AGENTS'
        target_table  NVARCHAR(200)  NOT NULL,   -- e.g. 'dbo.tiltan_agents'
        active        BIT            NOT NULL DEFAULT 1,
        description   NVARCHAR(500)  NULL,
        last_run      DATETIME2      NULL,
        last_row_count INT           NULL,
        created_at    DATETIME2      NOT NULL DEFAULT GETDATE(),
        updated_at    DATETIME2      NOT NULL DEFAULT GETDATE(),
        CONSTRAINT uq_etl_api_config UNIQUE (tenant, endpoint)
    );
END;

-- ------------------------------------------------------------
-- 3. Run log (one row per successful endpoint load)
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'etl_run_log'
)
BEGIN
    CREATE TABLE dbo.etl_run_log (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        run_time        DATETIME2      NOT NULL DEFAULT GETDATE(),
        tenant          NVARCHAR(50)   NOT NULL,
        endpoint        NVARCHAR(200)  NOT NULL,
        target_table    NVARCHAR(200)  NOT NULL,
        parent_rows     INT            NOT NULL DEFAULT 0,
        subform_rows    INT            NOT NULL DEFAULT 0,
        duration_sec    INT            NULL,      -- wall-clock seconds for this endpoint
        subform_table   NVARCHAR(200)  NULL
    );
END;

-- ------------------------------------------------------------
-- 4. Error log
-- ------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'etl_error_log'
)
BEGIN
    CREATE TABLE dbo.etl_error_log (
        id            INT IDENTITY(1,1) PRIMARY KEY,
        error_time    DATETIME2      NOT NULL DEFAULT GETDATE(),
        tenant        NVARCHAR(50)   NULL,
        endpoint      NVARCHAR(200)  NULL,
        target_table  NVARCHAR(200)  NULL,
        error_type    NVARCHAR(200)  NULL,   -- exception class name
        error_message NVARCHAR(2000) NULL,   -- str(exc)
        stack_trace   NVARCHAR(MAX)  NULL,   -- full traceback
        resolved      BIT            NOT NULL DEFAULT 0,
        notes         NVARCHAR(1000) NULL    -- manual notes after investigation
    );
END;

-- Seed endpoints for all three tenants
INSERT INTO dbo.etl_api_config (tenant, endpoint, target_table, active, description) VALUES
('a110123', 'AGENTS',    'dbo.a110123_agents',    1, 'Agents - A110123'),
('a110123', 'CUSTOMERS', 'dbo.a110123_customers', 1, 'Customers - A110123'),
('tiltan',  'AGENTS',    'dbo.tiltan_agents',     1, 'Agents - Tiltan'),
('tiltan',  'CUSTOMERS', 'dbo.tiltan_customers',  1, 'Customers - Tiltan'),
('nimbos',  'AGENTS',    'dbo.nimbos_agents',     1, 'Agents - Nimbos'),
('nimbos',  'CUSTOMERS', 'dbo.nimbos_customers',  1, 'Customers - Nimbos');
