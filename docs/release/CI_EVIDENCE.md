# GitHub Actions Evidence

**State:** FAIL; local remediation is uncommitted.

Run: https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41409296241
SHA: `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9`
Workflow: `CI`, completed 2026-11-02 with conclusion `failure`.

The run passed setup, dependency installation, compile, `pip check`, Ruff, 146 tests (0 failures, 6 warnings), coverage (76%), and dependency audit. Gitleaks failed because it misclassified blank API-key assignments in `docs/release/TEST_REPORT.md` as generic API keys. The assignments have been removed locally. This fix has not been pushed or rerun, so there is no successful Actions URL and no CI PASS claim.

The workflow intentionally receives no PayPal, AI, Telegram, dashboard, or database secrets. After rotating credentials, publish the reviewed remediation and current browser-test changes, then record the new run URL and exact successful SHA here.
