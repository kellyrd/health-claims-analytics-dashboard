from sqlalchemy import Column, Integer, Float, Date, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    group_number = Column(Integer, nullable=False)
    group_name = Column(String, nullable=False)

    agg_spec_deductible = Column(Integer, nullable=False)
    ind_spec_deductible = Column(Integer, nullable=False)

    plan_year = Column(Integer, nullable=False)


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, autoincrement=True)
    claimant_id = Column(Integer, nullable=False)
    group_id = Column(Integer, nullable=False)

    paid_amount = Column(Float, nullable=False)
    date_of_service = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=False)

    provider_name = Column(String, nullable=False)
    provider_type = Column(String, nullable=False)

    diagnosis_code = Column(String, nullable=False)
    procedure_code = Column(String, nullable=False)
    place_of_service = Column(String, nullable=False)

    plan_year = Column(Integer, nullable=False)
