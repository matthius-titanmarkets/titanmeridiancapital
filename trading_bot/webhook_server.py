"""
TradingView Webhook Receiver
============================
Runs a lightweight Flask server that accepts POST alerts from TradingView
Pine Script strategies and converts them into Signal objects queued for
the main bot loop.

Expected JSON payload from TradingView:
{
  "secret":    "<WEBHOOK_SECRET env var>",
  "symbol":    "EURUSD",
  "action":    "BUY",          // BUY | SELL | CLOSE
  "price":     1.0850,
  "sl":        1.0820,
  "tp":        1.0920
}

Run standalone:
  python3 webhook_server.py

Or import and call start_webhook_server(queue) from bot.py.
"""
from __future__ import annotations

import logging
import os
import queue
import sys
from datetime import datetime, timezone

from flask import Flask, request, jsonify

import config as cfg
from signals import Signal

logger = logging.getLogger(__name__)

app = Flask(__name__)
_signal_queue: queue.Queue[Signal] | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_secret() -> str | None:
    return os.environ.get(cfg.WEBHOOK_SECRET_ENV_VAR)


def _direction_from_action(action: str) -> str | None:
    action = action.upper()
    if action in ("BUY", "LONG"):
        return "LONG"
    if action in ("SELL", "SHORT"):
        return "SHORT"
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "ts": datetime.now(timezone.utc).isoformat()})


@app.route("/webhook", methods=["POST"])
def webhook():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True) or {}

    # Validate secret token if configured
    expected_secret = _get_secret()
    if expected_secret:
        if data.get("secret") != expected_secret:
            logger.warning(
                "Webhook received with invalid secret from %s", request.remote_addr
            )
            return jsonify({"error": "Unauthorized"}), 401

    # Parse required fields
    symbol = str(data.get("symbol", "")).upper().replace("/", "").replace("-", "")
    action = str(data.get("action", ""))
    price  = data.get("price")
    sl     = data.get("sl")
    tp     = data.get("tp")

    if not symbol:
        return jsonify({"error": "Missing 'symbol'"}), 400

    # CLOSE action — bot will handle it via state
    if action.upper() == "CLOSE":
        logger.info("Webhook CLOSE signal for %s", symbol)
        if _signal_queue is not None:
            # Sentinel: a Signal with direction=None means close
            _signal_queue.put(Signal(
                symbol=symbol,
                direction="CLOSE",  # type: ignore
                entry_price=float(price or 0),
                stop_loss=0.0,
                take_profit=0.0,
                timestamp=datetime.now(timezone.utc),
            ))
        return jsonify({"status": "queued", "action": "CLOSE", "symbol": symbol})

    direction = _direction_from_action(action)
    if direction is None:
        return jsonify({"error": f"Unknown action '{action}'. Use BUY/SELL/CLOSE."}), 400

    if price is None or sl is None or tp is None:
        return jsonify({"error": "Missing 'price', 'sl', or 'tp'"}), 400

    signal = Signal(
        symbol=symbol,
        direction=direction,
        entry_price=float(price),
        stop_loss=float(sl),
        take_profit=float(tp),
        timestamp=datetime.now(timezone.utc),
    )
    logger.info("Webhook signal received: %s", signal)

    if _signal_queue is not None:
        _signal_queue.put(signal)
        return jsonify({"status": "queued", "signal": str(signal)})

    return jsonify({"status": "received (no queue attached — standalone mode)"}), 200


@app.route("/test", methods=["POST"])
def test_signal():
    """
    Convenience endpoint for testing without a TradingView account.
    Accepts the same payload as /webhook but skips the secret check.
    Only available when WEBHOOK_SECRET is not set.
    """
    if _get_secret():
        return jsonify({"error": "Test endpoint disabled when WEBHOOK_SECRET is set"}), 403

    data = request.get_json(silent=True) or {}
    symbol    = str(data.get("symbol", "EURUSD")).upper()
    direction = _direction_from_action(str(data.get("action", "BUY"))) or "LONG"
    price     = float(data.get("price", 1.085))
    sl        = float(data.get("sl",    1.082))
    tp        = float(data.get("tp",    1.092))

    signal = Signal(symbol, direction, price, sl, tp, datetime.now(timezone.utc))
    logger.info("Test signal injected: %s", signal)

    if _signal_queue is not None:
        _signal_queue.put(signal)

    return jsonify({"status": "test signal queued", "signal": str(signal)})


# ── Public API ─────────────────────────────────────────────────────────────────

def start_webhook_server(signal_queue: queue.Queue[Signal]) -> None:
    """
    Start the Flask webhook server in a daemon thread.
    Call this from bot.py before the main loop.
    """
    import threading
    global _signal_queue
    _signal_queue = signal_queue

    def _run():
        logger.info(
            "Webhook server starting on %s:%d",
            cfg.WEBHOOK_HOST, cfg.WEBHOOK_PORT,
        )
        app.run(
            host=cfg.WEBHOOK_HOST,
            port=cfg.WEBHOOK_PORT,
            debug=False,
            use_reloader=False,
        )

    t = threading.Thread(target=_run, daemon=True, name="webhook-server")
    t.start()
    logger.info("Webhook server thread started.")


# ── Standalone entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    )

    # Standalone: signals are just logged, not forwarded
    dummy_q: queue.Queue[Signal] = queue.Queue()
    _signal_queue = dummy_q
    logger.info("Running webhook server standalone (signals will be logged only).")
    app.run(
        host=cfg.WEBHOOK_HOST,
        port=cfg.WEBHOOK_PORT,
        debug=True,
        use_reloader=False,
    )
