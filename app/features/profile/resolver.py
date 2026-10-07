from app.core.exceptions import ValidationError
from app.db.enums import AgeGroup

AGE_MIN = 7
AGE_MAX = 120


def resolve_age_group(age_years: int) -> AgeGroup:
    """Map age_years ke AgeGroup enum.

    Raises:
        ValidationError: kalau usia di luar range valid.
    """
    if age_years < AGE_MIN:
        raise ValidationError(
            code="AGE_TOO_YOUNG",
            message=f"Minimum usia {AGE_MIN} tahun",
        )
    if age_years > AGE_MAX:
        raise ValidationError(
            code="AGE_TOO_OLD",
            message=f"Maksimum usia {AGE_MAX} tahun",
        )
    if age_years <= 12:
        return AgeGroup.CHILD_SCHOOL
    if age_years <= 17:
        return AgeGroup.TEEN
    if age_years <= 25:
        return AgeGroup.YOUNG_ADULT
    return AgeGroup.MATURE_ELDER
