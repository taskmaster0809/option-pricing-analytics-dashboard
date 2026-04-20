from datetime import datetime as dt

from dash import Dash, html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from data.market_data import MarketData
from vol_surface.implied_vol import get_strike_vol_df

HIDE_STYLE = {"display": "none"}

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

market_data_cache = {}
strike_vol_df_cache = {}


def get_market_data(symbol) -> MarketData: # Used to store market data in cache
    if symbol not in market_data_cache:
        market_data_cache[symbol] = MarketData(symbol)
    return market_data_cache[symbol]


def market_vol_df_store(symbol): # Used to store the implied vol data in cache
    if symbol not in strike_vol_df_cache:
        strike_vol_df_cache[symbol] =  get_strike_vol_df(get_market_data(symbol))
    return  strike_vol_df_cache[symbol]


# App layout
app.layout = dbc.Container([
    html.H1(children="My App", style={"textAlign": "center", "color": "cyan"}, className="mt-4"),

    html.Div(children=[
        dbc.Row(
            dbc.Input(placeholder="Search Option Chain, e.g., SPY",
                              type="search",
                              style={"color": "black", "width": "100%"},
                              className="mt-3",
                              id="ticker-input"),
            className="d-flex justify-content-center"
        ),
        dbc.Row(
            dcc.Button(children="Search", style={"width": "20%"}, className="mt-2", id="search-button", n_clicks=0),
            className="d-flex justify-content-end")
    ], className="mt-3"),

    dcc.Store(id="market-data"),

    dbc.Spinner(
        html.Div(
            dcc.Dropdown(id="expiry-dates-dropdown", placeholder="Select an expiry date",
                         style={"color": "black"}),
            id="expiry-section", style=HIDE_STYLE, className="mt-5 mb-5"
        )
    ),

    dbc.Spinner(
        html.Div(children=[
            dbc.Row(
                dbc.RadioItems(options=["Underlying", "Volatility Smile", "Volatility Surface"],
                               value="Volatility Smile", inline=True, id="graph-radio-items", className="gap-5",
                               style={"display": "flex", "justifyContent": "center"}),
            ),
            dbc.Row(
                dbc.Checklist(
                    id='toggle-rangeslider',
                    options=[{'label': 'Include Rangeslider',
                              'value': 'slider'}],
                    value=['slider']
                ), className="mt-3"
            ),
            dbc.Row(
                dcc.Graph(id="graph-final", style={"display": "flex", "justifyContent": "center"}, className="mb-3")
            )
        ], id="graph-area", style=HIDE_STYLE)
    ),
], style={"width": "60%"})


# Handles expiry dropdown and market data
@callback(
    Output("market-data", "data"),
    Output("expiry-section", "style"),
    Output("expiry-dates-dropdown", "options"),
    Output("expiry-dates-dropdown", "value"),
    Input("search-button", "n_clicks"),
    State("ticker-input", "value"),
    prevent_initial_call=True
)
def show_expiries(_, state_value):
    if not state_value:
        return no_update, HIDE_STYLE, [], None

    ticker_symbol = str(state_value).upper().strip()
    data = get_market_data(ticker_symbol)
    return ticker_symbol, {"width": "60%", "margin": "auto", "display": "block"}, data.expiries, None


# Handles graph area, graphs and radio items
@callback(
    Output("graph-area", "style"),
    Output("graph-final", "figure"),
    Output("toggle-rangeslider", "style"),
    Input("search-button", "n_clicks"),
    Input("expiry-dates-dropdown", "value"),
    Input("graph-radio-items", "value"),
    Input("market-data", "data"),
    Input("toggle-rangeslider", "value"),
    prevent_initial_call=True
)
def toggle_graph_area(_, expiry_value, figure, symbol, slider_value):
    if ctx.triggered_id == "search-button":
        return HIDE_STYLE, no_update, HIDE_STYLE

    if expiry_value:
        my_df = market_vol_df_store(symbol)
        pivot_df = my_df.pivot(index="strike", columns="time_to_expiry", values="implied_vol")
        pivot_df = pivot_df.interpolate(axis=0).interpolate(axis=1)

        market_data = get_market_data(symbol)
        ticker_history = market_data.ticker.history(period="1y")

        time_to_expiry = (dt.strptime(expiry_value, "%Y-%m-%d") - market_data.today).days / 365.25
        my_df_expiry = my_df[my_df["time_to_expiry"] == time_to_expiry]

        if figure == "Volatility Surface":
            fig = go.Figure(data=go.Surface(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index))

        elif figure == "Volatility Smile":
            fig = px.line(data_frame=my_df_expiry, x="strike", y="implied_vol")

        else:
            fig = go.Figure(go.Candlestick(
                x=ticker_history.index,
                open=ticker_history['Open'],
                high=ticker_history['High'],
                low=ticker_history['Low'],
                close=ticker_history['Close']
            ))

            fig.update_layout(
                xaxis_rangeslider_visible='slider' in slider_value
            )
            return {"display": "block"}, fig, {"display": "block", "color":"white"}
        return {"display": "block"}, fig, HIDE_STYLE
    return HIDE_STYLE, no_update, HIDE_STYLE


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
