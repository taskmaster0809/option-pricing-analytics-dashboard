# VolatilityLens

An interactive options pricing and volatility analytics dashboard built in Python. VolatilityLens prices European options using the Black-Scholes closed-form solution, computes all major Greeks, extracts implied volatility from live market data via numerical inversion, and visualises the volatility smile and surface through an interactive Dash dashboard.

---

## Features

- **Black-Scholes Pricing**: analytical pricing of European call and put options with closed-form Greeks (Delta, Gamma, Vega, Theta, Rho)
- **Monte Carlo Pricing**: GBM-based simulation with antithetic variates variance reduction, available as a method on the `EuropeanOption` class
- **Implied Volatility Extraction**: numerical inversion of the BS formula using Brent's method (`scipy.optimize.brentq`) applied to live options chain data
- **Volatility Smile**: implied vol plotted against strike for a selected expiry, revealing the equity skew
- **Volatility Surface**: 3D surface of implied vol across all strikes and expiries
- **Underlying Price Chart**: 3-month candlestick chart of the underlying asset
- **Greeks Dashboard**: BS Greeks table and Greeks vs strike plot for a selected contract
- **Live Market Data**: Options chain and spot price fetched in real time via `yfinance`; risk-free rate from the 13-week US Treasury Bill (`^IRX`)

---

## Project Structure

```
options-pricing-dashboard/
│
├── pricing/
│   └── black_scholes.py          # EuropeanOption class: BS pricing, Greeks, Monte Carlo
│
├── data/
│   └── market_data.py            # MarketData class: yfinance data fetching and processing
│
├── vol_surface/
│   └── implied_vol.py            # Implied vol inversion and surface DataFrame construction
│
├── dashboard/
│   ├── app.py                    # Dash app layout and callbacks
│   ├── greeks_table.py           # AG Grid Greeks table component
│
└── README.md
```

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/volatilitylens.git
cd volatilitylens
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the dashboard**
```bash
python dashboard/app.py
```

Then open your browser at `http://127.0.0.1:8050`.

---

## Dependencies

```
dash
dash-bootstrap-components
dash-ag-grid
plotly
numpy
scipy
pandas
yfinance
```

---

## Usage

1. Enter a US-listed ticker symbol (e.g. `SPY`, `AAPL`, `QQQ`) in the search bar
2. Click **Search**. The app fetches the options chain and computes the implied volatility surface
3. Select an expiry date from the dropdown
4. Toggle between **Underlying**, **Volatility Smile**, and **Volatility Surface** views
5. Scroll down to the **Greeks Dashboard**, select a strike price, and view the Greeks table or Greeks vs strike plot

---

## Methodology

### Black-Scholes Model

Option prices are computed using the closed-form Black-Scholes formula under the risk-neutral measure. The underlying is assumed to follow Geometric Brownian Motion:

$$dS_t = rS_t \, dt + \sigma S_t \, dW_t$$

Greeks are derived analytically from the closed-form solution.

### Implied Volatility

For each listed option, the market price is observed and the Black-Scholes formula is inverted numerically to find the $\sigma$ that reproduces that price. Brent's method is used for root-finding with bounds $\sigma \in (10^{-9}, 5)$.

### Monte Carlo Pricing

The terminal stock price is simulated under the risk-neutral measure:

$$S_T = S_0 \exp\left(\left(r - \frac{\sigma^2}{2}\right)T + \sigma\sqrt{T}\, Z\right), \quad Z \sim \mathcal{N}(0,1)$$

Antithetic variates are used for variance reduction — each $Z$ is paired with $-Z$ and payoffs are averaged before discounting.

---

## Known Limitations

- **Data quality**: Market prices are sourced from Yahoo Finance `lastPrice`, which reflects the most recent trade and may be stale. The dashboard is most accurate during US market hours (9:30am–4pm EST). For production use, a paid real-time data feed (e.g. Polygon.io, Tradier) is recommended.
- **European options only**: The Black-Scholes model prices European options. American options, which can be exercised early, require different pricing methods (e.g. binomial trees, least-squares Monte Carlo).
- **Model assumptions**: Black-Scholes assumes constant volatility and lognormally distributed returns. The volatility smile visible in the dashboard is direct evidence that these assumptions do not hold in practice. More sophisticated models (Heston, SABR) would address this.
- **US equities only**: Options data coverage on Yahoo Finance is most reliable for US-listed equities and ETFs.

- **Live Updates**: The dashboard does not update data in real-time and needs to be refreshed to reflect latest data.

---