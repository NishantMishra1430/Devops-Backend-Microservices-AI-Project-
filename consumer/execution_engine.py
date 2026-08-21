import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List
import redis.asyncio as redis
import aio_pika  # 🚀 Added async RabbitMQ client

# Enforce strict standard logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [Execution] %(message)s")
logger = logging.getLogger("execution-engine")

# --- Domain Models ---
@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: float
    side: str  # 'LONG' or 'SHORT'
    stop_loss: float
    take_profit: float

@dataclass
class TradeRecord:
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    realized_pnl: float

class PortfolioState:
    def __init__(self, initial_cash: float = 10000.0):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.history: List[TradeRecord] = []

    def total_value(self, current_prices: Dict[str, float]) -> float:
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.entry_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value

# --- Risk Management Module ---
class RiskManager:
    def __init__(self, max_allocation_pct: float = 0.10, sl_pct: float = 0.02, tp_pct: float = 0.05):
        self.max_allocation_pct = max_allocation_pct
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct

    def calculate_position_size(self, current_price: float, portfolio: PortfolioState) -> float:
        total_capital = portfolio.total_value({})
        max_fiat_allocation = total_capital * self.max_allocation_pct
        actual_fiat_allocation = min(max_fiat_allocation, portfolio.cash)
        return actual_fiat_allocation / current_price if current_price > 0 else 0

    def calculate_sl_tp(self, entry_price: float, side: str) -> tuple[float, float]:
        if side == 'LONG':
            return entry_price * (1 - self.sl_pct), entry_price * (1 + self.tp_pct)
        else:
            return entry_price * (1 + self.sl_pct), entry_price * (1 - self.tp_pct)

# --- Core Execution Engine ---
class ExecutionEngine:
    def __init__(self, rmq_channel: aio_pika.RobustChannel):
        self.portfolio = PortfolioState(initial_cash=10000.0)
        self.risk_manager = RiskManager()
        self.current_prices: Dict[str, float] = {}
        self.rmq_channel = rmq_channel  # Inject RabbitMQ Channel

    async def publish_event(self, payload: dict):
        """Sends trade events to RabbitMQ for Notification Service"""
        if not self.rmq_channel:
            return

        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await self.rmq_channel.default_exchange.publish(
            message,
            routing_key="trade_events" # Matches Node.js consumer QUEUE_NAME
        )
        logger.info(f"Event published to RabbitMQ -> {payload}")

    async def process_signal(self, payload: dict):
        symbol = payload.get("symbol", "BTCUSDT")
        signal = payload.get("action")  

        try:
            current_price = float(payload.get("price", 0.0))
        except ValueError:
            current_price = 0.0

        if current_price <= 0:
            return

        self.current_prices[symbol] = current_price
        await self.check_exit_conditions(symbol, current_price)

        if signal == "BUY" and symbol not in self.portfolio.positions:
            await self.execute_entry(symbol, current_price, "LONG")
        elif signal == "SELL" and symbol not in self.portfolio.positions:
             await self.execute_entry(symbol, current_price, "SHORT")

    async def execute_entry(self, symbol: str, price: float, side: str):
        qty = self.risk_manager.calculate_position_size(price, self.portfolio)
        if qty <= 0:
            return

        cost_basis = qty * price
        self.portfolio.cash -= cost_basis
        sl, tp = self.risk_manager.calculate_sl_tp(price, side)

        self.portfolio.positions[symbol] = Position(
            symbol=symbol, entry_price=price, quantity=qty, side=side, stop_loss=sl, take_profit=tp
        )
        logger.info(f"OPEN {side} | {symbol} | Qty: {qty:.4f} | Entry: ${price:.2f}")

        await self.publish_event({
            "ticker": symbol,
            "action": f"OPEN_{side}",
            "amount_usd": round(cost_basis, 2)
        })

    async def check_exit_conditions(self, symbol: str, current_price: float):
        if symbol not in self.portfolio.positions:
            return

        pos = self.portfolio.positions[symbol]
        close_reason = None

        if pos.side == 'LONG':
            if current_price <= pos.stop_loss: close_reason = "STOP-LOSS"
            elif current_price >= pos.take_profit: close_reason = "TAKE-PROFIT"
        elif pos.side == 'SHORT':
            if current_price >= pos.stop_loss: close_reason = "STOP-LOSS"
            elif current_price <= pos.take_profit: close_reason = "TAKE-PROFIT"

        if close_reason:
            await self.execute_exit(symbol, current_price, close_reason)

    async def execute_exit(self, symbol: str, exit_price: float, reason: str):
        pos = self.portfolio.positions.pop(symbol)

        pnl = (exit_price - pos.entry_price) * pos.quantity if pos.side == 'LONG' else (pos.entry_price - exit_price) * pos.quantity
        capital_returned = (pos.entry_price * pos.quantity) + pnl
        self.portfolio.cash += capital_returned

        self.portfolio.history.append(TradeRecord(
            symbol=symbol, side=pos.side, entry_price=pos.entry_price,
            exit_price=exit_price, quantity=pos.quantity, realized_pnl=pnl
        ))

        logger.info(f"CLOSE {pos.side} ({reason}) | {symbol} | Exit: ${exit_price:.2f} | PnL: ${pnl:.2f}")

        await self.publish_event({
            "ticker": symbol,
            "action": f"CLOSE_{pos.side}_{reason}",
            "amount_usd": round(capital_returned, 2)
        })

# --- Main Ingestion Loop with Retry Logic ---
async def consume_signals():
    redis_url = os.getenv("REDIS_URL")
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    
    if not redis_url or not rabbitmq_url:
        logger.fatal("REDIS_URL and RABBITMQ_URL are strictly required.")
        exit(1)

    redis_client = redis.from_url(redis_url, decode_responses=True)

    # RabbitMQ Connection with Fault-Tolerant Retry Loop
    retries = 5
    # RabbitMQ Connection with Infinite Robust Retry Loop
    rmq_connection = None
    while rmq_connection is None:
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            rmq_connection = await aio_pika.connect_robust(rabbitmq_url)
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            logger.warning(f"RabbitMQ not ready yet ({e}), retrying in 5 seconds...")
            await asyncio.sleep(5)

    rmq_channel = await rmq_connection.channel()
    await rmq_channel.declare_queue("trade_events", durable=True)

    stream_key = 'market:stream:signals'
    last_id = '$'

    engine = ExecutionEngine(rmq_channel=rmq_channel)
    logger.info(f"Execution Engine online. Listening to {stream_key} (Redis) & publishing to trade_events (RabbitMQ)...")

    try:
        while True:
            events = await redis_client.xread({stream_key: last_id}, count=5, block=5000)
            if not events:
                continue

            for stream_name, messages in events:
                for message_id, data in messages:
                    last_id = message_id
                    await engine.process_signal(data)

    except asyncio.CancelledError:
        logger.info("Process cancelled.")
    except Exception as e:
        logger.error(f"[Fatal] Execution process failure: {e}")
    finally:
        await redis_client.aclose()
        await rmq_connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(consume_signals())
    except KeyboardInterrupt:
        logger.info("Shutting down Execution Engine.")
