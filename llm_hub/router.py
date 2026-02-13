from llm_hub.local_gemma_client import ollama_call
from llm_hub.openai_client import openai_call

LLM_PROVIDER = "openai"   


def llm_ask(prompt, input_message, context_block):
    if LLM_PROVIDER == "ollama":
        return ollama_call(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{input_message}\n\n{context_block}"}
            ],
            temperature=0
        )
    
    elif LLM_PROVIDER == "openai":
        return openai_call(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{input_message}\n\n{context_block}"}
            ],
            temperature=0
        )


def llm_classify(messages, temperature=0):
    if LLM_PROVIDER == "ollama":
        return ollama_call(
            messages=messages,
            temperature=temperature,
        )

    elif LLM_PROVIDER == "openai":
        return openai_call(
            messages=messages,
            temperature=temperature,
        )
