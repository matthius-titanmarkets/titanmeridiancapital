# Titan Markets LLC — Trading Bot

Automated MACD + Bollinger Bands bot for FX, Gold, and Indices.
Executes via Interactive Brokers (paper first, live after 10% profit).
Integrates with TradingView via Pine Script + webhooks.

---

## Architecture

```
trading_bot/
├── config.py           ← all tuneable parameters
├── signals.py          ← MACD + BB + session filter
├── broker.py           ← ib_insync wrapper (paper / live)
├── risk_manager.py     ← position sizing, daily loss limits, drawdown guard
├── state_manager.py    ← persistent JSON state (bot_state.json)
├── bot.py              ← main event loop (entry point)
├── webhook_server.py   ← Flask server for TradingView alerts
├── requirements.txt
└── pine_script/
    └── strategy.pine   ← TradingView Pine Script strategy
```

---

## Setup

### 1. Install dependencies

```bash
cd trading_bot
pip install -r requirements.txt
```

### 2. Configure Interactive Brokers

1. Open **TWS** or **IB Gateway**
2. Go to **File → Global Configuration → API → Settings**
3. Check **Enable ActiveX and Socket Clients**
4. Set **Socket port** to `7497` (paper) or `7496` (live)
5. Uncheck **Read-Only API**
6. Add `127.0.0.1` to trusted IPs

### 3. (Optional) Set webhook secret

```bash
export WEBHOOK_SECRET="your-random-secret-here"
```

Replace `YOUR_SECRET` in `pine_script/strategy.pine` with the same value.

---

## Running

### Paper trading (default)

```bash
python3 bot.py --paper
```

### Full simulation (no IB needed — for testing)

```bash
python3 bot.py --sim
```

### Re-initialise NAV from PropFirm data

```bash
python3 bot.py --paper --reset
```

### Live trading (after 10% target confirmed)

```bash
python3 bot.py --live
```

---

## Terminal commands (while bot is running)

| Command        | Action                                         |
|----------------|------------------------------------------------|
| `status`       | Show current NAV, mode, open positions         |
| `confirm live` | Switch to live (requires 10% target reached)   |
| `force live`   | Switch to live without target (with warning)   |
| `stop`         | Gracefully stop the bot                        |
| `help`         | Show this list                                 |

---

## TradingView Integration (requires Pro plan)

### Step 1 — Load the Pine Script

1. Open TradingView → **Pine Script Editor**
2. Paste the contents of `pine_script/strategy.pine`
3. Click **Add to chart** on your symbol/timeframe (5m recommended)

### Step 2 — Expose your webhook server

Your bot must be reachable from the internet.  Options:
- **ngrok** (easiest for testing): `ngrok http 5001` → copy the HTTPS URL
- **VPS / cloud server**: expose port 5001 publicly
- **Home router**: port-forward 5001 to your machine

### Step 3 — Create TradingView alert

1. Right-click on the chart → **Add Alert**
2. **Condition**: select the script → `alert() function calls only`
3. **Webhook URL**: `https://<your-public-url>/webhook`
4. **Message**: leave blank (the Pine Script builds the JSON payload)
5. **Expiration**: set to your preferred duration

### Step 4 — Test the webhook

```bash
curl -X POST http://localhost:5001/test \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","action":"BUY","price":1.085,"sl":1.082,"tp":1.092}'
```

---

## Paper → Live switching

The bot automatically detects when its NAV reaches **10% above starting NAV**
(derived from your PropFirm data). When triggered:

1. A prominent message prints in the terminal
2. The dashboard **Bot tab** shows a confirmation button
3. Type `confirm live` in the terminal to activate

The bot reconnects to IB on the live port (7496) and continues trading.

---

## Configuration

All parameters are in `config.py`:

| Parameter              | Default  | Description                              |
|------------------------|----------|------------------------------------------|
| `RISK_PER_TRADE_PCT`   | 0.01     | 1% of NAV risked per trade               |
| `TAKE_PROFIT_RR`       | 2.5      | 2.5:1 reward-to-risk ratio               |
| `MAX_POSITIONS`        | 3        | Max concurrent open positions            |
| `DAILY_LOSS_LIMIT_PCT` | 0.02     | 2% daily loss limit (pauses bot)         |
| `MAX_DRAWDOWN_PCT`     | 0.05     | 5% drawdown kill-switch                  |
| `LIVE_THRESHOLD`       | 0.10     | 10% profit → prompt for live switch      |
| `BAR_SIZE`             | "5 mins" | IB bar size for signal generation        |
| `MACD_FAST/SLOW/SIGNAL`| 12/26/9  | Standard MACD parameters                 |
| `BB_WINDOW`            | 20       | Bollinger Band period                    |
| `BB_NUM_STD`           | 2.0      | Bollinger Band standard deviations       |
| `SL_ATR_BUFFER`        | 0.5      | ATRs beyond BB for stop loss             |

---

## Dashboard

The **Bot tab** in the main Streamlit dashboard shows live bot status:

```bash
cd ..
python3 -m streamlit run dashboard.py
```

The Bot tab reads `bot_state.json` — no direct connection to the bot process needed.

---

## Risk Warnings

- Always test in **paper/simulation mode** before going live
- The bot trades real financial instruments — losses are possible
- The 10% target is a guideline, not a guarantee of future performance
- Never risk more than you can afford to lose
- Review `config.py` risk parameters before running in live mode
