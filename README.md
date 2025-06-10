# testCodex

This repository contains a simple example script for automatically trading Bitcoin futures on Binance using Python's built-in libraries.

## trade_bot.py

`trade_bot.py` implements a minimal trading bot that:

1. Fetches the current BTC price from Binance futures.
2. Retrieves a basic sentiment indicator from the CoinDesk price API.
3. Decides whether to go long or short based on this sentiment.
4. Places a market order and sets stop loss and take profit orders.

API credentials must be supplied via the environment variables `BINANCE_API_KEY` and `BINANCE_API_SECRET` before running the script.

Run the bot with:

```bash
python trade_bot.py
```

Note that this is a demonstration and does not include advanced error handling or trading logic. Use at your own risk.
