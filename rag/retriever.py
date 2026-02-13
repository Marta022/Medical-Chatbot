# TODO(remove-shim): remove after P2 stabilization.
from rag.retrieval.retriever import retrieve_top_similar


def retrieve_top_similar_descriptions(input_message: str, top_k: int = 5):
    result = retrieve_top_similar(input_message=input_message, top_k=top_k)
    return result.context_lines(with_score=True), result.titles()

