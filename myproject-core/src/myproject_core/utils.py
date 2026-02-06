async def streamcallback_simple_print(text: str):
    """
    Simple StreamCallback function to display LLM content and reasoning chunks to terminal
    'end=""' prevents newlines between chunks.
    'flush=True' forces the character to appear immediately (ignoring output buffering).
    """
    print(text, end="", flush=True)
