from litellm import completion

from .configs import settings

if __name__ == "__main__":
    print(settings)

    response = completion(
        base_url=settings.llm.base_url,
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        messages=[{ "content": "Hello, how are you?","role": "user"}]
    )
    print(response)
