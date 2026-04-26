from datetime import datetime as dt
import yfinance as yf


class MarketData:
    def __init__(self, ticker: str):
        self.today = dt.today()
        self.ticker = yf.Ticker(ticker)
        self.expiries = self.ticker.options  # Option expiries available

        # Spot price of underlying: S in Black Scholes model
        self.spot = self.ticker.history(period="1d")["Close"].iloc[-1]

        irx = yf.Ticker("^IRX")
        # US 13 Week Treasury Bill: r in the Black Scholes model
        self.interest_rate = irx.history(period="1d")["Close"].iloc[-1] / 100

        self.metadata = self.ticker.get_history_metadata()

    def get_calls(self, date: str):
        if date not in self.expiries:
            raise ValueError("Date must be in the list of expiries")

        option_chain = self.ticker.option_chain(date)

        calls = option_chain.calls[["strike", "lastPrice", "ask", "bid"]]
        calls = calls[ (0.85 * self.spot <= calls["strike"]) &
                       (calls["strike"] <= 1.15 * self.spot) ] # Filtering out stale prices
        calls.reset_index(drop=True, inplace=True)

        zero_bid_ask = calls[ (calls["ask"] == 0) | (calls["bid"] == 0) ]
        if len(zero_bid_ask) >= 0.5 * len(calls):
            calls["marketPrice"] = calls["lastPrice"]  # Set last price as the market price in case of illiquid options
        else:
            calls = calls[ (calls["ask"] > 0) & (calls["bid"] > 0) ]
            calls["marketPrice"] = calls["ask"].add(calls["bid"])/2  # Otherwise set them to ask-bid midpoint

        # Cleaning data
        calls = calls[calls["marketPrice"] > 0]
        calls = calls.dropna(subset=["marketPrice"])
        calls.reset_index(drop=True, inplace=True)
        return calls[["strike", "marketPrice"]]
