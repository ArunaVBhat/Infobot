# embeddings.py
from sentence_transformers import SentenceTransformer

class TransformerEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts, convert_to_tensor=True)

    def embed_query(self, query):
        """Generate embedding for a single query."""
        return self.model.encode(query, convert_to_tensor=True)
