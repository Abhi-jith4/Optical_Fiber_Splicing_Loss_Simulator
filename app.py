import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Optical Fiber Splicing Loss Simulator",
    page_icon="🔬",
    layout="wide",
)

# ----------------------------- Styling ---------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #fff8fb; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #111a3b 0%, #20294c 100%); }
    [data-testid="stSidebar"] * { color: #f6f3ff !important; }
    .hero {
        background: #172344; color: #fff; padding: 1.3rem 1.5rem;
        border-radius: 12px; margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 1.8rem; }
    .hero p { margin: .4rem 0 0 0; opacity: .9; }
    .metric-card {
        border: 1px solid #e6dfe9; background: #ffffff;
        border-radius: 10px; padding: 1rem;
    }
    .small-note { color: #625b6b; font-size: .88rem; }
</style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "fibre_length_km": 10.0,
    "attenuation_db_km": 0.2,
    "num_splices": 5,
    "splice_loss_db": 0.1,
    "num_connectors": 2,
    "connector_loss_db": 0.5,
    "tx_power_dbm": 0.0,
    "rx_sensitivity_dbm": -20.0,
}
SCENARIOS = {
    "Excellent": 0.05,
    "Good": 0.10,
    "Average": 0.20,
    "Poor": 0.50,
}


def calculate_link(p):
    fibre_loss = p["fibre_length_km"] * p["attenuation_db_km"]
    splice_loss = p["num_splices"] * p["splice_loss_db"]
    connector_loss = p["num_connectors"] * p["connector_loss_db"]
    total_loss = fibre_loss + splice_loss + connector_loss
    rx_power = p["tx_power_dbm"] - total_loss
    margin = rx_power - p["rx_sensitivity_dbm"]
    return {
        **p,
        "fibre_loss_db": fibre_loss,
        "total_splice_loss_db": splice_loss,
        "total_connector_loss_db": connector_loss,
        "total_loss_db": total_loss,
        "received_power_dbm": rx_power,
        "link_margin_db": margin,
        "status": "PASS" if margin >= 0 else "FAIL",
    }


def scenario_table(p):
    rows = []
    for name, loss_per_splice in SCENARIOS.items():
        q = dict(p)
        q["splice_loss_db"] = loss_per_splice
        result = calculate_link(q)
        rows.append({
            "name": name,
            "splice_loss_db": result["total_splice_loss_db"],
            "total_loss_db": result["total_loss_db"],
            "received_power_dbm": result["received_power_dbm"],
            "link_margin_db": result["link_margin_db"],
            "status": result["status"],
        })
    return pd.DataFrame(rows)


def current_config_csv(result):
    columns = [
        ("Fibre Length (km)", "fibre_length_km"),
        ("Attenuation (dB/km)", "attenuation_db_km"),
        ("Number of Splices", "num_splices"),
        ("Splice Loss (dB/splice)", "splice_loss_db"),
        ("Number of Connectors", "num_connectors"),
        ("Connector Loss (dB/connector)", "connector_loss_db"),
        ("Tx Power (dBm)", "tx_power_dbm"),
        ("Rx Sensitivity (dBm)", "rx_sensitivity_dbm"),
        ("Fibre Loss (dB)", "fibre_loss_db"),
        ("Total Splice Loss (dB)", "total_splice_loss_db"),
        ("Total Connector Loss (dB)", "total_connector_loss_db"),
        ("Total Loss (dB)", "total_loss_db"),
        ("Received Power (dBm)", "received_power_dbm"),
        ("Link Margin (dB)", "link_margin_db"),
        ("Status", "status"),
    ]
    return pd.DataFrame([{"Parameter": label, "Value": result[key]} for label, key in columns])


def simulation_report(result, scenarios):
    return f"""# Optical Fiber Splicing Loss Simulator — Simulation Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Configuration
- Fibre length: {result['fibre_length_km']:.2f} km
- Attenuation coefficient: {result['attenuation_db_km']:.3f} dB/km
- Number of splices: {result['num_splices']}
- Loss per splice: {result['splice_loss_db']:.3f} dB
- Number of connectors: {result['num_connectors']}
- Loss per connector: {result['connector_loss_db']:.3f} dB
- Transmitter power: {result['tx_power_dbm']:.2f} dBm
- Receiver sensitivity: {result['rx_sensitivity_dbm']:.2f} dBm

## Calculated Results
- Fibre attenuation: {result['fibre_loss_db']:.3f} dB
- Total splice loss: {result['total_splice_loss_db']:.3f} dB
- Total connector loss: {result['total_connector_loss_db']:.3f} dB
- Total link loss: {result['total_loss_db']:.3f} dB
- Received power: {result['received_power_dbm']:.3f} dBm
- Link margin: {result['link_margin_db']:.3f} dB
- Status: **{result['status']}**

## Equations
- Fibre loss: `L_f = alpha × L`
- Splice loss: `L_s = N_s × l_s`
- Connector loss: `L_c = N_c × l_c`
- Total loss: `L_total = L_f + L_s + L_c`
- Received power: `P_r = P_t - L_total`
- Link margin: `M = P_r - P_sensitivity`

## Scenario Comparison
{scenarios.to_markdown(index=False)}

## Model assumptions and limitations
This is a simplified optical power-budget model. It assumes constant fibre attenuation and identical loss per splice and per connector. It does not model chromatic dispersion, polarization-mode dispersion, nonlinear effects, wavelength-dependent attenuation, bend/temperature/ageing effects, or a BER target. PASS means only that the calculated received power meets or exceeds the configured receiver sensitivity. The model should be validated against real measurements before engineering deployment.
"""


def render_header(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


# Sidebar navigation and shared inputs
st.sidebar.markdown("## 🔬 Optical Fiber Splicing Loss Simulator")
st.sidebar.markdown("*Interactive optical power-budget analysis tool*")
nav_options = [
    "Dashboard", "Link Budget Calculator", "Graphical Analysis",
    "Scenario Comparison", "Reports & Export", "Theory & Methodology"
]
qp_page = st.query_params.get("page", None)
default_idx = nav_options.index(qp_page) if qp_page in nav_options else 0
page = st.sidebar.radio(
    "Navigation",
    nav_options,
    index=default_idx,
    label_visibility="collapsed",
)

with st.sidebar.expander("Link configuration", expanded=page == "Link Budget Calculator"):
    length = st.number_input("Fibre length (km)", min_value=0.0, max_value=10000.0,
                             value=float(st.session_state.get("length", DEFAULTS["fibre_length_km"])), step=1.0)
    attenuation = st.number_input("Attenuation (dB/km)", min_value=0.0, max_value=10.0,
                                  value=float(st.session_state.get("attenuation", DEFAULTS["attenuation_db_km"])), step=0.01, format="%.3f")
    n_splices = st.number_input("Number of splices", min_value=0, max_value=100000,
                                value=int(st.session_state.get("n_splices", DEFAULTS["num_splices"])), step=1)
    splice_loss = st.number_input("Loss per splice (dB)", min_value=0.0, max_value=20.0,
                                  value=float(st.session_state.get("splice_loss", DEFAULTS["splice_loss_db"])), step=0.01, format="%.3f")
    n_connectors = st.number_input("Number of connectors", min_value=0, max_value=100000,
                                   value=int(st.session_state.get("n_connectors", DEFAULTS["num_connectors"])), step=1)
    connector_loss = st.number_input("Loss per connector (dB)", min_value=0.0, max_value=20.0,
                                    value=float(st.session_state.get("connector_loss", DEFAULTS["connector_loss_db"])), step=0.01, format="%.3f")
    tx_power = st.number_input("Transmitter power (dBm)", min_value=-100.0, max_value=100.0,
                               value=float(st.session_state.get("tx_power", DEFAULTS["tx_power_dbm"])), step=0.5)
    rx_sensitivity = st.number_input("Receiver sensitivity (dBm)", min_value=-100.0, max_value=20.0,
                                      value=float(st.session_state.get("rx_sensitivity", DEFAULTS["rx_sensitivity_dbm"])), step=0.5)
    if st.button("Reset to defaults", use_container_width=True):
        for key in ["length", "attenuation", "n_splices", "splice_loss", "n_connectors",
                    "connector_loss", "tx_power", "rx_sensitivity"]:
            st.session_state.pop(key, None)
        st.rerun()

st.session_state["length"] = length
st.session_state["attenuation"] = attenuation
st.session_state["n_splices"] = n_splices
st.session_state["splice_loss"] = splice_loss
st.session_state["n_connectors"] = n_connectors
st.session_state["connector_loss"] = connector_loss
st.session_state["tx_power"] = tx_power
st.session_state["rx_sensitivity"] = rx_sensitivity

params = {
    "fibre_length_km": length,
    "attenuation_db_km": attenuation,
    "num_splices": int(n_splices),
    "splice_loss_db": splice_loss,
    "num_connectors": int(n_connectors),
    "connector_loss_db": connector_loss,
    "tx_power_dbm": tx_power,
    "rx_sensitivity_dbm": rx_sensitivity,
}
result = calculate_link(params)
scenarios = scenario_table(params)

# ------------------------------- Pages ---------------------------------------
if page == "Dashboard":
    render_header("Optical Fiber Splicing Loss Simulator", "Dashboard — optical link power-budget summary")
    st.caption("Change the configuration in the sidebar to recalculate the link.")
    cols = st.columns(4)
    cols[0].metric("Total link loss", f"{result['total_loss_db']:.2f} dB")
    cols[1].metric("Received power", f"{result['received_power_dbm']:.2f} dBm")
    cols[2].metric("Link margin", f"{result['link_margin_db']:.2f} dB")
    cols[3].metric("Status", result["status"])
    if result["status"] == "PASS":
        st.success("PASS — received power meets or exceeds the receiver sensitivity threshold.")
    else:
        st.error("FAIL — received power is below the receiver sensitivity threshold.")
    st.subheader("Loss summary")
    loss_df = pd.DataFrame({
        "Component": ["Fibre attenuation", "Splice loss", "Connector loss"],
        "Loss (dB)": [result["fibre_loss_db"], result["total_splice_loss_db"], result["total_connector_loss_db"]],
    })
    c1, c2 = st.columns([1, 1])
    with c1:
        st.dataframe(loss_df, use_container_width=True, hide_index=True)
    with c2:
        fig = px.pie(loss_df, names="Component", values="Loss (dB)", hole=0.48,
                     title="Component-wise loss breakdown")
        st.plotly_chart(fig, use_container_width=True)
    st.info("This application is a simplified educational power-budget model; it is not a substitute for optical power-meter or OTDR measurements.")

elif page == "Link Budget Calculator":
    render_header("Link Budget Calculator", "Calculate the loss and received power for a configurable optical link")
    st.subheader("Input parameters")
    st.write("Use the controls in the sidebar to change the link configuration.")
    st.subheader("Step-by-step calculation")
    st.markdown(f"""
    1. **Fibre attenuation:** `L_f = α × L = {attenuation:.3f} × {length:.3f} = {result['fibre_loss_db']:.3f} dB`
    2. **Splice loss:** `L_s = N_s × l_s = {int(n_splices)} × {splice_loss:.3f} = {result['total_splice_loss_db']:.3f} dB`
    3. **Connector loss:** `L_c = N_c × l_c = {int(n_connectors)} × {connector_loss:.3f} = {result['total_connector_loss_db']:.3f} dB`
    4. **Total loss:** `L_total = L_f + L_s + L_c = {result['total_loss_db']:.3f} dB`
    5. **Received power:** `P_r = P_t − L_total = {tx_power:.3f} − {result['total_loss_db']:.3f} = {result['received_power_dbm']:.3f} dBm`
    6. **Link margin:** `M = P_r − P_sensitivity = {result['received_power_dbm']:.3f} − ({rx_sensitivity:.3f}) = {result['link_margin_db']:.3f} dB`
    """)
    st.metric("Calculated link status", result["status"])

elif page == "Graphical Analysis":
    render_header("Graphical Analysis", "Visualize the contribution of loss components and the effect of fibre length")
    loss_df = pd.DataFrame({
        "Component": ["Fibre attenuation", "Splice loss", "Connector loss"],
        "Loss (dB)": [result["fibre_loss_db"], result["total_splice_loss_db"], result["total_connector_loss_db"]],
    })
    st.plotly_chart(px.bar(loss_df, x="Component", y="Loss (dB)", title="Loss by component"), use_container_width=True)
    st.plotly_chart(px.pie(loss_df, names="Component", values="Loss (dB)", hole=0.42,
                           title="Component-wise loss breakdown"), use_container_width=True)
    max_len = max(50.0, min(500.0, length * 2 if length > 0 else 50.0))
    lengths = list(range(0, int(max_len) + 1, max(1, int(max_len / 25))))
    if lengths[-1] != max_len:
        lengths.append(max_len)
    rows = []
    fixed_losses = result["total_splice_loss_db"] + result["total_connector_loss_db"]
    for L in lengths:
        total = L * attenuation + fixed_losses
        rx = tx_power - total
        rows.append({"Fibre length (km)": L, "Received power (dBm)": rx,
                     "Link margin (dB)": rx - rx_sensitivity})
    sweep = pd.DataFrame(rows)
    st.plotly_chart(px.line(sweep, x="Fibre length (km)", y="Received power (dBm)",
                            markers=True, title="Received power versus fibre length"), use_container_width=True)
    st.plotly_chart(px.line(sweep, x="Fibre length (km)", y="Link margin (dB)",
                            markers=True, title="Link margin versus fibre length"), use_container_width=True)
    st.caption("Length-sweep curves are theoretical predictions from the same simplified equations, not measurements.")

elif page == "Scenario Comparison":
    render_header("Scenario Comparison", "Compare link performance under different assumed splice-loss values")
    st.caption("Scenario labels are illustrative categories; the loss values can be edited in the code.")
    st.dataframe(scenarios.round(3), use_container_width=True, hide_index=True)
    fig = px.bar(scenarios, x="name", y="link_margin_db", color="status",
                 title="Scenario comparison — link margin", labels={"name": "Scenario", "link_margin_db": "Link margin (dB)"})
    fig.add_hline(y=0, line_dash="dash", annotation_text="PASS / FAIL boundary")
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.bar(scenarios, x="name", y="total_loss_db", title="Total link loss by scenario",
                  labels={"name": "Scenario", "total_loss_db": "Total loss (dB)"})
    st.plotly_chart(fig2, use_container_width=True)

elif page == "Reports & Export":
    render_header("Reports & Export", "Download the current configuration, scenario comparison, and simulation report")
    config_df = current_config_csv(result)
    st.subheader("1. Current Configuration CSV")
    st.dataframe(config_df, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download Configuration CSV",
                       data=config_df.to_csv(index=False).encode("utf-8"),
                       file_name="optical_link_configuration.csv", mime="text/csv")
    st.divider()
    st.subheader("2. Scenario Comparison CSV")
    st.dataframe(scenarios.round(4), use_container_width=True, hide_index=True)
    st.download_button("⬇ Download Scenario CSV",
                       data=scenarios.to_csv(index=False).encode("utf-8"),
                       file_name="scenario_comparison.csv", mime="text/csv")
    st.divider()
    st.subheader("3. Simulation Report (Markdown)")
    report = simulation_report(result, scenarios)
    with st.expander("View full report"):
        st.markdown(report)
    st.download_button("⬇ Download Report (Markdown)", data=report.encode("utf-8"),
                       file_name="optical_fiber_simulation_report.md", mime="text/markdown")

elif page == "Theory & Methodology":
    render_header("Theory & Methodology", "Understanding the optical link power-budget model")
    st.subheader("Fibre splicing")
    st.write("Fibre splicing is the process of joining two optical fibres end-to-end. Fusion splicing uses an electric arc to melt aligned fibre ends together. Mechanical splicing aligns the fibre ends in a fixture, often using index-matching material.")
    st.subheader("Fibre attenuation")
    st.write("As light travels through an optical fibre, its power decreases because of absorption and scattering. The simulator represents the attenuation with a coefficient α in dB/km.")
    st.latex(r"L_f = \alpha \times L \quad \mathrm{(dB)}")
    st.subheader("Splice and connector loss")
    st.latex(r"L_s = N_s \times l_s \quad \mathrm{(dB)}")
    st.latex(r"L_c = N_c \times l_c \quad \mathrm{(dB)}")
    st.subheader("Optical power budget")
    st.latex(r"L_{\mathrm{total}} = L_f + L_s + L_c")
    st.latex(r"P_r = P_t - L_{\mathrm{total}} \quad \mathrm{(dBm)}")
    st.latex(r"M = P_r - P_{\mathrm{sensitivity}} \quad \mathrm{(dB)}")
    st.markdown("""
    **Interpretation**
    - **PASS:** link margin is zero or positive; the calculated received power meets the configured sensitivity.
    - **FAIL:** link margin is negative; the calculated received power is below the configured sensitivity.

    **Limitations of the simplified model**
    1. Chromatic and polarization-mode dispersion are not included.
    2. Nonlinear fibre effects are not included.
    3. Attenuation is treated as constant and wavelength-independent.
    4. All splices and all connectors are assumed to have equal losses.
    5. Bending, ageing, temperature and other environmental effects are not modelled.
    6. The PASS/FAIL check does not establish a bit-error-rate target or replace a real link test.
    """)

st.sidebar.markdown("---")
st.sidebar.caption("Educational simulator • Python + Streamlit")
