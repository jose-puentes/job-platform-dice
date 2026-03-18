from app.services.prompt_templates import DEFAULT_TEMPLATES


def test_default_templates_include_resume_and_cover_letter() -> None:
    assert "resume" in DEFAULT_TEMPLATES
    assert "cover_letter" in DEFAULT_TEMPLATES

