from datetime import datetime as dt

from scipy.optimize import brentq
import numpy as np
import pandas as pd

from pricing.black_scholes import EuropeanOption
from data.market_data import MarketData


def get_strike_vol_df(market_data: MarketData):
    """
    Takes a MarketData object and returns a dataframe containing strike and implied volatility for various expiry dates
    for the corresponding call options
    """
    def helper(implied_vol, row, time):
        option = EuropeanOption(market_data.spot, row.strike, time, market_data.interest_rate, implied_vol)
        return option.call_price() - row.marketPrice

    strike_vol = []
    for date in market_data.expiries:
        # Time to expiry in years: T in Black Scholes Model
        time_to_expiry = (dt.strptime(date,"%Y-%m-%d") - market_data.today).days / 365.25

        calls = market_data.get_calls(date)

        for _, data_row in calls.iterrows():
            try:
                imp_vol = brentq(f=helper, a=1e-9, b=5, args=(data_row, time_to_expiry)) # Solve for root of helper
                strike_vol.append((data_row.strike, imp_vol, time_to_expiry))
            except ValueError:
                strike_vol.append((data_row.strike, np.nan, time_to_expiry))             # When no solution exists

    strike_vol_df = pd.DataFrame(strike_vol, columns=["strike", "implied_vol", "time_to_expiry"])
    strike_vol_df = strike_vol_df.dropna().reset_index(drop=True)
    return strike_vol_df
