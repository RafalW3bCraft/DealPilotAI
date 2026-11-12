from types import SimpleNamespace

from ai.agent import AIShoppingService


def test_featherless_auto_format_uses_prompt_with_strict_server_parser(monkeypatch):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(AIShoppingService, '_build_openai_client', staticmethod(lambda **_: client))
    cfg = SimpleNamespace(AI_PROVIDER='featherless', FEATHERLESS_API_KEY='test-only')
    service = AIShoppingService(cfg, object())
    assert service._call_provider([{'role': 'user', 'content': 'Return JSON'}]) == '{}'
    assert 'response_format' not in calls[0]


def test_explicit_json_mode_is_forwarded(monkeypatch):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(AIShoppingService, '_build_openai_client', staticmethod(lambda **_: client))
    cfg = SimpleNamespace(AI_PROVIDER='featherless', FEATHERLESS_API_KEY='test-only', AI_RESPONSE_FORMAT='json_object')
    AIShoppingService(cfg, object())._call_provider([])
    assert calls[0]['response_format'] == {'type': 'json_object'}
