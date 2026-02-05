import asyncio
from typing import Any

from litellm import acompletion

from .configs import settings
from .schemas import LLMModel, LLMProvider


async def get_llm_response(llm_model: LLMModel, messages: list[Any]):
    response = await acompletion(
        base_url=llm_model.provider.base_url,
        api_key=llm_model.provider.api_key,
        model=llm_model.model,
        messages=messages,
    )
    return response


if __name__ == "__main__":
    print(settings)
    llm_provider = LLMProvider(
        base_url=settings.llm.base_url, api_key=settings.llm.api_key
    )
    llm_model = LLMModel(provider=llm_provider, model=settings.llm.model)
    response = asyncio.run(
        get_llm_response(
            llm_model, [{"content": "Hello, how are you?", "role": "user"}]
        )
    )
    print(response)
