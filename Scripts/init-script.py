from pathlib import Path

main = Path("init-scripts")
init = main / "init.sql"

if not main.exists():
    main.mkdir(parents=True)
    print(f"Created {main} folder...")
else:
    print("Checking for {init} file...") 
init_content = """-- init.sql
-- Database: quanttrade
-- Description: Idempotent initialization script for the Execution Service.

-- Create the primary trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    amount_usd DECIMAL(12, 2) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization: B-Tree Indexes
-- Optimizes queries filtering by specific assets (e.g., WHERE ticker = 'BTC')
CREATE INDEX IF NOT EXISTS idx_trades_ticker 
ON trades USING btree (ticker);

-- Optimizes time-series aggregations (e.g., daily volume, VWAP calculations)
CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
ON trades USING btree (timestamp);"""

if not init.exists():
    init.touch()
    init.write_text(init_content)
    print(f"Created a {init} file inside {main} folder...")
else:
    print(f"{init} file is already existing...")
    
print(f"Task Successfully completed...")