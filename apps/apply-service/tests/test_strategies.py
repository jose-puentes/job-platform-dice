from app.services.strategies import determine_apply_strategy


def test_strategy_uses_manual_assist_for_unknown_sources() -> None:
    strategy = determine_apply_strategy({"source": "unknown", "application_url": "https://example.com/apply"})
    assert strategy.value == "manual_assist"


def test_strategy_uses_external_redirect_for_greenhouse() -> None:
    strategy = determine_apply_strategy(
        {"source": "greenhouse", "application_url": "https://boards.greenhouse.io/company/jobs/1"}
    )
    assert strategy.value == "external_redirect"

