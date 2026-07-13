-- Add subform support to etl_api_config
-- Run once after setup_config_table.sql

ALTER TABLE dbo.etl_api_config
    ADD subform_name  NVARCHAR(200) NULL,   -- OData subform to $expand, e.g. 'FNCITEMS_SUBFORM'
        subform_table NVARCHAR(200) NULL;   -- target table for subform rows, e.g. 'dbo.tiltan_fncitems'

-- Wire up FNCITEMS for all three tenants:
--   FNCTRANS fetches with $expand=FNCITEMS_SUBFORM and writes subform rows to {tenant}_fncitems
UPDATE dbo.etl_api_config
SET subform_name  = 'FNCITEMS_SUBFORM',
    subform_table = 'dbo.' + tenant + '_fncitems'
WHERE endpoint = 'FNCTRANS';

-- Disable the standalone FNCITEMS rows (now handled via FNCTRANS expansion)
UPDATE dbo.etl_api_config
SET active = 0
WHERE endpoint = 'FNCITEMS';
