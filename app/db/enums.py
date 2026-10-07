from enum import StrEnum


class AgeGroup(StrEnum):
    """Kelompok umur untuk kalkulasi daily limits."""

    CHILD_SCHOOL = "CHILD_SCHOOL"  # 7-12 tahun
    TEEN = "TEEN"  # 13-17 tahun
    YOUNG_ADULT = "YOUNG_ADULT"  # 18-39 tahun
    MATURE_ELDER = "MATURE_ELDER"  # 40+ tahun


class ConsumptionType(StrEnum):
    """Jenis konsumsi — menentukan unit default (gram vs ml)."""

    SOLID = "SOLID"
    LIQUID = "LIQUID"


class MeasurementType(StrEnum):
    """Cara sesuatu diukur — level abstraksi tertinggi.

    - SERVING: dari label produk (1 porsi = X gram/ml)
    - VOLUME:  ml (cairan)
    - WEIGHT:  gram (padatan)
    - CONTAINER: pakai wadah (glass, bowl, scoop, dll)
    """

    SERVING = "SERVING"
    VOLUME = "VOLUME"
    WEIGHT = "WEIGHT"
    CONTAINER = "CONTAINER"


class ContainerType(StrEnum):
    """Jenis wadah — tanpa size (size dipisah ke ContainerSize)."""

    GLASS = "GLASS"
    CUP = "CUP"
    BOTTLE = "BOTTLE"
    PLATE = "PLATE"
    BOWL = "BOWL"
    SPOON = "SPOON"
    SCOOP = "SCOOP"
    PIECE = "PIECE"
    SLICE = "SLICE"
    HANDFUL = "HANDFUL"
    PINCH = "PINCH"
    CUSTOM = "CUSTOM"


class ContainerSize(StrEnum):
    """Ukuran wadah — reusable across container types."""

    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
