"""Published Aevum testnet values. Override only the RPC or database path."""

from __future__ import annotations

import os

AEVUM_CHAIN_ID = 44005
AEVUM_CHAIN_HEX = "0xabe5"
TUSD8 = "0x456569838f1d43009A91ebA4263147Afd7233483"
TUSD8_DECIMALS = 6
DEFAULT_RPC = "https://rpc-test.qday.info"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def rpc_url() -> str:
    return os.getenv("AEVUM_RPC_URL", DEFAULT_RPC).strip() or DEFAULT_RPC


def invoice_db_path() -> str:
    return os.getenv("AEVUM_INVOICE_DB", "aevum_invoices.sqlite").strip()
