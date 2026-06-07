-- ============================================================
-- Seed all endpoints for all three tenants
-- Safe to re-run: INSERT only if the (tenant, endpoint) pair
-- does not already exist.
-- ============================================================

INSERT INTO dbo.etl_api_config (tenant, endpoint, target_table, active, description)
SELECT v.tenant, v.endpoint, v.target_table, 1, v.description
FROM (VALUES
    -- ── a110123 ──────────────────────────────────────────────
    ('a110123','AGENTS',               'dbo.a110123_agents',               'Agents'),
    ('a110123','ACCOUNTS',             'dbo.a110123_accounts',             'Accounts'),
    ('a110123','AINVOICES',            'dbo.a110123_ainvoices',            'AR Invoices'),
    ('a110123','CINVOICES',            'dbo.a110123_cinvoices',            'Credit Invoices'),
    ('a110123','CUSTOMERS',            'dbo.a110123_customers',            'Customers'),
    ('a110123','DOCUMENTS_D',          'dbo.a110123_documents_d',          'Documents Detail'),
    ('a110123','FAMILYTYPES',          'dbo.a110123_familytypes',          'Family Types'),
    ('a110123','FAMILY_LOG',           'dbo.a110123_family_log',           'Family Log'),
    ('a110123','FNCITEMS',             'dbo.a110123_fncitems',             'Finance Items'),
    ('a110123','FNCTRANS',             'dbo.a110123_fnctrans',             'Finance Transactions'),
    ('a110123','GENINVOICES',          'dbo.a110123_geninvoices',          'General Invoices'),
    ('a110123','INVOICEREP',           'dbo.a110123_invoicerep',           'Invoice Report'),
    ('a110123','LOGBAL2',              'dbo.a110123_logbal2',              'Logistics Balance'),
    ('a110123','ORDERS',               'dbo.a110123_orders',               'Sales Orders'),
    ('a110123','PART',                 'dbo.a110123_part',                 'Parts / Items'),
    ('a110123','PARTSPEC',             'dbo.a110123_partspec',             'Part Specifications'),
    ('a110123','PORDERS',              'dbo.a110123_porders',              'Purchase Orders'),
    ('a110123','PURCHASEINVOICEITEMS', 'dbo.a110123_purchaseinvoiceitems', 'Purchase Invoice Items'),
    ('a110123','SALESINVOICEITEMS',    'dbo.a110123_salesinvoiceitems',    'Sales Invoice Items'),
    ('a110123','TRIALBAL',             'dbo.a110123_trialbal',             'Trial Balance'),
    ('a110123','UNIT',                 'dbo.a110123_unit',                 'Units of Measure'),
    ('a110123','WAREHOUSES',           'dbo.a110123_warehouses',           'Warehouses'),
    ('a110123','WARHSBAL',             'dbo.a110123_warhsbal',             'Warehouse Balance'),

    -- ── tiltan ───────────────────────────────────────────────
    ('tiltan','AGENTS',               'dbo.tiltan_agents',               'Agents'),
    ('tiltan','ACCOUNTS',             'dbo.tiltan_accounts',             'Accounts'),
    ('tiltan','AINVOICES',            'dbo.tiltan_ainvoices',            'AR Invoices'),
    ('tiltan','CINVOICES',            'dbo.tiltan_cinvoices',            'Credit Invoices'),
    ('tiltan','CUSTOMERS',            'dbo.tiltan_customers',            'Customers'),
    ('tiltan','DOCUMENTS_D',          'dbo.tiltan_documents_d',          'Documents Detail'),
    ('tiltan','FAMILYTYPES',          'dbo.tiltan_familytypes',          'Family Types'),
    ('tiltan','FAMILY_LOG',           'dbo.tiltan_family_log',           'Family Log'),
    ('tiltan','FNCITEMS',             'dbo.tiltan_fncitems',             'Finance Items'),
    ('tiltan','FNCTRANS',             'dbo.tiltan_fnctrans',             'Finance Transactions'),
    ('tiltan','GENINVOICES',          'dbo.tiltan_geninvoices',          'General Invoices'),
    ('tiltan','INVOICEREP',           'dbo.tiltan_invoicerep',           'Invoice Report'),
    ('tiltan','LOGBAL2',              'dbo.tiltan_logbal2',              'Logistics Balance'),
    ('tiltan','ORDERS',               'dbo.tiltan_orders',               'Sales Orders'),
    ('tiltan','PART',                 'dbo.tiltan_part',                 'Parts / Items'),
    ('tiltan','PARTSPEC',             'dbo.tiltan_partspec',             'Part Specifications'),
    ('tiltan','PORDERS',              'dbo.tiltan_porders',              'Purchase Orders'),
    ('tiltan','PURCHASEINVOICEITEMS', 'dbo.tiltan_purchaseinvoiceitems', 'Purchase Invoice Items'),
    ('tiltan','SALESINVOICEITEMS',    'dbo.tiltan_salesinvoiceitems',    'Sales Invoice Items'),
    ('tiltan','TRIALBAL',             'dbo.tiltan_trialbal',             'Trial Balance'),
    ('tiltan','UNIT',                 'dbo.tiltan_unit',                 'Units of Measure'),
    ('tiltan','WAREHOUSES',           'dbo.tiltan_warehouses',           'Warehouses'),
    ('tiltan','WARHSBAL',             'dbo.tiltan_warhsbal',             'Warehouse Balance'),

    -- ── nimbos ───────────────────────────────────────────────
    ('nimbos','AGENTS',               'dbo.nimbos_agents',               'Agents'),
    ('nimbos','ACCOUNTS',             'dbo.nimbos_accounts',             'Accounts'),
    ('nimbos','AINVOICES',            'dbo.nimbos_ainvoices',            'AR Invoices'),
    ('nimbos','CINVOICES',            'dbo.nimbos_cinvoices',            'Credit Invoices'),
    ('nimbos','CUSTOMERS',            'dbo.nimbos_customers',            'Customers'),
    ('nimbos','DOCUMENTS_D',          'dbo.nimbos_documents_d',          'Documents Detail'),
    ('nimbos','FAMILYTYPES',          'dbo.nimbos_familytypes',          'Family Types'),
    ('nimbos','FAMILY_LOG',           'dbo.nimbos_family_log',           'Family Log'),
    ('nimbos','FNCITEMS',             'dbo.nimbos_fncitems',             'Finance Items'),
    ('nimbos','FNCTRANS',             'dbo.nimbos_fnctrans',             'Finance Transactions'),
    ('nimbos','GENINVOICES',          'dbo.nimbos_geninvoices',          'General Invoices'),
    ('nimbos','INVOICEREP',           'dbo.nimbos_invoicerep',           'Invoice Report'),
    ('nimbos','LOGBAL2',              'dbo.nimbos_logbal2',              'Logistics Balance'),
    ('nimbos','ORDERS',               'dbo.nimbos_orders',               'Sales Orders'),
    ('nimbos','PART',                 'dbo.nimbos_part',                 'Parts / Items'),
    ('nimbos','PARTSPEC',             'dbo.nimbos_partspec',             'Part Specifications'),
    ('nimbos','PORDERS',              'dbo.nimbos_porders',              'Purchase Orders'),
    ('nimbos','PURCHASEINVOICEITEMS', 'dbo.nimbos_purchaseinvoiceitems', 'Purchase Invoice Items'),
    ('nimbos','SALESINVOICEITEMS',    'dbo.nimbos_salesinvoiceitems',    'Sales Invoice Items'),
    ('nimbos','TRIALBAL',             'dbo.nimbos_trialbal',             'Trial Balance'),
    ('nimbos','UNIT',                 'dbo.nimbos_unit',                 'Units of Measure'),
    ('nimbos','WAREHOUSES',           'dbo.nimbos_warehouses',           'Warehouses'),
    ('nimbos','WARHSBAL',             'dbo.nimbos_warhsbal',             'Warehouse Balance')

) AS v(tenant, endpoint, target_table, description)
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.etl_api_config e
    WHERE e.tenant = v.tenant AND e.endpoint = v.endpoint
);

-- Verify
SELECT tenant, COUNT(*) AS endpoint_count
FROM dbo.etl_api_config
GROUP BY tenant
ORDER BY tenant;
