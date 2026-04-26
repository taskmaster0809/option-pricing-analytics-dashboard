import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import dash_ag_grid as dag

from data.market_data import MarketData
from vol_surface.implied_vol import get_strike_vol_df, get_day_diff
from pricing.black_scholes import EuropeanOption
from greeks_table import GREEKS, create_greeks_table

HIDE_STYLE = {"display": "none"}
VISIBLE_STYLE = {"display": "block"}


def custom_error_handler(_):
    return no_update, HIDE_STYLE, [], None, {
        **VISIBLE_STYLE,
        "textAlign": "center",
        "color": "#ff6b6b",
        "fontSize": "1rem",
        "opacity": "0.85",
        "letterSpacing": "0.03em"
    }


app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dag.themes.BASE, dag.themes.ALPINE])

market_data_cache = {}
strike_vol_df_cache = {}
strike_greek_df_cache = {}


def get_market_data(symbol) -> MarketData:        # Used to store market data in cache
    if symbol not in market_data_cache:
        market_data_cache[symbol] = MarketData(symbol)
    return market_data_cache[symbol]


def get_market_vol_df(symbol) -> pd.DataFrame:  # Used to store the implied vol data in cache
    if symbol not in strike_vol_df_cache:
        strike_vol_df_cache[symbol] =  get_strike_vol_df(get_market_data(symbol))
    return strike_vol_df_cache[symbol]


# Get greeks and strikes data
def get_strike_greek_df(symbol, expiry_date, strikes) -> pd.DataFrame:
    if (symbol, expiry_date, tuple(strikes)) not in strike_greek_df_cache:
        columns = ["Delta Call", "Delta Put", "Gamma", "Vega", "Rho Call", "Rho Put", "Theta Call", "Theta Put"]
        market_data = get_market_data(symbol)
        time_to_expiry = get_day_diff(expiry_date, market_data)

        strike_greek_df = pd.DataFrame(index=strikes, columns=columns)

        for strike in strikes:
            option = get_option(symbol, market_data, time_to_expiry, strike)
            greek_values = []
            greeks = option.greeks()
            call_options = greeks["call"]
            put_options = greeks["put"]

            for column in columns:
                if "Call" in column:
                    greek_values.append(call_options[column.replace(" Call", "")])
                elif "Put" in column:
                    greek_values.append(put_options[column.replace(" Put", "")])
                else:
                    greek_values.append(call_options[column])

            strike_greek_df.loc[strike] = greek_values

        strike_greek_df_cache[(symbol, expiry_date, tuple(strikes))] = strike_greek_df

    return strike_greek_df_cache[(symbol, expiry_date, tuple(strikes))]


def get_option(symbol:str, market_data: MarketData, time_to_expiry: float, strike: float) -> EuropeanOption:
    my_df = get_market_vol_df(symbol)

    # Calculate implied vol for given strike and expiry
    sigma = my_df[ (np.isclose(my_df["time_to_expiry"], time_to_expiry))
                   & (my_df["strike"] == strike) ]["implied_vol"].values[0]

    option = EuropeanOption(market_data.spot, strike, time_to_expiry, market_data.interest_rate, sigma)
    return option


# App layout
app.layout = dbc.Container([
    # Search bar and search functionality
    html.H1(children="VolatilityLens", style={
        "textAlign": "center",
        "color": "cyan",
        "fontSize": "3.5rem",
        "fontWeight": "700",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "textShadow": "0 0 20px rgba(0, 255, 255, 0.4)"
    }, className="mt-4"),

    html.Div(children=[

        dbc.Row(
            html.P(children=["Enter US based option chain symbol as in ",
                             html.A("Yahoo Finance", href="https://finance.yahoo.com/", target="_blank")]),
            className="mt-3"
        ),

        dbc.Row(
            dbc.Input(placeholder="Search Option Chain, e.g., SPY",
                              type="search",
                              style={"color": "black", "width": "100%"},
                              id="ticker-input"),
            className="d-flex justify-content-center"
        ),
        dbc.Row(
            dcc.Button(children="Search", style={"width": "20%"}, className="mt-2", id="search-button", n_clicks=0),
            className="d-flex justify-content-end"
        )
    ]),

    dcc.Store(id="market-data"),

    dbc.Row(
        html.P(["Oops! Could not find the option chain you were looking for :( Try visiting ",
                html.A("Yahoo Finance", href="https://finance.yahoo.com/", target="_blank"),
                " and see if option chains are available for this ticker"], style=HIDE_STYLE, id="error-message"),
        className="mt-4"
    ),

    dbc.Spinner(
        html.Div(
            dcc.Dropdown(id="expiry-dates-dropdown", placeholder="Select an expiry date",
                         style={"color": "black"}),
            id="expiry-section", style=HIDE_STYLE, className="mt-5 mb-5"
        )
    ),

    # Graph area inside a spinner
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
                    value=[]
                ), className="mt-3"
            ),

            dbc.Row(
                dcc.Graph(id="graph-final", style={"width": "100%", "display": "flex", "justifyContent": "center"},
                          className="mb-3")
            ),

            dbc.Row(
                html.P("Note: The jaggedness in volatility smile/surface may represent stale data")
            ),

            html.Hr(),
        ], id="graph-area", style=HIDE_STYLE)
    ),

    # Dashboard area in a spinner
    dbc.Spinner(
        html.Div(children=[
            html.H2(children="Greeks Dashboard", style={
                    "textAlign": "center",
                    "color": "cyan",
                    "fontSize": "1.8rem",
                    "fontWeight": "600",
                    "letterSpacing": "0.05em",
                    "opacity": "0.9"
            }),

            dbc.Row(
                dcc.Dropdown(id="strike-price-dropdown", placeholder="Select a strike price",
                             style={"color": "black", "width": "70%"}),
                id="strike-price-section", className="mt-3 mb-5", style={"display": "flex", "justifyContent": "center"}
            ),

            dbc.Row(
                dbc.RadioItems(options=["Greeks Table", "Greeks Plot"],
                               value="Greeks Table", inline=True, id="greeks-radio-items", className="gap-5",
                               style=HIDE_STYLE)
            ),

            dbc.Row(
                html.Div(id="dash-table-div", className="mt-3")
            ),

            dbc.Row(
                dcc.Dropdown(options=GREEKS, id="greek-selection-dropdown", value="Delta",
                             placeholder="Select a Greek option", style=HIDE_STYLE, className="mb-3"),
                style={"display": "flex", "justifyContent": "center"}
            ),

            dbc.Row(
                dcc.Graph(id="greek-plot-figure", style={"width":"100%", "display":"flex", "justifyContent": "center"}),
                className="mb-3"
            )

        ], style=HIDE_STYLE, id="greeks-dashboard-div")
    )

], style={"width": "70%"})


# Handles expiry dropdown and market data
@callback(
    Output("market-data", "data"),
    Output("expiry-section", "style"),
    Output("expiry-dates-dropdown", "options"),
    Output("expiry-dates-dropdown", "value"),
    Output("error-message", "style"),
    Input("search-button", "n_clicks"),
    State("ticker-input", "value"),
    prevent_initial_call=True,
    on_error=custom_error_handler
)
def show_expiries(_, state_value):
    if not state_value:
        return no_update, HIDE_STYLE, [], None, no_update

    symbol = str(state_value).upper().strip()
    vol_df = get_market_vol_df(symbol)

    if vol_df.empty:
        return custom_error_handler(_)

    return symbol, {"width": "60%", "margin": "auto", "display": "block"}, vol_df["date"].unique(), None, HIDE_STYLE


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
def toggle_graph_area(_, expiry_date, figure, symbol, slider_value):
    if ctx.triggered_id == "search-button":
        return HIDE_STYLE, no_update, HIDE_STYLE

    if expiry_date:
        my_df = get_market_vol_df(symbol)
        pivot_df = my_df.pivot(index="strike", columns="time_to_expiry", values="implied_vol")
        pivot_df = pivot_df.interpolate(axis=0).interpolate(axis=1)

        market_data = get_market_data(symbol)
        ticker_history = market_data.ticker.history(period="3mo")

        time_to_expiry = get_day_diff(expiry_date, market_data)
        my_df_expiry = my_df[ np.isclose(my_df["time_to_expiry"], time_to_expiry) ]

        if figure == "Volatility Surface":
            fig = go.Figure(data=go.Surface(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index))
            fig.update_layout(title=f"Volatility Surface ({symbol})", title_font_size=25, hoverlabel=dict(font_size=16),
                              autosize=True, height=600, scene=dict(
                    xaxis_title="Time to Expiry (years)",
                    yaxis_title=f"Strike Price ({market_data.metadata['currency']})",
                    zaxis_title="Implied Vol"
                )
            )
            fig.update_traces(hovertemplate='Strike: %{y}<br>' +
                                            'Time to expiry (years): %{x:.4f}<br>' +
                                            'Implied Vol: %{z}<br><extra></extra>',
                              colorbar_title="IV"
                              )

        elif figure == "Volatility Smile":
            fig = px.line(data_frame=my_df_expiry, x="strike", y="implied_vol", height=600)
            fig.update_layout(title=f"Volatility Smile ({symbol})",
                              xaxis_title=f"Strike Price (in {market_data.metadata['currency']})",
                              yaxis_title="Implied Volatility", font=dict(size=16), hoverlabel=dict(font_size=16),
                              )
            fig.update_traces(hovertemplate="Strike: %{x:.2f}<br>" +
                                            "Implied Vol: %{y:.4f}"
                              )

        else:
            fig = go.Figure(go.Candlestick(
                x=ticker_history.index,
                open=ticker_history['Open'],
                high=ticker_history['High'],
                low=ticker_history['Low'],
                close=ticker_history['Close']
            ))

            try:
                name = market_data.metadata["longName"]
            except KeyError:
                name = market_data.metadata["shortName"]

            fig.update_layout(
                xaxis_rangeslider_visible='slider' in slider_value, title=name,
                xaxis_title="Date", yaxis_title="Price", font=dict(size=16), height=600, hoverlabel=dict(font_size=16),
                template="plotly_dark"
            )
            fig.update_traces(
                increasing_line_color="cyan",
                decreasing_line_color="red",
                increasing_fillcolor="cyan",
                decreasing_fillcolor="red"
            )
            return VISIBLE_STYLE, fig, {"display": "block", "color":"white"}

        fig.update_layout(template="plotly_dark")
        return VISIBLE_STYLE, fig, HIDE_STYLE
    return HIDE_STYLE, no_update, HIDE_STYLE


# Handles strike price dropdown
@callback(
    Output("strike-price-dropdown", "options"),
    Output("greeks-dashboard-div", "style"),
    Input("market-data", "data"),
    Input("expiry-dates-dropdown", "value"),
    Input("graph-final", "figure"),
    prevent_initial_call=True
)
def show_strikes(symbol, expiry_date, _):
    if not expiry_date or not symbol:
        return no_update, HIDE_STYLE

    my_df = get_market_vol_df(symbol)
    time_to_expiry = get_day_diff(expiry_date, get_market_data(symbol))
    call_strikes = my_df[ np.isclose(my_df["time_to_expiry"], time_to_expiry) ]["strike_with_currency"].values
    return call_strikes, VISIBLE_STYLE


# Handles Greeks dashboard content
@callback(
    Output("dash-table-div", "children"),
    Output("greeks-radio-items", "style"),
    Output("greek-selection-dropdown", "style"),
    Input("strike-price-dropdown", "value"),
    Input("market-data", "data"),
    Input("expiry-dates-dropdown", "value"),
    Input("greeks-radio-items", "value"),
    prevent_initial_call=True
)
def toggle_greeks_dashboard(strike, symbol, expiry_date, radio_item_value):
    if not strike or not expiry_date or not symbol:
        return None, HIDE_STYLE, HIDE_STYLE

    strike = float(strike.split(" ")[1])

    market_data = get_market_data(symbol)
    time_to_expiry = get_day_diff(expiry_date, market_data)

    option = get_option(symbol, market_data, time_to_expiry, strike)

    if radio_item_value == "Greeks Table":
        greeks_table = create_greeks_table(option)
        return greeks_table, {"display": "flex", "justifyContent": "center"}, HIDE_STYLE
    elif radio_item_value == "Greeks Plot":
        return None, {"display": "flex", "justifyContent": "center"}, {**VISIBLE_STYLE, "color": "black",
                                                                       "width": "70%"}
    else:
        return None, HIDE_STYLE, HIDE_STYLE


@callback(
    Output("greek-plot-figure", "style"),
    Output("greek-plot-figure", "figure"),
    Input("market-data", "data"),
    Input("expiry-dates-dropdown", "value"),
    Input("greek-selection-dropdown", "value"),
    Input("strike-price-dropdown", "value"),
    Input("greeks-radio-items", "value"),
    prevent_initial_call=True
)
def show_strike_greek_graph(symbol, expiry_date, greek, strike_value, radio_item):
    if not greek or not symbol or not expiry_date or not strike_value or radio_item != "Greeks Plot":
        return HIDE_STYLE, no_update

    market_data = get_market_data(symbol)
    time_to_expiry = get_day_diff(expiry_date, market_data)
    my_df = get_market_vol_df(symbol)
    strikes = my_df[ np.isclose(my_df["time_to_expiry"], time_to_expiry) ]["strike"].values

    strike_greek_df = get_strike_greek_df(symbol, expiry_date, strikes)

    if greek == "Vega" or greek == "Gamma":
        fig = px.line(x=strikes, y=strike_greek_df[greek], height=600)
    else:
        fig = px.line(strike_greek_df[[greek + " Call", greek + " Put"]], height=600)

    fig.update_layout(title=f"{greek} ({symbol})", xaxis_title=f"Strike Price (in {market_data.metadata['currency']})",
                      yaxis_title="Value", legend_title="", font=dict(size=16), hoverlabel=dict(font_size=16),
                      hovermode="x", template="plotly_dark")
    fig.update_traces(hovertemplate= "Strike: %{x:.2f}<br>" +
                                     "Value: %{y:.4f}"
                      )

    return VISIBLE_STYLE, fig


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
