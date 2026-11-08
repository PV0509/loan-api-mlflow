"""Prediction history. SQLite file (ephemeral on Render free plan: resets on each deploy)."""
import os
import sqlite3
import threading
from datetime import UTC, datetime

DB_PATH = os.getenv("DB_PATH", "/tmp/predictions.db")
_lock = threading.Lock()
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.execute("""
create table if not exists predictions (
    id                  integer primary key autoincrement,
    created_at          text not null,
    income              real not null,
    loan_amount         real not null,
    loan_term           integer not null,
    credit_score        real not null,
    employment_years    integer not null,
    default_probability real not null,
    decision            text not null,
    model_version       text not null
)""")
_conn.commit()


def add(applicant: dict, prob: float, decision: str, model_version: str) -> dict:
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with _lock:
        cur = _conn.execute(
            "insert into predictions (created_at, income, loan_amount, loan_term, credit_score,"
            " employment_years, default_probability, decision, model_version)"
            " values (?,?,?,?,?,?,?,?,?)",
            (now, applicant["income"], applicant["loan_amount"], applicant["loan_term"],
             applicant["credit_score"], applicant["employment_years"], prob, decision, model_version))
        _conn.commit()
    return get(cur.lastrowid)


def get(pred_id: int) -> dict | None:
    row = _conn.execute("select * from predictions where id = ?", (pred_id,)).fetchone()
    return _to_dict(row) if row else None


def list_(limit: int, after_id: int) -> list[dict]:
    rows = _conn.execute("select * from predictions where id > ? order by id limit ?",
                         (after_id, limit)).fetchall()
    return [_to_dict(r) for r in rows]


def delete(pred_id: int) -> bool:
    with _lock:
        cur = _conn.execute("delete from predictions where id = ?", (pred_id,))
        _conn.commit()
    return cur.rowcount > 0


def _to_dict(r) -> dict:
    return {
        "id": r["id"],
        "created_at": r["created_at"],
        "applicant": {k: r[k] for k in ("income", "loan_amount", "loan_term",
                                        "credit_score", "employment_years")},
        "default_probability": r["default_probability"],
        "decision": r["decision"],
        "model_version": r["model_version"],
    }
