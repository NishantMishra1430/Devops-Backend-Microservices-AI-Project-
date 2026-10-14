-- init.sql
-- Description: Idempotent initialization script for the Quant Trading System

-- 1. Create auxiliary databases if they don't exist (Note: PostgreSQL doesn't support IF NOT EXISTS for databases directly in plain SQL, so we handle it gracefully or use compose)
-- Alternatively, ensure your connection string matches the POSTGRES_DB env variable in docker-compose.yml.

-- 2. Create the primary trades table for the Execution Service
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    amount_usd DECIMAL(12, 2) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Users table for the Auth Service
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization: B-Tree Indexes
-- Optimizes queries filtering by specific assets (e.g., WHERE ticker = 'BTC')
CREATE INDEX IF NOT EXISTS idx_trades_ticker
ON trades USING btree (ticker);

-- Optimizes time-series aggregations (e.g., daily volume, VWAP calculations)
CREATE INDEX IF NOT EXISTS idx_trades_timestamp
ON trades USING btree (timestamp);

-- Index for fast user lookups by email during login
CREATE INDEX IF NOT EXISTS idx_users_email
ON users USING btree (email);
