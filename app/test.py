from sentence_transformers import SentenceTransformer

# Try loading the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Test embedding generation
query_embedding = model.encode("What are the admission criteria?")
print(query_embedding)
import logging

logging.basicConfig(level=logging.DEBUG)
logging.debug("Script is running")

# Rest of your script
