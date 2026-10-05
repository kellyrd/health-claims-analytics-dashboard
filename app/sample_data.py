from datetime import date
from app.models import Claim, Group
from app.database import SessionLocal

def load_sample_data():
    session = SessionLocal()

    # --- Insert Groups ---
    groups = [
        Group(group_number=5027, group_name="Town Pump", agg_spec_deductible=100000, ind_spec_deductible=50000, plan_year=2024),
        Group(group_number=5028, group_name="Jones Bros.", agg_spec_deductible=120000, ind_spec_deductible=55000, plan_year=2024),
        Group(group_number=5029, group_name="Taco John's", agg_spec_deductible=130000, ind_spec_deductible=60000, plan_year=2024),
        Group(group_number=5030, group_name="Missoula County", agg_spec_deductible=150000, ind_spec_deductible=65000, plan_year=2024),
        Group(group_number=5031, group_name="City of Helena", agg_spec_deductible=160000, ind_spec_deductible=70000, plan_year=2024),
        Group(group_number=5032, group_name="City of Missoula", agg_spec_deductible=180000, ind_spec_deductible=75000, plan_year=2024),
    ]

    session.add_all(groups)
    session.commit()

    # Map group_id after insert
    group_map = {g.group_number: g.group_id for g in session.query(Group).all()}

    # Assign claimants to groups
    claimant_groups = {
        2001: group_map[5027],  # Town Pump
        1001: group_map[5027],

        1004: group_map[5028],  # Jones Bros.
        3001: group_map[5028],

        1003: group_map[5029],  # Taco John's
        3002: group_map[5029],

        3003: group_map[5030],  # Missoula County
        4001: group_map[5030],

        3004: group_map[5031],  # City of Helena
        4002: group_map[5031],

        4003: group_map[5032],  # City of Missoula
        4004: group_map[5032],
        5001: group_map[5032],
        5002: group_map[5032],
        5003: group_map[5032],
        5004: group_map[5032],
    }

    # --- Insert Claims ---
    sample_claims = [
        # Town Pump (5027)
        Claim(claimant_id=2001, group_id=claimant_groups[2001], paid_amount=2400, date_of_service=date(2024,1,3), paid_date=date(2024,1,10),
              provider_name="Missoula Family Medicine Clinic", provider_type="Clinic", diagnosis_code="E11.9", procedure_code="99213",
              place_of_service="Office", plan_year=2024),
        Claim(claimant_id=2001, group_id=claimant_groups[2001], paid_amount=1800, date_of_service=date(2024,1,12), paid_date=date(2024,1,18),
              provider_name="Missoula Family Medicine Clinic", provider_type="Clinic", diagnosis_code="I10", procedure_code="80053",
              place_of_service="Office", plan_year=2024),
        Claim(claimant_id=2001, group_id=claimant_groups[2001], paid_amount=1600, date_of_service=date(2024,1,20), paid_date=date(2024,1,27),
              provider_name="Missoula Family Medicine Clinic", provider_type="Clinic", diagnosis_code="E78.5", procedure_code="36415",
              place_of_service="Office", plan_year=2024),

        Claim(claimant_id=1001, group_id=claimant_groups[1001], paid_amount=5700, date_of_service=date(2024,2,10), paid_date=date(2024,2,15),
              provider_name="Community Medical Center", provider_type="Urgent Care", diagnosis_code="S93.401A", procedure_code="73590",
              place_of_service="Urgent Care", plan_year=2024),

        # Jones Bros. (5028)
        Claim(claimant_id=1004, group_id=claimant_groups[1004], paid_amount=45000, date_of_service=date(2024,2,1), paid_date=date(2024,2,20),
              provider_name="St. Patrick Hospital", provider_type="Hospital", diagnosis_code="C50.911", procedure_code="77427",
              place_of_service="Inpatient Hospital", plan_year=2024),

        Claim(claimant_id=3001, group_id=claimant_groups[3001], paid_amount=3200, date_of_service=date(2024,1,8), paid_date=date(2024,1,14),
              provider_name="Missoula Internal Medicine", provider_type="Clinic", diagnosis_code="R53.83", procedure_code="85025",
              place_of_service="Office", plan_year=2024),

        # Taco John's (5029)
        Claim(claimant_id=1003, group_id=claimant_groups[1003], paid_amount=8500, date_of_service=date(2024,3,5), paid_date=date(2024,3,12),
              provider_name="Providence Health Urgent Care", provider_type="Hospital", diagnosis_code="J18.9", procedure_code="99285",
              place_of_service="Emergency Room", plan_year=2024),

        Claim(claimant_id=3002, group_id=claimant_groups[3002], paid_amount=4100, date_of_service=date(2024,2,14), paid_date=date(2024,2,22),
              provider_name="Rocky Mountain Orthopedics", provider_type="Specialist", diagnosis_code="M17.11", procedure_code="20610",
              place_of_service="Office", plan_year=2024),

        # Missoula County (5030)
        Claim(claimant_id=3003, group_id=claimant_groups[3003], paid_amount=2900, date_of_service=date(2024,3,2), paid_date=date(2024,3,9),
              provider_name="Missoula Primary Care", provider_type="Clinic", diagnosis_code="J06.9", procedure_code="87880",
              place_of_service="Office", plan_year=2024),

        Claim(claimant_id=4001, group_id=claimant_groups[4001], paid_amount=2200, date_of_service=date(2024,1,15), paid_date=date(2024,1,21),
              provider_name="Missoula Pediatrics", provider_type="Clinic", diagnosis_code="J45.909", procedure_code="94640",
              place_of_service="Office", plan_year=2024),

        # City of Helena (5031)
        Claim(claimant_id=3004, group_id=claimant_groups[3004], paid_amount=5100, date_of_service=date(2024,4,11), paid_date=date(2024,4,18),
              provider_name="Montana Surgical Center", provider_type="Surgery Center", diagnosis_code="K40.20", procedure_code="49505",
              place_of_service="Outpatient Surgery", plan_year=2024),

        Claim(claimant_id=4002, group_id=claimant_groups[4002], paid_amount=3600, date_of_service=date(2024,2,18), paid_date=date(2024,2,25),
              provider_name="Community Medical Center", provider_type="Urgent Care", diagnosis_code="N39.0", procedure_code="81001",
              place_of_service="Urgent Care", plan_year=2024),

        # City of Missoula (5032)
        Claim(claimant_id=4003, group_id=claimant_groups[4003], paid_amount=4800, date_of_service=date(2024,3,20), paid_date=date(2024,3,28),
              provider_name="Providence Health Urgent Care", provider_type="Hospital", diagnosis_code="R07.9", procedure_code="93000",
              place_of_service="Emergency Room", plan_year=2024),

        Claim(claimant_id=4004, group_id=claimant_groups[4004], paid_amount=5300, date_of_service=date(2024,4,6), paid_date=date(2024,4,14),
              provider_name="St. Patrick Hospital", provider_type="Hospital", diagnosis_code="K52.9", procedure_code="99284",
              place_of_service="Emergency Room", plan_year=2024),

        Claim(claimant_id=5001, group_id=claimant_groups[5001], paid_amount=1500, date_of_service=date(2024,1,22), paid_date=date(2024,1,29),
              provider_name="Missoula Family Medicine Clinic", provider_type="Clinic", diagnosis_code="E66.9", procedure_code="99401",
              place_of_service="Office", plan_year=2024),

        Claim(claimant_id=5002, group_id=claimant_groups[5002], paid_amount=2700, date_of_service=date(2024,2,3), paid_date=date(2024,2,10),
              provider_name="Community Medical Center", provider_type="Urgent Care", diagnosis_code="J02.9", procedure_code="87880",
              place_of_service="Urgent Care", plan_year=2024),

        Claim(claimant_id=5003, group_id=claimant_groups[5003], paid_amount=3900, date_of_service=date(2024,3,15), paid_date=date(2024,3,22),
              provider_name="Missoula Internal Medicine", provider_type="Clinic", diagnosis_code="E03.9", procedure_code="84443",
              place_of_service="Office", plan_year=2024),

        Claim(claimant_id=5004, group_id=claimant_groups[5004], paid_amount=6200, date_of_service=date(2024,4,19), paid_date=date(2024,4,26),
              provider_name="Montana Surgical Center", provider_type="Surgery Center", diagnosis_code="K80.20", procedure_code="47562",
              place_of_service="Outpatient Surgery", plan_year=2024),
    ]

    session.add_all(sample_claims)
    session.commit()
    session.close()
