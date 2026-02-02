from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

def vector_size():
    return model.get_sentence_embedding_dimension()

def embed_texts(texts):
    vecs = model.encode(texts, convert_to_tensor=False, normalize_embeddings=True)
    return vecs.tolist()

def embed_query(text):
    v = model.encode([text], convert_to_tensor=False, normalize_embeddings=True)[0]
    return v.tolist()
