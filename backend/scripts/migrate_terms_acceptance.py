from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal


def _has_column(db: Session, table: str, col: str) -> bool:
    rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == col for r in rows)  # (cid, name, type, notnull, dflt_value, pk)


def main() -> None:
    db: Session = SessionLocal()
    try:
        # SQLite simple migration: add columns if missing
        if not _has_column(db, "users", "terms_accepted_at"):
            db.execute(text("ALTER TABLE users ADD COLUMN terms_accepted_at DATETIME"))
        if not _has_column(db, "users", "terms_version"):
            db.execute(text("ALTER TABLE users ADD COLUMN terms_version VARCHAR(64)"))
        db.commit()
        print("Migration OK: terms acceptance columns ensured.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

