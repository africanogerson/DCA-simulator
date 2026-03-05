import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from simulation import (
    aggregate_results,
    download_spy_data,
    run_all_simulations,
)

st.set_page_config(page_title="DCA S&P 500 Simulator", layout="wide")
st.title("DCA S&P 500 Simulator")
st.caption("Simulate a Dollar Cost Averaging strategy on S&P 500 ETF (SPY) and compare it against a fixed income return")

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
        max_value=2024,
        value=2010,
        step=1,
    )

    end_year = st.number_input(
        "End Year",
        min_value=int(start_year) + 1,
        max_value=2025,
        value=max(int(start_year) + 1, 2025),
        step=1,
    )

    window_years = st.number_input(
        "Investment Period (years)",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
    )

    annual_rate_pct = st.number_input(
        "Fixed Income Annual Rate (%)",
        min_value=0.1,
        max_value=30.0,
        value=5.0,
        step=0.1,
    )

    if end_year <= start_year:
        st.error("End Year must be greater than Start Year.")
        st.stop()

    n_months = int(window_years) * 12
    n_windows = int(end_year) - int(start_year)
    monthly_installment = total_aum / n_months
    st.info(
        f"**{n_windows} investment periods of {'s' if n_windows != 1 else ''}** · "
        f"**{n_months} months** | "
        f"Monthly installment: **${monthly_installment:,.0f}**"
    )


# ---------------------------------------------------------------------------
# Data fetch (cached by year range — AUM change does not re-download)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Downloading SPY data...")
def fetch_data(sy: int, ey: int, wy: int) -> pd.DataFrame:
    return download_spy_data(sy, ey, wy)


df = fetch_data(int(start_year), int(end_year), int(window_years))

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
results = run_all_simulations(df, int(start_year), int(end_year), float(total_aum), int(window_years))

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
    title="Portfolio % Variation vs. time (months)",
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
_y_min = min(final_returns)
_y_max = max(final_returns)
_y_range = _y_max - _y_min

fig3.update_layout(
    title=f"Final return after {window_years} years of continuous monthly investments by starting year",
    xaxis=dict(title="Start Year", tickmode="linear", dtick=1),
    yaxis=dict(
        title=f"Return after {window_years} years (%)",
        range=[_y_min - _y_range * 0.1, _y_max + _y_range * 0.2],
    ),
    hovermode="x",
)

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

# --- Chart 3: Final return by start year ---
st.divider()
st.plotly_chart(fig3, use_container_width=True)

# --- Fixed Income Comparison ---
st.divider()
st.subheader("Fixed Income Comparison")

# Effective monthly rate: (1 + annual)^(1/12) - 1
# Ensures compounding monthly for 12 months yields exactly the annual rate.
r_monthly = (1 + annual_rate_pct / 100) ** (1 / 12) - 1

# Future value of an ordinary annuity:  FV = C × [(1 + r)^n − 1] / r
# Return % is independent of C (investment amount cancels out).
fi_fv_ratio = ((1 + r_monthly) ** n_months - 1) / r_monthly  # FV / C
fi_total_ratio = n_months  # total invested / C
fi_return_pct = (fi_fv_ratio - fi_total_ratio) / fi_total_ratio * 100

dca_median_final = agg["pct_median"][-1]

col1, col2 = st.columns(2)
col1.metric(
    f"Fixed Income return ({window_years}yr @ {annual_rate_pct:.1f}%/yr)",
    f"{fi_return_pct:.2f}%",
)
col2.metric(
    "DCA median return (same period)",
    f"{dca_median_final:.2f}%",
    delta=f"{dca_median_final - fi_return_pct:+.2f}% vs fixed income",
)


st.caption(
    f"Fixed income assumes equal monthly contributions over {n_months} months, "
    f"compounded at an effective monthly rate of {r_monthly * 100:.4f}% "
    f"(≡ {annual_rate_pct:.1f}%/yr). "
    f"The percentage is the same regardless of the amount invested or the start year."
)

# --- Chart 1: % Variation Band ---
st.divider()
st.plotly_chart(fig1, use_container_width=True)
st.markdown(
    "The **volatility band** is built by running one independent DCA window per starting year "
    "and tracking the portfolio's percentage gain or loss against invested capital at each month. "
    "The shaded area spans the worst and best outcomes across all windows; the line is the median, "
    "giving a sense of the typical trajectory regardless of when you started investing."
)

# --- Chart 2: Dollar Value Band ---
st.divider()
st.plotly_chart(fig2, use_container_width=True)
st.markdown(
    "The **dollar value band** shows the same windows in absolute terms: the dashed line is the "
    "capital being deployed month by month, while the shaded area represents the range of portfolio "
    "values across all start years. When the band sits above the dashed line the strategy is in profit; "
    "the spread between min and max reflects how much the entry year affects the final outcome."
)

st.divider()
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
