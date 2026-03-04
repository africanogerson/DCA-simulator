import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from simulation import (
    aggregate_results,
    download_spy_data,
    run_all_simulations,
)

st.set_page_config(page_title="DCA SPY Simulator", layout="wide")
st.title("DCA SPY Simulator")
st.caption("Dollar Cost Averaging on SPY across sliding 24-month windows")

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Parameters")

    total_aum = st.number_input(
        "Total Investment ($)",
        min_value=1_000,
        value=100_000,
        step=1_000,
    )

    start_year = st.number_input(
        "Start Year",
        min_value=1993,
        max_value=2023,
        value=2010,
        step=1,
    )

    end_year = st.number_input(
        "End Year",
        min_value=int(start_year) + 1,
        max_value=2025,
        value=max(int(start_year) + 1, 2020),
        step=1,
    )

    if end_year <= start_year:
        st.error("End Year must be greater than Start Year.")
        st.stop()

    n_windows = int(end_year) - int(start_year)
    monthly_installment = total_aum / 24
    st.info(
        f"**{n_windows} window{'s' if n_windows != 1 else ''}** | "
        f"Monthly installment: **${monthly_installment:,.0f}**"
    )


# ---------------------------------------------------------------------------
# Data fetch (cached by year range — AUM change does not re-download)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Downloading SPY data...")
def fetch_data(sy: int, ey: int) -> pd.DataFrame:
    return download_spy_data(sy, ey)


df = fetch_data(int(start_year), int(end_year))

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
results = run_all_simulations(df, int(start_year), int(end_year), float(total_aum))

if not results:
    st.error("No simulation windows could be computed. Check your year range.")
    st.stop()

agg = aggregate_results(results)

months = agg["months"]

# ---------------------------------------------------------------------------
# Chart 1 — % Variation Band
# ---------------------------------------------------------------------------
fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=months, y=agg["pct_min"],
    name="Min",
    line=dict(width=0),
    mode="lines",
    showlegend=True,
))
fig1.add_trace(go.Scatter(
    x=months, y=agg["pct_max"],
    name="Max",
    line=dict(width=0),
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(99,110,250,0.20)",
    showlegend=True,
))
fig1.add_trace(go.Scatter(
    x=months, y=agg["pct_median"],
    name="Median",
    line=dict(color="rgb(99,110,250)", width=2.5),
    mode="lines",
))
fig1.add_hline(
    y=0,
    line_width=2.5,
    line_color="black",
    annotation_text="Break-even",
    annotation_position="bottom right",
)
fig1.update_layout(
    title="Portfolio % Variation vs. Invested Capital",
    xaxis_title="Month",
    yaxis_title="Return (%)",
    hovermode="x unified",
    legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
)

# ---------------------------------------------------------------------------
# Chart 2 — Dollar Value Band
# ---------------------------------------------------------------------------
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=months, y=agg["value_min"],
    name="Min Value",
    line=dict(width=0),
    mode="lines",
    showlegend=True,
))
fig2.add_trace(go.Scatter(
    x=months, y=agg["value_max"],
    name="Max Value",
    line=dict(width=0),
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(0,204,150,0.20)",
    showlegend=True,
))
fig2.add_trace(go.Scatter(
    x=months, y=agg["value_median"],
    name="Median Value",
    line=dict(color="rgb(0,204,150)", width=2.5),
    mode="lines",
))
fig2.add_trace(go.Scatter(
    x=months, y=agg["invested_line"],
    name="Invested Capital",
    line=dict(color="black", width=3, dash="dash"),
    mode="lines",
))
fig2.update_layout(
    title="Portfolio Dollar Value vs. Invested Capital",
    xaxis_title="Month",
    yaxis=dict(title="Value ($)", tickformat="$,.0f"),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
)

# ---------------------------------------------------------------------------
# Chart 3 — Final Return by Start Year
# ---------------------------------------------------------------------------
final_returns = agg["final_returns"]
start_years = agg["start_years"]

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=start_years,
    y=final_returns,
    text=[f"{r:.1f}%" for r in final_returns],
    textposition="outside",
    marker=dict(
        color=final_returns,
        colorscale="RdYlGn",
        showscale=True,
        colorbar=dict(title="Return %"),
    ),
    name="Final Return",
))
fig3.add_hline(
    y=0,
    line_width=2.5,
    line_color="black",
)
fig3.update_layout(
    title="Final 24-Month Return by Window Start Year",
    xaxis=dict(title="Start Year", tickmode="linear", dtick=1),
    yaxis_title="Return at Month 24 (%)",
    hovermode="x",
)

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("Raw simulation data"):
    rows = []
    for r in results:
        rows.append({
            "Start Year": r.start_year,
            "Monthly Investment ($)": f"${r.monthly_investment:,.0f}",
            "Final Portfolio Value ($)": f"${r.portfolio_values[-1]:,.0f}",
            "Total Invested ($)": f"${r.invested_capital[-1]:,.0f}",
            "Final Return (%)": f"{r.final_return_pct:.2f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
