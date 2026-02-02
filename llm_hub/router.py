from llm_hub.local_gemma_client import ollama_call

LLM_PROVIDER = "ollama"   


def llm_ask(prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return ollama_call(
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2}
        )
    
    # elif LLM_PROVIDER == "openai":
    #     return openai_call(prompt)
