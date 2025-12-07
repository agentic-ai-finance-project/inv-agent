import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature=0):
    """
    Returns the configured LLM based on environment variables.
    Defaults to OpenAI if not specified.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL")

    if provider == "google":
        if not model_name:
            model_name = "gemini-2.5-flash"
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    
    elif provider == "openai":
        if not model_name:
            model_name = "gpt-5-mini"
        return ChatOpenAI(model=model_name, temperature=temperature)
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
