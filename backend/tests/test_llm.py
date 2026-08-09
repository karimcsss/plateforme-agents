import pytest
from app.llm.factory import get_llm_provider
from app.main import EchoResult


@pytest.mark.asyncio
async def test_structured_output():
    provider = get_llm_provider()
    result = await provider.complete_structured(
        system_prompt="Analyse ce texte et retourne des métadonnées via emit_result.",
        user_prompt="Bonjour, ceci est un test de trois mots.",
        response_model=EchoResult,
    )
    assert isinstance(result, EchoResult)
    assert result.word_count > 0