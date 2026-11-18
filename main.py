"""Deep-drawdown breakout rider for make.fun btc-race-24h-20261118-1444.

Strategy (long-only, one asset CBBTC, 1-minute bars):
  A 24h BTC day is mostly noise at 1-minute scale (typical 1-min move ~7 bps)
  while a full round trip costs ~26 bps in fees, slippage and price impact.
  Frequent trading therefore bleeds money on this market: on the published
  dev window every mean-reversion, RSI, EMA-cross and Donchian variant I
  tested lost money, and the kit's own RSI-Bollinger baseline lost ~$40.
  The only durable edge in the data is the rare large intraday swing: a
  deep drawdown followed by a confirmed recovery rally (the dev window's
  one big move was a -2.0% slide, a flat base, then a +1.9% rally over
  ~4 hours). So this bot trades rarely and only for that shape:

  ENTRY (flat only): the close is at least 1.7% below the session high so
  far AND breaks above the highest close of the previous 90 bars. The
  first condition says a real drawdown happened; the second says buyers
  have stepped back in and the base is breaking upward, not that we are
  catching a falling knife. Full cash is deployed (max_weight is 100%).

  EXIT (holding): a 0.7% trailing stop from the highest close since entry,
  or a 0.8% hard stop below the fill price. The trailing stop is wide
  enough to survive ordinary 1-minute noise and the mid-rally pullbacks,
  but tight enough to bank most of a rally instead of riding it back down.

  Nothing else trades. No re-entry chasing, no counter-trend dip buying,
  no time-of-day rules (those would overfit one day's clock). On the
  published dev window this makes exactly one round trip: +$9.64 net on
  $1,000, max drawdown ~1.0%, 2 fills. If the live window offers no
  deep-drawdown breakout, the bot stays flat at $0 rather than bleeding
  fees in chop -- a flat $0 still outranks every bot that loses money.

  Determinism: only closes and counters are used. No clock, no random,
  no environment, no network. Two runs produce byte-identical replies.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
# A drawdown of this size from the session high arms the entry.
DRAWDOWN_PCT = 0.017
# Breakout lookback: close must beat the highest close of the last N bars.
BREAKOUT_BARS = 90
# Trailing stop from the highest close since entry.
TRAIL_PCT = 0.007
# Hard stop below the entry fill price.
STOP_PCT = 0.008
# Slippage cap on every order, in bps (1-minute gaps are tiny; 100 bps is ample).
MAX_SLIPPAGE_BPS = 100
# Bars of cooling-off after an exit before a new entry may be taken.
COOLDOWN_BARS = 60


class Rider:
    """One position at a time: flat, or long CBBTC riding a recovery."""

    def __init__(self):
        self.closes = []          # closes so far, raw price units (ints)
        self.peak = None          # highest close since entry, raw units
        self.entry_price = None   # fill price of the current position
        # Bar index before which no new entry is taken. Set on every exit:
        # a trailing-stop exit means the rally is fading, so buying back
        # into the same fade on the next breakout would be a whipsaw.
        # Sixty bars of cooling-off costs nothing when a real new setup
        # needs a fresh drawdown and breakout to form anyway.
        self.cooldown_until = -1

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        idx = len(self.closes) - 1
        held = state.positions.get(SYMBOL)

        if held is not None and held.qty > 0:
            if self.peak is None or close > self.peak:
                self.peak = close
            if self.entry_price is None:
                self.entry_price = close
            # Trailing stop: give back at most TRAIL_PCT from the peak.
            if close < self.peak * (1 - TRAIL_PCT):
                return self._sell_all(state, idx)
            # Hard stop below the entry price.
            if close < self.entry_price * (1 - STOP_PCT):
                return self._sell_all(state, idx)
            return []

        # Flat: reset tracking and look for the setup.
        self.peak = None
        self.entry_price = None
        if idx < self.cooldown_until:
            return []
        if len(self.closes) < BREAKOUT_BARS + 1:
            return []
        session_high = max(self.closes)
        if (session_high - close) / session_high < DRAWDOWN_PCT:
            return []
        range_high = max(self.closes[-BREAKOUT_BARS - 1:-1])
        if close <= range_high:
            return []
        # Deep drawdown + breakout: deploy all cash.
        if state.cash < 1_000_000:  # below the $1 minimum notional
            return []
        return [{
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": state.cash,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    def _sell_all(self, state, idx):
        held = state.positions.get(SYMBOL)
        if held is None or held.qty <= 0:
            return []
        self.peak = None
        self.entry_price = None
        self.cooldown_until = idx + COOLDOWN_BARS
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": held.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]


def main():
    rider = Rider()
    makefun_bars.run(rider.on_batch)


if __name__ == "__main__":
    main()
