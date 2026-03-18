from openai import OpenAI

from app.core.config import settings


def generate_text(prompt: str) -> str:
    if not settings.openai_api_key:
        return (
            "OpenAI API key is not configured. This is a development fallback document.\n\n"
            + prompt[:1200]
        )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )
    return response.output_text

