# Live AI Evidence

- **Last live attempt:** 2026-11-02
- **Attempted source revision:** `2b7c45b87e404ea5dbf85e7abb07310a2ac196e9`
- **Current assessment:** 2026-11-05
- **State:** FAIL; genuine inference did not pass. No successful live request has been recorded on current HEAD.

## Attempt

Command: `python scripts/ai_smoke.py`

Configured provider/model: Featherless, `Qwen/Qwen3.8-27B`. The request returned an empty assistant content string. `AIShoppingService` then correctly used its deterministic fallback. The smoke output reported `fallback=true` and exited with `REAL_AI_SMOKE=FAIL`; the sanitized output is in `docs/evidence/ai_smoke.json`.

A redacted metadata-only request using the same model had `finish_reason=stop`, zero content characters, and five completion tokens. A second smoke attempt with the configured Featherless default model `meta-llama/Meta-Llama-3.1-8B-Instruct` failed with `PermissionDeniedError`. No model response text or credentials are recorded here.

## Assessment

This does not satisfy the genuine AI requirement. The configured model returned no usable JSON, and the default model was denied. The evidence does not distinguish conclusively between an invalid/limited key, model entitlement, provider-side model behavior, or JSON-mode compatibility. Do not claim AI is working based on fallback output or mocked tests.

## Required operator action

1. Rotate the exposed `FEATHERLESS_API_KEY` and any other credentials that appeared in local session/tool output.
2. In the Featherless console, verify the replacement key has inference access and that the selected model is enabled for the account.
3. Select a model whose current Featherless documentation explicitly supports the OpenAI-compatible `response_format={"type":"json_object"}` request.
4. Set `AI_PROVIDER=featherless`, the supported `AI_MODEL`, and the new `FEATHERLESS_API_KEY` in a private environment.
5. Run `python scripts/ai_smoke.py` and require `fallback=false`, a real provider/model identity, valid catalog SKUs, and catalog-matching prices. Then run the multilingual/budget/cart/injection release smoke before marking G1 PASS.

An OpenAI route is an alternative only if an authorized key and a JSON-mode-capable model are supplied; it has not been tested here. No credential value is included in this report.

The current assessment did not retry the live request because the prior verification documented credential exposure and required rotation first. The most recent recorded attempt remains a failure, not a PASS.
