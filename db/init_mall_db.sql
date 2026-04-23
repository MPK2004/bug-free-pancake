-- Phase 1: Clear legacy data and define core business intelligence schema

-- Drop tables if they exist (for clean redeploy)
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS category_insights CASCADE;
DROP TABLE IF EXISTS proposals CASCADE;
DROP TABLE IF EXISTS rental_agreements CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;
DROP TABLE IF EXISTS malls CASCADE;
DROP TABLE IF EXISTS news CASCADE;

-- Create core tables
CREATE TABLE malls (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- e.g., 'Clothing', 'Shoes', 'Technology'
    brand_type TEXT NOT NULL -- e.g., 'Premium', 'Mass', 'Luxury'
);

CREATE TABLE rental_agreements (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    mall_id INT REFERENCES malls(id),
    base_rent FLOAT NOT NULL,
    revenue_share_percentage FLOAT DEFAULT 0.0,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'Active'
);

CREATE TABLE proposals (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    mall_id INT REFERENCES malls(id),
    proposed_rent FLOAT NOT NULL,
    expected_sales FLOAT NOT NULL,
    expected_yield FLOAT GENERATED ALWAYS AS ((proposed_rent / NULLIF(expected_sales, 0)) * 100) STORED
);

CREATE TABLE category_insights (
    category TEXT PRIMARY KEY,
    priority TEXT NOT NULL, -- 'HIGH', 'MEDIUM', 'LOW'
    note TEXT
);

-- Real-world transaction data table
CREATE TABLE transactions (
    invoice_no TEXT PRIMARY KEY,
    customer_id TEXT,
    gender TEXT,
    age INT,
    category TEXT,
    quantity INT,
    price FLOAT,
    payment_method TEXT,
    invoice_date TEXT, -- Stored as text to match CSV format, can be converted later if needed
    shopping_mall TEXT,
    total_sales FLOAT GENERATED ALWAYS AS (quantity * price) STORED
);

-- Optimize for dynamic aggregation
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_mall ON transactions(shopping_mall);
