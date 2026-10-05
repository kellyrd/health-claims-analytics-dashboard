from sqlalchemy import func
from app.database import SessionLocal
from app.models import Claim, Group
from math import exp

def calculate_total_paid(group_id):
    session = SessionLocal()
    total = session.query(func.sum(Claim.paid_amount)).filter(Claim.group_id == group_id).scalar()
    session.close()
    return total

def find_advanced_funding_claimants(group_id, threshold=5000):
    session = SessionLocal()
    results = (
        session.query(
            Claim.claimant_id,
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.claimant_id)
        .having(func.sum(Claim.paid_amount) > threshold)
        .all()
    )
    session.close()
    return results

def find_claimants_above_deductible(group_id, deductible):
    return find_advanced_funding_claimants(group_id, threshold=deductible)

def get_monthly_paid_totals(group_id):
    session = SessionLocal()
    results = (
        session.query(
            func.strftime("%Y-%m", Claim.paid_date).label("month"),
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by("month")
        .order_by("month")
        .all()
    )
    session.close()
    return results

def get_group_deductibles(group_id):
    session = SessionLocal()
    group = session.query(Group).filter(Group.group_id == group_id).first()
    session.close()
    return group.agg_spec_deductible, group.ind_spec_deductible

def get_top_diagnosis_cost_drivers(group_id, limit=5):
    session = SessionLocal()
    results = (
        session.query(
            Claim.diagnosis_code,
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.diagnosis_code)
        .order_by(func.sum(Claim.paid_amount).desc())
        .limit(limit)
        .all()
    )
    session.close()
    return results


def get_top_procedure_cost_drivers(group_id, limit=5):
    session = SessionLocal()
    results = (
        session.query(
            Claim.procedure_code,
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.procedure_code)
        .order_by(func.sum(Claim.paid_amount).desc())
        .limit(limit)
        .all()
    )
    session.close()
    return results


def get_top_provider_cost_drivers(group_id, limit=5):
    session = SessionLocal()
    results = (
        session.query(
            Claim.provider_name,
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.provider_name)
        .order_by(func.sum(Claim.paid_amount).desc())
        .limit(limit)
        .all()
    )
    session.close()
    return results


def get_top_pos_cost_drivers(group_id, limit=5):
    session = SessionLocal()
    results = (
        session.query(
            Claim.place_of_service,
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.place_of_service)
        .order_by(func.sum(Claim.paid_amount).desc())
        .limit(limit)
        .all()
    )
    session.close()
    return results

from math import exp

def _logistic(x):
    return 1 / (1 + exp(-x))


def get_group_risk_factors(group_id):
    session = SessionLocal()

    # Total paid
    total_paid = session.query(func.sum(Claim.paid_amount))\
        .filter(Claim.group_id == group_id).scalar() or 0

    # Chronic claimants: 3+ claims
    chronic = (
        session.query(Claim.claimant_id, func.count(Claim.claim_id))
        .filter(Claim.group_id == group_id)
        .group_by(Claim.claimant_id)
        .having(func.count(Claim.claim_id) >= 3)
        .count()
    )

    # High-cost claimants: > $25,000 total
    high_cost = (
        session.query(Claim.claimant_id, func.sum(Claim.paid_amount).label("total_paid"))
        .filter(Claim.group_id == group_id)
        .group_by(Claim.claimant_id)
        .having(func.sum(Claim.paid_amount) > 25000)
        .count()
    )

    # Trend velocity: last month vs first month
    monthly = (
        session.query(
            func.strftime("%Y-%m", Claim.paid_date).label("month"),
            func.sum(Claim.paid_amount).label("total_paid")
        )
        .filter(Claim.group_id == group_id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    trend_velocity = 0
    if len(monthly) >= 2:
        first = monthly[0].total_paid
        last = monthly[-1].total_paid
        if first > 0:
            trend_velocity = (last - first) / first

    session.close()

    return {
        "total_paid": total_paid,
        "chronic_claimants": chronic,
        "high_cost_claimants": high_cost,
        "trend_velocity": trend_velocity,
    }


def get_predictive_stop_loss_exposure(group_id, agg_spec_ded, ind_spec_ded):
    factors = get_group_risk_factors(group_id)

    # Simple scoring model
    score = 0

    # Scale total paid vs agg spec
    if agg_spec_ded > 0:
        score += (factors["total_paid"] / agg_spec_ded) * 1.5

    # Chronic claimants
    score += factors["chronic_claimants"] * 0.4

    # High-cost claimants
    score += factors["high_cost_claimants"] * 0.8

    # Trend velocity
    score += factors["trend_velocity"] * 2.0

    # Convert to probabilities via logistic
    prob_hit_specific = _logistic(score - 1.0)
    prob_hit_aggregate = _logistic(score - 0.5)

    # Simple expected next-year paid (scale current by trend + risk)
    expected_next_year_paid = factors["total_paid"] * (1 + max(factors["trend_velocity"], 0) + 0.2 * (factors["high_cost_claimants"]))

    # Risk category
    if score < 0.5:
        risk_category = "Low"
    elif score < 1.5:
        risk_category = "Moderate"
    else:
        risk_category = "High"

    return {
        "prob_hit_specific": prob_hit_specific,
        "prob_hit_aggregate": prob_hit_aggregate,
        "expected_next_year_paid": expected_next_year_paid,
        "risk_category": risk_category,
        "raw_score": score,
        "factors": factors,
    }
def get_high_risk_claimants(group_id, ind_spec_ded):
    session = SessionLocal()

    # Get all claimants and their totals
    claimant_totals = (
        session.query(
            Claim.claimant_id,
            func.sum(Claim.paid_amount).label("total_paid"),
            func.count(Claim.claim_id).label("claim_count")
        )
        .filter(Claim.group_id == group_id)
        .group_by(Claim.claimant_id)
        .all()
    )

    # High-risk diagnosis codes (simple starter list)
    high_risk_dx = {"C", "I", "N17", "N18", "J44", "K50", "K51"}  # cancer, cardiac, renal, COPD, Crohn’s, UC

    # Build risk list
    risk_list = []

    for claimant_id, total_paid, claim_count in claimant_totals:

        # Diagnosis codes for this claimant
        dx_codes = session.query(Claim.diagnosis_code)\
            .filter(Claim.claimant_id == claimant_id).all()
        dx_codes = [dx[0] for dx in dx_codes]

        # Risk factors
        pct_of_spec = total_paid / ind_spec_ded if ind_spec_ded > 0 else 0
        chronic = claim_count >= 3
        has_high_risk_dx = any(dx.startswith(tuple(high_risk_dx)) for dx in dx_codes)

        # Simple scoring model
        score = 0
        score += pct_of_spec * 2.0
        score += 0.5 if chronic else 0
        score += 1.0 if has_high_risk_dx else 0

        risk_list.append({
            "Claimant ID": claimant_id,
            "Total Paid": total_paid,
            "% of Spec Ded": pct_of_spec,
            "Chronic": chronic,
            "High-Risk DX": has_high_risk_dx,
            "Risk Score": score
        })

    session.close()

    # Sort descending by risk score
    risk_list = sorted(risk_list, key=lambda x: x["Risk Score"], reverse=True)

    return risk_list
