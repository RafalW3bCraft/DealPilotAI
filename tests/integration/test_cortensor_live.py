"""Opt-in OpenMinion echo turn. Echo is not a model-backed recommendation."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from integrations.cortensor.advisor import ProcurementAdvisor, OpenMinionRunner
from tests.commerce.test_cortensor import _catalog


pytestmark = pytest.mark.skipif(os.getenv("CORTENSOR_LIVE") != "1", reason="set CORTENSOR_LIVE=1")


def test_openminion_echo_turn_stays_catalog_priced(tmp_path):
    home = tmp_path / "openminion-home"
    home.mkdir()
    env = os.environ.copy()
    env["OPENMINION_HOME"] = str(home)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "openminion",
            "config",
            "init",
            "--provider",
            "echo",
            "--force",
            "--storage-location",
            "config",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    config = home / ".openminion" / "agents.json"
    assert config.is_file(), completed.stderr
    advice = ProcurementAdvisor(
        _catalog(),
        runner=OpenMinionRunner(str(config)),
        provider="echo",
    ).advise("headphones", budget="30")
    assert advice["model_backed"] is False
    assert advice["selected"]["sku"] == "HP-2"
    assert advice["quote"]["total"] == "25.00"
    assert advice["sdk_text"]
    evidence = Path("docs/hackathon-mania/evidence")
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "cortensor_echo.json").write_text(
        json.dumps(
            {
                "sdk": "openminion",
                "version": "0.1.20",
                "provider": "echo",
                "model_backed": False,
                "selected_sku": advice["selected"]["sku"],
                "quote_total": advice["quote"]["total"],
                "runtime_note": advice["runtime_note"],
            },
            indent=2,
        )
        + "\n"
    )
