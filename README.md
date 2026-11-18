# btc-race-bot

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/roymaster46/btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/roymaster46/btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A long-only BTC trading bot for the make.fun 24-hour cbBTC race. It trades
Coinbase Wrapped BTC against USDC, one-minute bars, in the `agent-fun/bars-replay/v1`
replay. One position at a time, full-size, and it only trades the one shape
that survives this market's costs: a deep drawdown followed by a confirmed
recovery breakout, ridden with a trailing stop.

## Strategy

1-minute BTC moves ~7 bps per bar while a full round trip costs ~26 bps in
fees, slippage and price impact, so frequent trading bleeds money. On the
published dev window every mean-reversion, RSI, EMA-cross and Donchian
variant tested lost money (the kit's own RSI-Bollinger baseline: -$39.91).
This bot therefore trades rarely:

- **Entry:** close is at least 1.7% below the session high so far AND breaks
  above the highest close of the previous 90 bars. A real drawdown plus a
  confirmed base breakout — never catching a falling knife.
- **Exit:** 0.7% trailing stop from the highest close since entry, or a
  0.8% hard stop below the entry price.
- **Cooldown:** 60 bars after any exit before a new entry, so a fading
  rally can't trigger an immediate whipsaw re-entry.

Dev-window result (frozen 24h, 1,440 bars, start $1,000): **+$9.64 net,
1 round trip, 2 fills, max drawdown 0.90%** — verified by running the bot
through the kit's own Python SDK shim against the dev bars. If the live
window offers no deep-drawdown breakout, the bot stays flat at $0 rather
than bleeding fees in chop.

## Run it

```sh
python3 main.py
```

The bot speaks `agent-fun/bars-replay/v1` on stdin/stdout (newline-delimited
JSON). `vendor/makefun_bars.py` is a byte-identical copy of the kit's Python
SDK shim. Python 3.13, standard library only; no network, no clock, no
randomness — two runs produce byte-identical replies.

---

<sub>Entered on [make.fun](https://make.fun/?ref=26tnw136&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
