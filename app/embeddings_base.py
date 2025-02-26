class Embeddings:
    def fit(self, texts):
        raise NotImplementedError("The method not implemented")

    def transform(self, text):
        raise NotImplementedError("The method not implemented")

    def embed_documents(self, texts):
        raise NotImplementedError("The method not implemented")

    def embed_query(self, text):
        raise NotImplementedError("The method not implemented")

    def __call__(self, text):
        raise NotImplementedError("The method not implemented")