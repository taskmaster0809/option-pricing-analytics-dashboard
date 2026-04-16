from datetime import datetime as dt

import yfinance as yf
from scipy.optimize import brentq
import numpy as np

from pricing.black_scholes import EuropeanOption

TODAY = dt.today()

ticker = yf.Ticker("SPY") # State Street SPDR S&P 500 ETF Trust
expiries = ticker.options # Option expiries available

date_list = []

for expiry in expiries:
    day_diff = (dt.strptime(expiry, "%Y-%m-%d") - TODAY).days
    if 70 <= day_diff <= 90: # Option expiry between 90 and 120 days from now
        date_list.append(expiry)

date = date_list[0]
option_chain = ticker.option_chain(date)

spot = ticker.history(period="1d")["Close"].iloc[-1] # Spot price of underlying: S in Black Scholes model
print(f"Spot price: ${spot:.2f}")

calls = option_chain.calls[["strike", "lastPrice", "impliedVolatility"]]
calls = calls[(0.85 * spot <= calls["strike"]) & (calls["strike"] <= 1.15 * spot) & (calls["lastPrice"] >= 1)] # Filtering out stale prices
calls.reset_index(drop=True, inplace=True)

print(f"\nCalls:\n{calls}")

tnx = yf.Ticker("^TNX")
interest_rate = tnx.history(period="1d")["Close"].iloc[-1]/100
print(f"Current 10-Year Treasury Yield: {interest_rate}\n")                # Risk-free interest rate: r in the Black Scholes model

time_to_expiry = (dt.strptime(date, "%Y-%m-%d") - TODAY).days/365 # Time to expiry in years: T in Black Scholes Model
print(f"Time to expiry: {time_to_expiry * 365:.0f} days\n")


def helper(implied_vol, row):
    option = EuropeanOption(spot, row.strike, time_to_expiry, interest_rate, implied_vol)
    return option.call_price() - row.lastPrice


strike_vol = []
for _, data_row in calls.iterrows():
    try:
        imp_vol = brentq(f=helper, a=1e-9, b=5, args=(data_row, ))
        strike_vol.append((data_row.strike, imp_vol))
    except ValueError:
        strike_vol.append((data_row.strike, np.nan))

print(strike_vol)