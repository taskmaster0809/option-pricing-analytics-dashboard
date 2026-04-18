import plotly.graph_objects as go

my_df = get_strike_vol_df(ticker)
pivot_df = my_df.pivot(index="strike", columns="time_to_expiry", values="implied_vol")
pivot_df = pivot_df.interpolate(axis=0).interpolate(axis=1)
print(pivot_df)

fig = go.Figure(data=go.Surface(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index))
fig.show()