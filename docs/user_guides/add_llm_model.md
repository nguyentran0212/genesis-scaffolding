# Adding and using LLM Models

This system uses the LiteLLM SDK to interact with LLM providers. This integration allows your agents to use any model or provider supported by LiteLLM.

## Key Terminology

**LLM Provider**: The service that runs the model and provides an API endpoint (e.g., Anthropic, Gemini, or local tools like `vLLM` and `llama.cpp`). Each provider requires three settings:
- `name`: The provider name recognized by LiteLLM.
- `base_url`: The API endpoint URL. This can be left blank for major cloud providers like Anthropic or Gemini.
- `api_key`: Your secret access key.

**LLM Model**: In this system, a "Model" is a specific combination of a provider, a model name, and specific settings (like temperature). 
- *Example:* You could create two different model configurations for `Qwen 3.5 27B` running on `llama.cpp`—one with a low temperature for coding and another with a higher temperature for chatting. You can then assign these to agents by their nicknames.

## Setup Guide

1. Click your **username/gear icon** at the bottom of the sidebar to open Settings.
2. Select the **LLM Configuration** tab.
3. **Add a Provider**: Click `+ Add Provider` and enter your API details.
4. **Add a Model**: Click `+ Add New Model Configuration`. Choose a provider from your list, enter the model name, and adjust the settings.

## Provider-Specific Instructions

Before starting, ensure you have an API key from your chosen provider.

### OpenRouter
OpenRouter provides access to many models through a single API. It is convenient for testing, though costs may differ from direct provider pricing.

**Provider Settings:**
- `name`: `openrouter`
- `base_url`: `https://openrouter.ai/api/v1`
- `api_key`: Your OpenRouter API key.

**Model Name Example:**
- `qwen/qwen3.5-27b` (Copy the model string from the OpenRouter catalog).

### Google AI Studio
Use this for Gemini models.

**Provider Settings:**
- `name`: `gemini`
- `base_url`: (Leave empty)
- `api_key`: Your API key from Google AI Studio.

**Common Model Names:**
- `gemini-flash-latest`
- `gemini-pro`
