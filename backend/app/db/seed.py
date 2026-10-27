"""Seeding the crop reference into the database.

The crops and their growth stages are not user data; they come from the study's
agronomic reference files and must match what the prediction path computes. This
module reads them from the same :class:`~ml.crop_reference.CropCoefficientModel`
that the baseline uses, so the database and the calculation cannot disagree
about which crops exist or how long their stages are.

Seeding is idempotent: running it twice updates rather than duplicates.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Crop, CropGrowthStage
from ml.logging_utils import get_logger

log = get_logger("api.seed")

#: Categories for display. The reference files do not carry one.
CROP_CATEGORIES: dict[str, str] = {
    "paddy": "cereal",
    "maize": "cereal",
    "wheat": "cereal",
    "finger_millet": "millet",
    "groundnut": "oilseed",
    "cotton": "fibre",
    "chickpea": "pulse",
    "cumin": "spice",
}


def seed_crops(db: Session) -> dict[str, Any]:
    """Load every crop that has a complete coefficient curve."""
    from app.services.baseline_service import get_kc_model

    kc_model = get_kc_model()
    stage_table = kc_model.to_frame()

    created = updated = 0
    for slug in kc_model.crops:
        rows = stage_table[stage_table["crop"] == slug].sort_values("stage_order")
        display_name = str(rows.iloc[0]["display_name"])
        source = str(rows.iloc[0]["source"])
        cycle = int(kc_model.cycle_length(slug))

        crop = db.scalar(select(Crop).where(Crop.slug == slug))
        if crop is None:
            crop = Crop(
                slug=slug, name=display_name,
                category=CROP_CATEGORIES.get(slug),
                cycle_length_days=cycle, reference_source=source,
            )
            db.add(crop)
            db.flush()
            created += 1
        else:
            crop.name = display_name
            crop.cycle_length_days = cycle
            crop.reference_source = source
            crop.category = CROP_CATEGORIES.get(slug, crop.category)
            updated += 1

        # Replace the stages wholesale. They are reference data, so an update to
        # the configuration should be reflected exactly rather than merged.
        for existing in list(crop.stages):
            db.delete(existing)
        db.flush()

        for row in rows.itertuples():
            db.add(
                CropGrowthStage(
                    crop_id=crop.id,
                    stage_name=str(row.stage),
                    stage_order=int(row.stage_order),
                    start_day=int(row.start_day),
                    end_day=int(row.end_day),
                    kc_value=None if row.kc_anchor is None or row.kc_anchor != row.kc_anchor
                    else float(row.kc_anchor),
                    kc_basis=str(row.kc_basis),
                    description=(
                        f"{row.stage.replace('_', ' ').title()}: days "
                        f"{int(row.start_day)} to {int(row.end_day)} after sowing."
                    ),
                )
            )

    db.commit()
    summary = {"crops_created": created, "crops_updated": updated,
               "crops_total": len(kc_model.crops)}
    log.info("seeded crop reference: %s", summary)
    return summary


def seed_demo_account(db: Session, *, email: str = "demo@jalachakra.example.com",
                      password: str = "demo-password-123") -> dict[str, Any]:
    """A worked example: one farmer, one farm, one field, one planting.

    Exists so a reviewer can exercise the prediction endpoint immediately
    instead of creating four records by hand first. It is clearly labelled and
    is only created when the account does not already exist.
    """
    import datetime as dt

    from app.core.security import hash_password
    from app.db.models import Farm, Farmer, Field, FieldCrop, User

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return {"created": False, "email": email, "note": "the demo account already exists"}

    user = User(email=email, password_hash=hash_password(password),
                full_name="Demo Farmer", role="researcher")
    db.add(user)
    db.flush()

    farmer = Farmer(user_id=user.id, full_name="Demo Farmer",
                    state="Karnataka", district="Tumakuru")
    db.add(farmer)
    db.flush()

    farm = Farm(farmer_id=farmer.id, name="Demo Farm", state="Karnataka",
                district="Tumakuru", latitude=13.34, longitude=77.10,
                total_area_ha=4.0)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="North Plot", area_ha=1.5,
                  soil_type="clay_loam", irrigation_method="drip",
                  irrigation_efficiency=0.90)
    db.add(field)
    db.flush()

    maize = db.scalar(select(Crop).where(Crop.slug == "maize"))
    planting_id = None
    if maize is not None:
        planting = FieldCrop(
            field_id=field.id, crop_id=maize.id,
            sowing_date=dt.date.today() - dt.timedelta(days=60),
            planting_area_ha=1.5,
            notes="Demo planting, sown 60 days ago so it sits in mid-season.",
        )
        db.add(planting)
        db.flush()
        planting_id = planting.id

    db.commit()
    log.info("created the demo account %s", email)
    return {
        "created": True, "email": email, "password": password,
        "farm_id": farm.id, "field_id": field.id, "field_crop_id": planting_id,
        "note": "Demo data for evaluating the API. Not real farm records.",
    }
