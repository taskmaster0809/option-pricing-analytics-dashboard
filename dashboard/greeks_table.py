import dash_ag_grid as dag
import pandas as pd

from pricing.black_scholes import EuropeanOption

GREEKS = ["Delta", "Gamma", "Vega", "Rho", "Theta"]


def create_greeks_table(option: EuropeanOption) -> dag.AgGrid:
    greeks_dict = option.greeks()
    calls = [round(greeks_dict["call"][g], 4) for g in GREEKS]
    puts = [round(greeks_dict["put"][g], 4) for g in GREEKS]
    data = pd.DataFrame(data={"Greeks": GREEKS, "Call": calls, "Put": puts})

    table = dag.AgGrid(
        columnDefs=[
            {"field": "Greeks", "headerName": "Greek"},
            {"field": "Call"},
            {"field": "Put"}
        ],
        rowData=data.to_dict("records"),

        defaultColDef={
            "cellStyle": {"fontSize": "16px"},
            "headerStyle": {"fontSize": "23px", "fontWeight": "bold"}
        },

        dashGridOptions={
            "domLayout": "autoHeight",
            "theme": "legacy"
        },

        columnSize="sizeToFit",
        style={
            "margin": "auto",
            "borderRadius": "10px",
            "overflow": "hidden"
        },
        className="ag-theme-alpine-dark"
    )

    return table
