from openai import OpenAI

from app.core.config import settings


def _fallback_document(prompt: str) -> str:
    return (
        "OpenAI API key is not configured. This is a development fallback document.\n\n"
        + prompt[:1200]
    )


def generate_text(prompt: str) -> str:
    api_key = (settings.openai_api_key or "").strip()
    if not api_key or api_key.startswith("your-"):
        return _fallback_document(prompt)

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=settings.openai_model,
            input=prompt,
        )
        return response.output_text
    except Exception:
        return _fallback_document(prompt)
