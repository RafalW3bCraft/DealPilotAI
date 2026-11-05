# Release Gate Matrix

- **Reviewed:** 2026-11-05
- **Branch/current HEAD:** `main` / `f758a163f2683d56c2c90bc85bcb9a653977c144`
- **Worktree:** contains uncommitted backend, storefront, test, and release-record changes. Local PASS results below apply to this worktree, not a published commit.
- **Rule:** PASS means independently executed. BLOCKED and NOT RUN are never counted as PASS.

| Gate | State | Evidence / reason |
|---|---|---|
| G1 - Genuine AI inference | FAIL | The last live Featherless attempt on 2026-11-02 produced unusable/empty model output and `fallback=true`; the default-model attempt was denied. No successful live request is evidenced. Reverification is blocked until exposed credentials are rotated. See [AI evidence](AI_LIVE_EVIDENCE.md). |
| G2 - Buyer-approved PayPal capture | BLOCKED | No buyer-approved sandbox order or completed capture is evidenced. Existing credentials must be rotated before another live attempt. See [PayPal evidence](PAYPAL_SANDBOX_EVIDENCE.md). |
| G3 - Persistence across restart | BLOCKED | No real captured payment exists in this verification to test receipt recovery against. |
| G4 - Verified webhook and durable retry | BLOCKED | Automated webhook/retry coverage exists, but no real signed sandbox delivery or scheduled retry execution is evidenced. See [webhook evidence](WEBHOOK_EVIDENCE.md). |
| G5 - Security | BLOCKED | Dependency audit passed, and route/auth regression tests pass. A credential exposure was recorded in the prior verification; rotation and a complete release security review remain required. |
| G6 - Automated tests | PASS | Fresh Python 3.14.2 virtual environment: 152 passed, 0 failed, 0 skipped; 76% targeted combined coverage. Ruff, compileall, `pip check`, dependency audit, JavaScript syntax, and diff checks pass. See [test report](TEST_REPORT.md). |
| G7 - Browser checkout journey | PASS | Playwright covers catalog recommendation/fallback disclosure, malicious AI text as text (no injected image), cart quote, mocked approval/capture, receipt, browser merchant login/logout, desktop and 390px mobile layout: 1 passed. External payment remains mocked. See [browser evidence](BROWSER_EVIDENCE.md). |
| G8 - Sandbox configuration | BLOCKED | Required nonempty entries exist in local dotenv, but their values were not used or disclosed; prior evidence requires credential rotation. Fresh configuration/OAuth validation is still required. |
| G9 - GitHub Actions | FAIL | Current HEAD run [41413708891](https://github.com/RafalW3bCraft/DealPilotAI/actions/runs/41413708891) failed the test job. The Playwright corrections that make the local suite pass are uncommitted, and no green run exists for the corrected source. See [CI evidence](CI_EVIDENCE.md). |
| G10 - README | BLOCKED | README now includes genuine local offline-mode landing/shop screenshots and accurately documents setup and limitations; the candidate remains uncommitted and therefore is not yet verified in the public submission branch. |
| G11 - Working judge demo/video | BLOCKED | No verified live AI/PayPal demo, hosted URL, or public YouTube video exists. The local offline/mock browser journey is not a substitute. |
| G12 - Devpost materials and links | BLOCKED | Draft submission is present; no verified public demo/video links or actual Devpost submission are evidenced. |

## Verdict

HACKATHON NOT READY — MANDATORY REQUIREMENTS FAILED. G1 and G9 are known failures; live payment, persistence, webhook, and public submission evidence is missing. Do not represent the repository as submission-ready until every mandatory gate is PASS.

**PRODUCTION NOT READY.** The application is sandbox-only and has no production merchant/payment operations certification.
