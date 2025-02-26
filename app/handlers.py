import json
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_faqs(user_type):
    if user_type == "staff":
        file_path = "data/staff_faqs.json"
    else:
        file_path = "data/visitor_faqs.json"

    with open(file_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)
    return faqs

def process_query(user_input, user_type="visitor"):
    faqs = load_faqs(user_type)
    faq_questions = list(faqs.keys())
    faq_answers = list(faqs.values())
    faq_embeddings = model.encode(faq_questions, convert_to_tensor=True)

    # Generate embedding for the user query
    query_embedding = model.encode(user_input, convert_to_tensor=True)

    # Compute similarity with FAQ questions
    similarities = util.pytorch_cos_sim(query_embedding, faq_embeddings)[0]
    best_match_idx = similarities.argmax().item()
    best_score = similarities[best_match_idx].item()

    # Threshold for matching
    similarity_threshold = 0.7
    if best_score >= similarity_threshold:
        response = faq_answers[best_match_idx]
    else:
        response = "I'm sorry, I couldn't understand your question. Can you please rephrase it?"

    return response
