import asyncio
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, cast

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.nutrition_reference import NutritionReference
from app.db.models.portion_reference import PortionReference
from app.db.models.scanned_product import ScannedProduct
from app.db.session import get_session_factory

SEEDS_DIR = ROOT_DIR / "seeds"


def load_json(filename: str) -> list[dict[str, Any]]:
    path = SEEDS_DIR / filename
    with open(path, encoding="utf-8") as f:
        data = cast(list[dict[str, Any]], json.load(f))
    print(f"  Loaded {len(data)} rows from {filename}")
    return data


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return None


async def seed_nutrition_references(session: AsyncSession, data: list[dict[str, Any]]) -> int:
    inserted = 0
    for item in data:
        existing = await session.get(NutritionReference, item["id"])
        if existing:
            continue
        payload = {**item}
        payload["effective_date"] = parse_date(payload.get("effective_date"))
        session.add(NutritionReference(**payload))
        inserted += 1
    await session.commit()
    return inserted


async def seed_portion_references(session: AsyncSession, data: list[dict[str, Any]]) -> int:
    inserted = 0
    for item in data:
        stmt = select(PortionReference).where(
            PortionReference.name == item["name"],
            PortionReference.measurement_type == item["measurement_type"],
            PortionReference.container_type == item["container_type"],
            PortionReference.container_size == item["container_size"],
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            continue
        session.add(PortionReference(**item))
        inserted += 1
    await session.commit()
    return inserted


async def seed_scanned_products(session: AsyncSession, data: list[dict[str, Any]]) -> int:
    inserted = 0
    for item in data:
        stmt = select(ScannedProduct).where(
            ScannedProduct.product_name == item["product_name"],
            ScannedProduct.brand == item["brand"],
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            continue
        session.add(ScannedProduct(**item))
        inserted += 1
    await session.commit()
    return inserted


async def main() -> None:
    print("=" * 70)
    print("SEEDING DATABASE")
    print("=" * 70)

    factory = get_session_factory()

    print("\n[1/3] nutrition_references")
    data = load_json("nutrition_references.json")
    async with factory() as session:
        n = await seed_nutrition_references(session, data)
    print(f"  Inserted: {n}, Skipped: {len(data) - n}")

    print("\n[2/3] scanned_products")
    data = load_json("scanned_products.json")
    async with factory() as session:
        n = await seed_scanned_products(session, data)
    print(f"  Inserted: {n}, Skipped: {len(data) - n}")

    print("\n[3/3] portion_references")
    data = load_json("portion_references.json")
    async with factory() as session:
        n = await seed_portion_references(session, data)
    print(f"  Inserted: {n}, Skipped: {len(data) - n}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
