"""Durable Telegraph receipts. A restarted process reads the same SQLite file."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .schemas import Receipt


class ReceiptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS telegraph_receipts (
                    idempotency_key TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    amount_atomic INTEGER NOT NULL,
                    network TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    pay_to TEXT NOT NULL,
                    miner_id TEXT NOT NULL,
                    signal_hash TEXT NOT NULL,
                    price_usd TEXT NOT NULL,
                    paid INTEGER NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def get(self, idempotency_key: str) -> Receipt | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM telegraph_receipts WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
        if row is None:
            return None
        return Receipt(
            idempotency_key=row["idempotency_key"],
            workflow_id=row["workflow_id"],
            intent=row["intent"],
            params=json.loads(row["params_json"]),
            amount_atomic=row["amount_atomic"],
            network=row["network"],
            asset=row["asset"],
            pay_to=row["pay_to"],
            miner_id=row["miner_id"],
            signal_hash=row["signal_hash"],
            price_usd=row["price_usd"],
            paid=bool(row["paid"]),
        )

    def save(self, receipt: Receipt) -> Receipt:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO telegraph_receipts (
                    idempotency_key, workflow_id, intent, params_json, amount_atomic,
                    network, asset, pay_to, miner_id, signal_hash, price_usd, paid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO NOTHING
                """,
                (
                    receipt.idempotency_key,
                    receipt.workflow_id,
                    receipt.intent,
                    json.dumps(receipt.params, sort_keys=True),
                    receipt.amount_atomic,
                    receipt.network,
                    receipt.asset,
                    receipt.pay_to,
                    receipt.miner_id,
                    receipt.signal_hash,
                    receipt.price_usd,
                    1 if receipt.paid else 0,
                ),
            )
        stored = self.get(receipt.idempotency_key)
        return stored or receipt
