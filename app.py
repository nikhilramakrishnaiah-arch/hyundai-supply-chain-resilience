import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ------------------------------------------------------------
# Hyundai Cognitive Supply Chain Resilience Dashboard
# Reads the project's existing CSV files from the same folder.
# ------------------------------------------------------------

st.set_page_config(page_title="Cognitive Supply Chain Resilience", page_icon="🚗", layout="wide")
BASE_DIR = Path(__file__).resolve().parent

st.markdown("""
<style>
.main-title {font-size: 2.35rem; font-weight: 750; color: #14213d; margin-bottom: 0;}
.sub-title {font-size: 1.05rem; color: #64748b; margin-top: .15rem;}
.section-title {font-size: 1.35rem; font-weight: 700; color: #14213d;}
.small-note {font-size: .85rem; color: #64748b;}
div[data-testid="stMetric"] {background: #f7f9fc; border: 1px solid #e5eaf1; padding: 14px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_csv(filename):
    path = BASE_DIR / filename
    
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception as exc:
            st.warning(f"Could not read {filename}: {exc}")
    return None

supplier = load_csv("Supply chain disruption Portfolio/supplier_component_master.csv")
inventory = load_csv("Supply chain disruption Portfolio/inventory_demand_synthetic.csv")
scenarios = load_csv("Supply chain disruption Portfolio/hyundai_disruption_scenarios.csv")
scenario_results = load_csv("hyundai_revised_disruption_results.csv")
if scenario_results is None:
    scenario_results = load_csv("hyundai_disruption_simulation_results.csv")
scenario_summary = load_csv("hyundai_revised_scenario_summary.csv")
if scenario_summary is None:
    scenario_summary = load_csv("hyundai_disruption_scenario_summary.csv")
vulnerability = load_csv("supplier_vulnerability_analysis.csv")
transport = load_csv("Supply chain disruption Portfolio/transport_routes_synthetic.csv")

st.markdown('<div class="main-title">Cognitive Supply Chain Resilience</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hyundai Supply Chain Analytics | Decision-support prototype</div>', unsafe_allow_html=True)
st.divider()

# Sidebar controls
st.sidebar.title("Dashboard Controls")
st.sidebar.caption("Choose the analysis area to explore.")
page = st.sidebar.radio("Navigate", ["Executive Overview", "Supplier Risk", "Disruption Scenarios", "Procurement Optimization", "Inventory & Logistics", "Data Quality & Notes"])
st.sidebar.divider()
st.sidebar.caption("Data files are read from the same folder as app.py. Synthetic datasets are labelled accordingly.")

# Common helpers

def metric_row(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)

def show_missing(files):
    missing = [f for f in files if not (BASE_DIR / f).exists()]
    if missing:
        st.info("Some optional project files were not found in the app.py folder: " + ", ".join(missing))

if page == "Executive Overview":
    st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)
    st.write("A consolidated view of supplier exposure, disruption impact and procurement decisions.")

    n_suppliers = supplier["supplier_id"].nunique() if supplier is not None and "supplier_id" in supplier else None
    n_components = inventory["component_id"].nunique() if inventory is not None and "component_id" in inventory else (supplier["component_id"].nunique() if supplier is not None and "component_id" in supplier else None)
    budget = None
    if supplier is not None and {"component_id", "component_name"}.issubset(supplier.columns):
        st.caption("Supplier and component master data loaded.")
    if scenario_summary is not None:
        st.caption("Scenario summary data loaded from your project output.")

    metrics = []
    if n_suppliers is not None: metrics.append(("Suppliers mapped", f"{n_suppliers:,}", "Count in supplier master"))
    if n_components is not None: metrics.append(("Components mapped", f"{n_components:,}", "Count in component/inventory master"))
    if inventory is not None and "avg_daily_demand_units" in inventory:
        metrics.append(("Total daily component demand", f"{inventory['avg_daily_demand_units'].sum():,.0f}", "Sum of illustrative component demand"))
    if inventory is not None and "on_hand_inventory_units" in inventory:
        metrics.append(("On-hand inventory", f"{inventory['on_hand_inventory_units'].sum():,.0f}", "Illustrative inventory units"))
    if metrics: metric_row(metrics)
    else: st.warning("No recognised project CSVs were found. Place the project CSV files beside app.py.")

    left, right = st.columns(2)
    with left:
        st.subheader("Component demand profile")
        if inventory is not None and {"component_name", "avg_daily_demand_units"}.issubset(inventory.columns):
            fig = px.bar(inventory, x="component_name", y="avg_daily_demand_units", color="criticality_score" if "criticality_score" in inventory else None, title="Average daily demand by component")
            fig.update_layout(xaxis_title="", yaxis_title="Units per day")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Supply chain disruption Portfolio/inventory_demand_synthetic.csv is needed for this chart.")
    with right:
        st.subheader("Scenario impact")
        if scenario_summary is not None:
            numeric = scenario_summary.select_dtypes(include="number").columns.tolist()
            label_col = next((c for c in scenario_summary.columns if "scenario" in c.lower() and c not in numeric), None)
            impact_col = next((c for c in numeric if any(k in c.lower() for k in ["unmet", "short", "loss"])), None)
            if label_col and impact_col:
                fig = px.bar(scenario_summary, x=label_col, y=impact_col, title=f"{impact_col.replace('_',' ').title()} by scenario")
                fig.update_layout(xaxis_title="", yaxis_title="Units")
                st.plotly_chart(fig, use_container_width=True)
            else: st.dataframe(scenario_summary, use_container_width=True, hide_index=True)
        else: st.info("Scenario summary output CSV was not found. Add it to the app folder to display scenario results.")

    st.subheader("Project data status")

    status = pd.DataFrame({
        "Dataset": [
            "Supplier master",
            "Inventory and demand",
            "Disruption scenarios",
            "Scenario results",
            "Scenario summary",
            "Supplier vulnerability",
            "Transport routes"
        ],
        "Status": [
            "Loaded" if x is not None else "Not found"
            for x in [
                supplier,
                inventory,
                scenarios,
                scenario_results,
                scenario_summary,
                vulnerability,
                transport
            ]
        ]
    })

    st.dataframe(status, use_container_width=True, hide_index=True)


elif page == "Supplier Risk":
    st.markdown(
        '<div class="section-title">Supplier Vulnerability Analysis</div>',
        unsafe_allow_html=True
    )

    if vulnerability is not None:
        st.dataframe(vulnerability, use_container_width=True, hide_index=True)

        nums = vulnerability.select_dtypes(include="number").columns.tolist()
        name = next(
            (c for c in vulnerability.columns
             if "supplier" in c.lower() or "component" in c.lower()),
            None
        )
        score = next(
            (c for c in nums if "score" in c.lower() or "risk" in c.lower()),
            None
        )

        if name and score:
            fig = px.bar(
                vulnerability,
                x=name,
                y=score,
                color=score,
                title="Supplier Vulnerability Score"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Supplier vulnerability data was not found.")

elif page == "Disruption Scenarios":
    st.markdown(
        '<div class="section-title">Disruption Scenarios</div>',
        unsafe_allow_html=True
    )

    if scenarios is not None:
        st.subheader("Scenario assumptions")
        st.dataframe(scenarios, use_container_width=True, hide_index=True)
        st.caption("Scenario values are modelling assumptions unless explicitly identified as event anchors in the source data.")

    if scenario_summary is not None:
        st.subheader("Scenario summary results")
        st.dataframe(scenario_summary, use_container_width=True, hide_index=True)

        num_cols = scenario_summary.select_dtypes(include="number").columns.tolist()
        scenario_col = next((c for c in scenario_summary.columns if "scenario" in c.lower() and c not in num_cols), None)
        unmet_col = next((c for c in num_cols if "unmet" in c.lower() or "short" in c.lower()), None)

        if scenario_col and unmet_col:
            fig = px.bar(
                scenario_summary,
                x=scenario_col,
                y=unmet_col,
                title="Unmet demand by scenario"
            )
            st.plotly_chart(fig, use_container_width=True)

    elif scenario_results is not None:
        st.subheader("Detailed scenario results")
        st.dataframe(scenario_results, use_container_width=True, hide_index=True)

    else:
        st.info("Add the scenario summary or results CSV generated by your notebook to this folder to view quantified scenario outcomes.")

elif page == "Procurement Optimization":
    st.markdown('<div class="section-title">Procurement Budget Optimization</div>', unsafe_allow_html=True)
    st.write("Explore how a tighter procurement budget changes order quantities and component shortages.")
    st.caption("This section uses your optimization output if available. It does not rerun the PuLP model inside the dashboard.")
    uploaded = st.file_uploader("Optional: upload the procurement optimization output CSV", type=["csv"], key="proc_upload")
    proc = pd.read_csv(uploaded) if uploaded is not None else load_csv("procurement_optimization_results.csv")
    if proc is not None:
        st.dataframe(proc, use_container_width=True, hide_index=True)
        num_cols = proc.select_dtypes(include="number").columns.tolist()
        budget_col = next((c for c in proc.columns if "budget scenario" in c.lower()), None)
        short_col = next((c for c in num_cols if "short" in c.lower()), None)
        order_col = next((c for c in num_cols if "ordered" in c.lower()), None)
        component_col = next((c for c in proc.columns if "component" in c.lower() and c != "component_id"), None)
        if budget_col and short_col:
            summary = proc.groupby(budget_col, as_index=False)[short_col].sum()
            fig = px.bar(summary, x=budget_col, y=short_col, title="Total component shortage by budget scenario")
            st.plotly_chart(fig, use_container_width=True)
        if component_col and short_col:
            fig = px.bar(proc, x=component_col, y=short_col, color=budget_col if budget_col else None, barmode="group", title="Shortage by component")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("The optimization table you shared can be exported from your notebook as procurement_optimization_results.csv and uploaded here, or saved beside app.py.")
        st.markdown("**Export from your notebook:** `optimization_df.to_csv('procurement_optimization_results.csv', index=False)`")

elif page == "Inventory & Logistics":
    st.markdown('<div class="section-title">Inventory & Logistics</div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Inventory position")
        if inventory is not None:
            cols = [c for c in ["component_name", "avg_daily_demand_units", "lead_time_days", "on_hand_inventory_units", "safety_stock_units", "reorder_point_units"] if c in inventory.columns]
            st.dataframe(inventory[cols], use_container_width=True, hide_index=True)
            if {"component_name", "on_hand_inventory_units", "safety_stock_units"}.issubset(inventory.columns):
                plot_df = inventory.melt(id_vars="component_name", value_vars=["on_hand_inventory_units", "safety_stock_units"], var_name="Inventory measure", value_name="Units")
                fig = px.bar(plot_df, x="component_name", y="Units", color="Inventory measure", barmode="group", title="On-hand inventory vs safety stock")
                st.plotly_chart(fig, use_container_width=True)
        else: st.info("Supply chain disruption Portfolio/inventory_demand_synthetic.csv not found.")
    with right:
        st.subheader("Transport route options")
        if transport is not None:
            st.dataframe(transport, use_container_width=True, hide_index=True)
            if {"transport_mode", "transit_time_days"}.issubset(transport.columns):
                fig = px.scatter(transport, x="transit_time_days", y="cost_per_shipment_usd" if "cost_per_shipment_usd" in transport else "transit_time_days", color="transport_mode", hover_name="route_id" if "route_id" in transport else None, title="Route transit time and cost")
                st.plotly_chart(fig, use_container_width=True)
        else: st.info("Supply chain disruption Portfolio/transport_routes_synthetic.csv not found.")

elif page == "Data Quality & Notes":
    st.markdown('<div class="section-title">Data Quality & Modelling Notes</div>', unsafe_allow_html=True)
    st.warning("This is a portfolio prototype, not a live Hyundai operational system. Supplier, inventory, transport and optimization datasets are synthetic/illustrative unless explicitly marked otherwise.")
    st.markdown("""
    **Interpretation rules**
    - Public Hyundai disclosures establish the Mobis facility fire and the company's stated operational response.
    - Scenario durations, capacity reductions, alternate-source capacity and simulated shortages are assumptions unless a source explicitly says otherwise.
    - Procurement optimization results are recommendations under the model's constraints, not actual purchase orders.
    - A solver status of `Optimal` means the mathematical model found the best solution for the defined objective and constraints; it does not prove the assumptions are realistic.
    - Check that the procurement budget, component demand, supplier capacity and shortage penalties use consistent units and time periods.
    """)
    st.subheader("Files detected beside app.py")
    detected = sorted(p.name for p in BASE_DIR.glob("*.csv"))
    st.write(detected if detected else "No CSV files detected.")

st.divider()
st.markdown('<div class="small-note">Cognitive Supply Chain Resilience | Analytical prototype | Synthetic assumptions are explicitly identified</div>', unsafe_allow_html=True)
