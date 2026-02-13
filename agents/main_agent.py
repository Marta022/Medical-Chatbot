from rag.retriever import retrieve_top_similar_descriptions
from llm_hub.router import llm_ask
from config.settings import BASE_SYSTEM_PROMPT
from translation.translator import translate_to_romanian, translate_to_english
from guardrails.rules import apply_guardrails

while True:
    q = input("You: ").strip()
    if not q:
        continue

    # Apply guardrails to check for emergencies
    guardrail_result = apply_guardrails(q)
    
    if not guardrail_result["is_valid"]:
        print(guardrail_result["message"])
        if guardrail_result["is_emergency"]:
            print("\n" + "="*80 + "\n")
        continue
    q_en = translate_to_english(q)
    top, titles = retrieve_top_similar_descriptions(q_en, top_k=3)
    
    # Translate chunks to Romanian
    top_romanian = translate_to_romanian(top)
    
    print("\n Context folosit (în română):")
    for i, item in enumerate(top_romanian, 1):
        print(f"\n{i}. {item}")
    print("\n" + "="*80 + "\n")
    
    context_block = "Top similar diseases and additional information:\n" + "\n".join(f"- {item}" for item in top_romanian)
    response = llm_ask(BASE_SYSTEM_PROMPT, q, context_block)
    print(f"Assistant: {response}\n")
