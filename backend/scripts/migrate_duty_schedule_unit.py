"""Migration thu cong: them truong don vi / cuong vi / quan so cho `duty_schedules`.

`Base.metadata.create_all` chi tao bang moi, KHONG them cot vao bang cu -> can
script nay cho DB da co bang `duty_schedules`. Idempotent, KHONG xoa du lieu.

    venv/Scripts/python.exe scripts/migrate_duty_schedule_unit.py

Lam (chi them cot con thieu):
  - duty_schedules.week_plan_id      INT NULL  (FK duty_week_plans.id - bang truc tuan cha)
  - duty_schedules.unit_id           INT NULL  (FK units.id - don vi dam nhiem ca truc)
  - duty_schedules.duty_type         VARCHAR(30) NOT NULL DEFAULT 'khac' (nhom cuong vi)
  - duty_schedules.contact_phone     VARCHAR(30) NULL  (SDT vi tri truc)
  - duty_schedules.personnel_present INT NULL  (quan so co mat)
  - duty_schedules.personnel_total   INT NULL  (tong quan so bien che vi tri truc)

Bang `duty_week_plans` (bang truc tuan theo don vi) do `Base.metadata.create_all`
tu tao - script nay chi lo phan them cot vao bang `duty_schedules` cu.
Ban ghi cu -> week_plan_id = NULL, unit_id = NULL, duty_type = 'khac' (chi chi huy
Lu doan + don vi so huu nhin thay tren bang tong hop). Chi huy bo sung dan qua UI.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

TABLE = "duty_schedules"
COLUMNS = {
    "week_plan_id": "INT NULL",
    "unit_id": "INT NULL",
    "duty_type": "VARCHAR(30) NOT NULL DEFAULT 'khac'",
    "contact_phone": "VARCHAR(30) NULL",
    "personnel_present": "INT NULL",
    "personnel_total": "INT NULL",
}
# ten FK -> (cot, bang tham chieu)
FOREIGN_KEYS = {
    "fk_duty_schedules_unit_id": ("unit_id", "units(id)"),
    "fk_duty_schedules_week_plan_id": ("week_plan_id", "duty_week_plans(id)"),
}


def cols(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    )
    return {r[0] for r in rows}


def fk_names(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
            "AND REFERENCED_TABLE_NAME IS NOT NULL"
        ),
        {"t": table},
    )
    return {r[0] for r in rows}


def main() -> None:
    with engine.begin() as conn:
        have = cols(conn, TABLE)
        added = []
        for name, ddl in COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE {TABLE} ADD COLUMN `{name}` {ddl}"))
                added.append(name)

        have_now = cols(conn, TABLE)
        existing_fks = fk_names(conn, TABLE)
        fk_added = []
        for fk_name, (column, ref) in FOREIGN_KEYS.items():
            if column in have_now and fk_name not in existing_fks:
                try:
                    conn.execute(
                        text(
                            f"ALTER TABLE {TABLE} ADD CONSTRAINT {fk_name} "
                            f"FOREIGN KEY ({column}) REFERENCES {ref}"
                        )
                    )
                    fk_added.append(fk_name)
                except Exception as exc:  # noqa: BLE001
                    print(f"  (bo qua rang buoc {fk_name}: {exc})")

    print(f"{TABLE} (cot moi) : {added or 'khong co (da day du)'}")
    print(f"{TABLE} FK moi    : {fk_added or 'khong co (da day du / bo qua)'}")
    print("Hoan tat. Ban ghi cu: week_plan_id = NULL, unit_id = NULL, duty_type = 'khac'.")


if __name__ == "__main__":
    main()
