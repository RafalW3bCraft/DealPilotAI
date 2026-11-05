# GitHub Actions Evidence

**Current state:** FAIL; there is no green run for the corrected working tree.

The public run for current HEAD `f758a163f2683d56c2c90bc85bcb9a653977c144` is [41413708891](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41413708891). It completed with failure in the **Unit and integration tests** step. The local failure was traced to the Playwright browser test: invalid viewport argument placement and an approval URL without the mock order token.

The local working tree now contains backend, storefront, auth, screenshot, and browser-test changes, and its complete isolated suite passes (152 passed, 0 failed, 0 skipped). None of these changes have been pushed or run by GitHub Actions. The earlier run [41409296241](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41409296241) on `2b7c45b` also failed, at the secret-scan stage. Therefore there is no successful Actions URL or CI PASS claim.

The workflow has least-privilege `contents: read` and receives no live AI, PayPal, Telegram, dashboard, or database secrets. GitHub CLI is not authenticated in this environment, and no repository write or workflow dispatch was performed. After reviewing and publishing the corrected candidate with authorization, rerun CI and record the successful URL and exact SHA here.
