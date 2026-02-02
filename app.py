from rag.retriever import retrieve_top_similar_descriptions

while True:
    q = input("You: ").strip()
    if not q:
        continue

    top, titles = retrieve_top_similar_descriptions(q, top_k=5)

    print("\nTop matches:")
    for t in top:
        print(" -", t)
    print()
