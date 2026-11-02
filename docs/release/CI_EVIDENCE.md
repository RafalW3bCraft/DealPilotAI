# GitHub Actions Evidence

**State:** NOT RUN.

A local workflow is defined at `.github/workflows/ci.yml`. It has not been pushed, executed by GitHub Actions, or associated with a final submission SHA. Therefore there is no successful run URL and no CI PASS claim.

The workflow intentionally receives no PayPal, AI, Telegram, dashboard, or database secrets. It runs the pinned dev dependencies, compile/dependency checks, the configured Ruff correctness profile, tests/coverage, dependency audit, and secret scan. It must be pushed to the intended submission branch and observed green before G9 can pass.

No push or publication was performed in this workspace. After rotating credentials, publish only reviewed source and evidence; then record the actual successful GitHub Actions URL and exact candidate SHA here.
