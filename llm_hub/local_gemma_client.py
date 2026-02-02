import ollama


def ollama_call(
    messages,
    model="gemma2:2b",
    temperature=0,
    
):
    
    response = ollama.chat(
        model=model,
        messages=messages,
        
    )

    return response["message"]["content"].strip()
