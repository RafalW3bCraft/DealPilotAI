"""Invoice records. Amounts are integer tUSD8 units, 6 decimals, never floats."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .errors import InvoiceNotFound


def atomic_from_units(whole: str) -> int:
    """Convert a decimal string such as '1.50' into 6-decimal token units."""
    text = whole.strip()
    if not text or text.startswith("-") or text.startswith("+"):
        raise ValueError("amount must be a positive decimal")
    if text.count(".") > 1:
        raise ValueError("amount must be a positive decimal")
    whole_part, _, frac = text.partition(".")
    if not whole_part:
        whole_part = "0"
    if not whole_part.isdigit() or (frac and not frac.isdigit()):
        raise ValueError("amount must be a positive decimal")
    if len(frac) > 6:
        raise ValueError("tUSD8 supports 6 decimal places")
    units = int(whole_part) * 1_000_000 + int(frac.ljust(6, "0") or "0")
    if units <= 0:
        raise ValueError("amount must be positive")
    return units


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    merchant: str
    amount_atomic: int
    status: str
    tx_hash: str | None


class InvoiceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS aevum_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    merchant TEXT NOT NULL,
                    amount_atomic INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS aevum_tx_hash
                ON aevum_invoices(tx_hash) WHERE tx_hash IS NOT NULL
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path)
        try:
            connection.row_factory = sqlite3.Row
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create(self, merchant: str, amount_atomic: int) -> Invoice:
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            merchant=_checksum_lower(merchant),
            amount_atomic=amount_atomic,
            status="awaiting_payment",
            tx_hash=None,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO aevum_invoices
                (invoice_id, merchant, amount_atomic, status, tx_hash)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (invoice.invoice_id, invoice.merchant, invoice.amount_atomic, invoice.status),
            )
        return invoice

    def get(self, invoice_id: str) -> Invoice:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM aevum_invoices WHERE invoice_id = ?",
                (invoice_id,),
            ).fetchone()
        if row is None:
            raise InvoiceNotFound(invoice_id)
        return _row(row)

    def find_by_tx(self, tx_hash: str) -> Invoice | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM aevum_invoices WHERE tx_hash = ?",
                (tx_hash.lower(),),
            ).fetchone()
        return _row(row) if row is not None else None

    def mark(self, invoice_id: str, status: str, tx_hash: str | None) -> Invoice:
        stored_hash = tx_hash.lower() if tx_hash else None
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE aevum_invoices
                SET status = ?, tx_hash = ?
                WHERE invoice_id = ?
                """,
                (status, stored_hash, invoice_id),
            )
        return self.get(invoice_id)


def _checksum_lower(address: str) -> str:
    text = address.strip()
    if not text.startswith("0x") or len(text) != 42:
        raise ValueError("merchant must be a 20-byte hex address")
    try:
        int(text[2:], 16)
    except ValueError as exc:
        raise ValueError("merchant must be a 20-byte hex address") from exc
    return text.lower()


def _row(row: sqlite3.Row) -> Invoice:
    return Invoice(
        invoice_id=row["invoice_id"],
        merchant=row["merchant"],
        amount_atomic=row["amount_atomic"],
        status=row["status"],
        tx_hash=row["tx_hash"],
    )
