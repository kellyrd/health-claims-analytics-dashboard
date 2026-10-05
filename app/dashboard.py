import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import func

from app.database import init_db, SessionLocal
from app.sample_data import load_sample_data
from app.models import Claim, Group

from app.analytics import (
    calculate_total_paid,
    find_advanced_funding_claimants,
    find_claimants_above_deductible,
    get_monthly_paid_totals,
    get_group_deductibles,
    get_top_diagnosis_cost_drivers,
    get_top_procedure_cost_drivers,
    get_top_provider_cost_drivers,
    get_top_pos_cost_drivers,
    get_predictive_stop_loss_exposure,
    get_high_risk_claimants
)

# ---------------------------------------------------------
# Initialize DB and load sample data if empty
# ---------------------------------------------------------
init_db()

session = SessionLocal()
if session.query(Claim).count() == 0:
    load_sample_data()
session.close()

# ---------------------------------------------------------
# PAGE NAVIGATION STATE
# ---------------------------------------------------------
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "overview"  # overview or detail

# ---------------------------------------------------------
# GROUP LIST
# ---------------------------------------------------------
session = SessionLocal()
groups = session.query(Group).all()
session.close()

group_options = {g.group_name: g.group_id for g in groups}

# ---------------------------------------------------------
# PAGE 1 — GROUP OVERVIEW
# ---------------------------------------------------------
if st.session_state.view_mode == "overview":
    st.title("Group Overview Dashboard")

    # Build overview table
    overview_data = []
    for g in groups:
        total_paid = calculate_total_paid(g.group_id)
        agg_spec, ind_spec = get_group_deductibles(g.group_id)

        pct_agg = total_paid / agg_spec if agg_spec > 0 else 0

        exposure = get_predictive_stop_loss_exposure(g.group_id, agg_spec, ind_spec)

        overview_data.append({
            "Group Name": g.group_name,
            "Individual Spec Ded": ind_spec,
            "Aggregate Spec Ded": agg_spec,
            "Total Paid": total_paid,
            "% of Agg Ded": pct_agg,
            "Risk Category": exposure["risk_category"]
        })

    df_overview = pd.DataFrame(overview_data)

    # Format
    df_overview["Individual Spec Ded"] = df_overview["Individual Spec Ded"].apply(lambda x: f"${x:,.0f}")
    df_overview["Aggregate Spec Ded"] = df_overview["Aggregate Spec Ded"].apply(lambda x: f"${x:,.0f}")
    df_overview["Total Paid"] = df_overview["Total Paid"].apply(lambda x: f"${x:,.2f}")
    df_overview["% of Agg Ded"] = df_overview["% of Agg Ded"].apply(lambda x: f"{x*100:,.1f}%")

    st.dataframe(df_overview, width="stretch")

    # Group selector for drill-down
    selected_group_name = st.selectbox("Select a group to drill down", list(group_options.keys()))
    if st.button("View Group Details"):
        st.session_state.view_mode = "detail"
        st.session_state.selected_group_id = group_options[selected_group_name]
        st.session_state.selected_group_name = selected_group_name
        st.stop()  # Correct navigation

# ---------------------------------------------------------
# PAGE 2 — GROUP DETAIL
# ---------------------------------------------------------
else:
    selected_group_id = st.session_state.selected_group_id
    selected_group_name = st.session_state.selected_group_name

    agg_spec, ind_spec = get_group_deductibles(selected_group_id)
    agg_target = agg_spec * 0.65

    st.title(f"{selected_group_name} — Group Detail")

    if st.button("Back to Overview"):
        st.session_state.view_mode = "overview"
        st.stop()  # Correct navigation

    # ---------------------------------------------------------
    # Group Deductible Overview
    # ---------------------------------------------------------
    st.subheader("Group Deductible Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Individual Specific Deductible", f"${ind_spec:,.0f}")

    with col2:
        st.metric("Aggregate Specific Deductible", f"${agg_spec:,.0f}")

    # ---------------------------------------------------------
    # Total Paid Claims
    # ---------------------------------------------------------
    total_paid = calculate_total_paid(selected_group_id)
    st.subheader("Total Claims Paid")
    st.metric("Total Paid", f"${total_paid:,.2f}")

    # ---------------------------------------------------------
    # Advanced Funding Claimants
    # ---------------------------------------------------------
    st.subheader("Advanced Funding Claimants (>$5,000)")

    advanced_funding = find_advanced_funding_claimants(selected_group_id)
    df_af = pd.DataFrame(advanced_funding, columns=["Claimant ID", "Amount Paid"])
    st.dataframe(df_af, width="stretch")

    if not df_af.empty:
        st.download_button(
            "Download Advanced Funding CSV",
            df_af.to_csv(index=False),
            "advanced_funding.csv",
            "text/csv"
        )

    # ---------------------------------------------------------
    # Monthly Trend Line
    # ---------------------------------------------------------
    st.subheader("Monthly Paid Claims Trend vs 65% Agg Spec Deductible")

    monthly_totals = get_monthly_paid_totals(selected_group_id)

    if monthly_totals:
        df_trend = pd.DataFrame(monthly_totals, columns=["Month", "Total Paid"])
        df_trend["Month"] = pd.to_datetime(df_trend["Month"])
        df_trend["Agg Spec Target"] = agg_target

        trend_line = alt.Chart(df_trend).mark_line(point=True).encode(
            x="Month:T",
            y="Total Paid:Q",
            tooltip=["Month", "Total Paid"]
        )

        target_line = alt.Chart(df_trend).mark_line(
            strokeDash=[5, 5],
            color="red"
        ).encode(
            x="Month:T",
            y="Agg Spec Target:Q"
        )

        st.altair_chart(trend_line + target_line, width="stretch")

    # ---------------------------------------------------------
    # Aggregate Deductible Check
    # ---------------------------------------------------------
    session = SessionLocal()
    total_group_paid = session.query(func.sum(Claim.paid_amount))\
        .filter(Claim.group_id == selected_group_id).scalar() or 0
    session.close()

    if total_group_paid >= agg_spec:
        st.success(f"{selected_group_name} has HIT the Aggregate Specific Deductible (${agg_spec:,.0f}).")
    else:
        st.info(f"{selected_group_name} has NOT hit the Aggregate Specific Deductible (${agg_spec:,.0f}).")

    # ---------------------------------------------------------
    # Specific Deductible Claimants
    # ---------------------------------------------------------
    st.subheader("Claimants Above Specific Deductible")

    deductible_claimants = find_claimants_above_deductible(selected_group_id, ind_spec)

    if deductible_claimants:
        df_spec = pd.DataFrame(deductible_claimants, columns=["Claimant ID", "Total Paid"])
        st.dataframe(df_spec, width="stretch")

        st.download_button(
            "Download Specific Deductible CSV",
            df_spec.to_csv(index=False),
            "specific_deductible_claimants.csv",
            "text/csv"
        )
    else:
        st.info("No claimants found above this deductible.")

    # ---------------------------------------------------------
    # 50% Specific Deductible Claimants
    # ---------------------------------------------------------
    st.subheader("Claimants Above 50% of Individual Specific Deductible")

    half_deductible = ind_spec * 0.50
    half_spec_claimants = find_claimants_above_deductible(selected_group_id, half_deductible)

    if half_spec_claimants:
        df_half_spec = pd.DataFrame(half_spec_claimants, columns=["Claimant ID", "Total Paid"])
        st.dataframe(df_half_spec, width="stretch")

        st.download_button(
            "Download 50% Specific Deductible CSV",
            df_half_spec.to_csv(index=False),
            "half_specific_deductible_claimants.csv",
            "text/csv"
        )
    else:
        st.info("No claimants have reached 50% of the specific deductible.")

    # ---------------------------------------------------------
    # Cost Driver Analysis
    # ---------------------------------------------------------
    st.subheader("Cost Driver Analysis")

    df_diag = pd.DataFrame(get_top_diagnosis_cost_drivers(selected_group_id),
                           columns=["Diagnosis Code", "Total Paid"])
    df_diag["Total Paid"] = df_diag["Total Paid"].apply(lambda x: f"${x:,.2f}")
    st.write("### Top Diagnosis Codes")
    st.dataframe(df_diag, width="stretch")

    df_proc = pd.DataFrame(get_top_procedure_cost_drivers(selected_group_id),
                           columns=["Procedure Code", "Total Paid"])
    df_proc["Total Paid"] = df_proc["Total Paid"].apply(lambda x: f"${x:,.2f}")
    st.write("### Top Procedure Codes")
    st.dataframe(df_proc, width="stretch")

    df_prov = pd.DataFrame(get_top_provider_cost_drivers(selected_group_id),
                           columns=["Provider Name", "Total Paid"])
    df_prov["Total Paid"] = df_prov["Total Paid"].apply(lambda x: f"${x:,.2f}")
    st.write("### Top Providers")
    st.dataframe(df_prov, width="stretch")

    df_pos = pd.DataFrame(get_top_pos_cost_drivers(selected_group_id),
                          columns=["Place of Service", "Total Paid"])
    df_pos["Total Paid"] = df_pos["Total Paid"].apply(lambda x: f"${x:,.2f}")
    st.write("### Top Places of Service")
    st.dataframe(df_pos, width="stretch")

    # ---------------------------------------------------------
    # High-Risk Claimant Watchlist
    # ---------------------------------------------------------
    st.subheader("High-Risk Claimant Watchlist")

    risk_list = get_high_risk_claimants(selected_group_id, ind_spec)

    if risk_list:
        df_risk = pd.DataFrame(risk_list)
        df_risk["Total Paid"] = df_risk["Total Paid"].apply(lambda x: f"${x:,.2f}")
        df_risk["% of Spec Ded"] = df_risk["% of Spec Ded"].apply(lambda x: f"{x*100:,.1f}%")

        st.dataframe(df_risk, width="stretch")

        st.download_button(
            "Download High-Risk Claimant Watchlist CSV",
            df_risk.to_csv(index=False),
            "high_risk_claimant_watchlist.csv",
            "text/csv"
        )
    else:
        st.info("No high-risk claimants identified.")

    # ---------------------------------------------------------
    # Predictive Stop-Loss Exposure
    # ---------------------------------------------------------
    st.subheader("Predictive Stop-Loss Exposure")

    exposure = get_predictive_stop_loss_exposure(selected_group_id, agg_spec, ind_spec)

    st.write(f"**Risk Category:** {exposure['risk_category']}")
    st.write(f"**Probability of Hitting Specific Deductible:** {exposure['prob_hit_specific']*100:,.1f}%")
    st.write(f"**Probability of Hitting Aggregate Deductible:** {exposure['prob_hit_aggregate']*100:,.1f}%")
    st.write(f"**Expected Next-Year Paid Claims:** ${exposure['expected_next_year_paid']:,.2f}")

    factors = exposure["factors"]
    st.write("**Underlying Risk Factors:**")
    st.write(f"- Total Paid (current year): ${factors['total_paid']:,.2f}")
    st.write(f"- Chronic Claimants (≥3 claims): {factors['chronic_claimants']}")
    st.write(f"- High-Cost Claimants (> $25,000): {factors['high_cost_claimants']}")
    st.write(f"- Trend Velocity (first→last month): {factors['trend_velocity']*100:,.1f}%")
