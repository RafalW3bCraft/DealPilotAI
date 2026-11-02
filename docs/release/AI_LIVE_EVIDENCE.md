# Live AI Evidence

**Date:** 2026-11-02  
**Source revision:** `6ae608c166a3bdf16e3225cbf939ccb1e9d81df0` plus uncommitted local worktree changes  
**State:** BLOCKED; genuine inference did not pass.

## Attempt

Command: `python scripts/ai_smoke.py`

Configured provider/model: Featherless, `Qwen/Qwen3.8-27B`. The request returned an empty assistant content string. `AIShoppingService` then correctly used its deterministic fallback. The smoke output reported `fallback=true` and exited with `REAL_AI_SMOKE=FAIL`; the sanitized output is in `docs/evidence/ai_smoke.json`.

A redacted metadata-only request using the same model had `finish_reason=stop`, zero content characters, and five completion tokens. A second smoke attempt with the configured Featherless default model `meta-llama/Meta-Llama-3.1-8B-Instruct` failed with `PermissionDeniedError`. No model response text or credentials are recorded here.

## Assessment

This does not satisfy the genuine AI requirement. The configured model returned no usable JSON, and the default model was denied. The evidence does not distinguish conclusively between an invalid/limited key, model entitlement, provider-side model behavior, or JSON-mode compatibility. Do not claim AI is working based on fallback output or mocked tests.

## Required operator action

1. Rotate the exposed Featherless API key and any other credentials that appeared in local session/tool output.
2. In the Featherless console, verify the replacement key has inference access and that the selected model is enabled for the account.
3. Select a model whose current Featherless documentation explicitly supports the OpenAI-compatible `response_format={"type":"json_object"}` request.
4. Set `AI_PROVIDER=featherless`, the supported `AI_MODEL`, and the new `FEATHERLESS_API_KEY` in a private environment.
5. Run `python scripts/ai_smoke.py` and require `fallback=false`, a real provider/model identity, valid catalog SKUs, and catalog-matching prices. Then run the multilingual/budget/cart/injection release smoke before marking G1 PASS.

An OpenAI route is an alternative only if an authorized key and a JSON-mode-capable model are supplied; it has not been tested here. No credential value is included in this report.
