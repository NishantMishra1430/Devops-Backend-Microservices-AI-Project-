import redis
import argparse
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [RedisBacktester] %(message)s"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
STREAM_NAME = "market:stream:live"

def parse_args():
    parser = argparse.ArgumentParser(description="Redis-backed Backtester / Signal Tester")
    parser.add_argument("--count", type=int, default=100, help="Number of recent ticks to fetch from Redis stream")
    parser.add_argument("--window", type=int, default=5, help="Rolling window size for Z-score")
    parser.add_argument("--threshold", type=float, default=0.5, help="Z-score threshold for signals")
    return parser.parse_args()

def connect_redis():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        logging.critical(f"Failed to connect to Redis: {e}")
        sys.exit(1)

def run_redis_backtester():
    args = parse_args()
    r = connect_redis()

    logging.info(f"Fetching last {args.count} ticks from Redis Stream '{STREAM_NAME}'...")
    
    # XRANGE fetches historical/buffered data from Redis stream
    # '-' to '+' means from the very beginning to the latest in the stream
    messages = r.xrange(STREAM_NAME, count=args.count)

    if not messages:
        logging.warning("No data found in Redis stream! Make sure your producer is running.")
        return

    prices = []
    timestamps = []

    for message_id, data in messages:
        price = data.get("price")
        timestamp = data.get("timestamp") or data.get("time")
        if price:
            prices.append(float(price))
            timestamps.append(timestamp)

    total_ticks = len(prices)
    logging.info(f"Successfully loaded {total_ticks} ticks from Redis cache.")

    if total_ticks < args.window:
        logging.warning(f"Fetched ticks ({total_ticks}) are less than window size ({args.window}). Increase --count or wait for more data.")
        return

    # Simulation & Strategy Execution Loop (Z-Score Mean Reversion)
    trades = 0
    wins = 0
    losses = 0
    cumulative_pnl = 0.0
    capital = 10000.0
    peak_capital = capital
    max_drawdown = 0.0

    position = None  # None, 'BUY', 'SELL'
    entry_price = 0.0

    for i in range(args.window, total_ticks):
        window_slice = prices[i - args.window : i]
        current_price = prices[i]

        mean = sum(window_slice) / args.window
        variance = sum((p - mean) ** 2 for p in window_slice) / args.window
        std_dev = variance ** 0.5

        if std_dev == 0:
            continue

        z_score = (current_price - mean) / std_dev

        # Strategy Logic
        if position is None:
            if z_score < -args.threshold:
                position = 'BUY'
                entry_price = current_price
                trades += 1
                logging.info(f"[BUY] at {entry_price} | Z-Score: {z_score:.2f}")
            elif z_score > args.threshold:
                position = 'SELL'
                entry_price = current_price
                trades += 1
                logging.info(f"[SELL] at {entry_price} | Z-Score: {z_score:.2f}")

        elif position == 'BUY':
            # Mean reversion exit condition (crossing back near mean)
            if z_score >= 0 or i == total_ticks - 1:
                pnl = current_price - entry_price
                cumulative_pnl += pnl
                capital += pnl
                if pnl > 0:
                    wins += 1
                else:
                    losses += 1
                logging.info(f"[EXIT BUY] at {current_price} | PnL: {pnl:.2f}")
                position = None

        elif position == 'SELL':
            if z_score <= 0 or i == total_ticks - 1:
                pnl = entry_price - current_price
                cumulative_pnl += pnl
                capital += pnl
                if pnl > 0:
                    wins += 1
                else:
                    losses += 1
                logging.info(f"[EXIT SELL] at {current_price} | PnL: {pnl:.2f}")
                position = None

        # Track Drawdown
        if capital > peak_capital:
            peak_capital = capital
        drawdown = (peak_capital - capital) / peak_capital * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    win_rate = (wins / trades * 100) if trades > 0 else 0.0

    # Final Report
    print("\n========================================")
    print("      REDIS BACKTEST PERFORMANCE REPORT ")
    print("========================================")
    print(f"Total Ticks Analyzed  : {total_ticks}")
    print(f"Total Trades Executed : {trades}")
    print(f"Win/Loss Ratio        : {win_rate:.2f}% ({wins}W / {losses}L)")
    print(f"Maximum Drawdown (MDD): {max_drawdown:.2f}%")
    print(f"Cumulative PnL        : ${cumulative_pnl:.2f}")
    print(f"Final Capital         : ${capital:.2f}")
    print("========================================\n")

if __name__ == "__main__":
    run_redis_backtester()