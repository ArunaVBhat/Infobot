import os
import json
import logging
import requests
from flask import request, jsonify
from fuzzywuzzy import process, fuzz
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from app.infobot import infobot_bp

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logging.warning("⚠️ GROQ_API_KEY environment variable not set. Some features may not work.")

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

# Load FAQs from a JSON file
def load_faqs():
    faq_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "staff_faqs.json")
    try:
        with open(faq_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"⚠️ FAQs file not found: {faq_file_path}")
        return {}
    except json.JSONDecodeError:
        logging.error("❌ Error parsing staff_faqs.json - check its format.")
        return {}

# Preload FAQs
FAQs = load_faqs()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Normalize function to standardize input
def normalize_text(text):
    return text.strip().lower()

# Function to match a query to the FAQ with fuzzy matching
def match_faq(query):
    max_ratio = 0
    best_match_answer = None
    for faq_question, faq_answer in FAQs.items():
        ratio = process.extractOne(query, [faq_question], scorer=fuzz.partial_ratio)
        if ratio and ratio[1] > max_ratio:
            max_ratio = ratio[1]
            best_match_answer = faq_answer

    if max_ratio >= 65:
        return best_match_answer
    return None

# Function to clean extracted text
def clean_text(text):
    return ' '.join(text.split())

# Function to match extracted information to the query using fuzzy matching
def match_extracted_info(query, extracted_info):
    max_ratio = 0
    best_match_info = None
    for info in extracted_info:
        cleaned_info = clean_text(info)
        ratio = fuzz.partial_ratio(query.lower(), cleaned_info.lower())
        if ratio > max_ratio:
            max_ratio = ratio
            best_match_info = cleaned_info

    return best_match_info

# Function to perform semantic search using Hugging Face Transformers
def semantic_search(query):
    try:
        if not FAQs:
            return None

        # Encode the query and FAQs
        query_embedding = model.encode(query, convert_to_tensor=True)
        faq_questions = list(FAQs.keys())
        faq_embeddings = model.encode(faq_questions, convert_to_tensor=True)

        # Compute cosine similarities
        similarities = util.pytorch_cos_sim(query_embedding, faq_embeddings)
        best_match_idx = similarities.argmax().item()

        if similarities[0][best_match_idx] > 0.75:  # Adjust threshold if necessary
            best_match_question = faq_questions[best_match_idx]
            return FAQs[best_match_question]

        return None
    except Exception as e:
        logging.error(f"❌ Error during semantic search: {str(e)}")
        return None

# Function to scrape a list of URLs for relevant information
def scrape_urls(query, urls, timeout=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    relevant_sections = []

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            logging.debug(f"🔍 Request sent to {url}, status code: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p']):
                    text = tag.get_text(separator="\n").strip()
                    if any(keyword in text.lower() for keyword in query.split()):
                        relevant_sections.append(text)
            else:
                logging.warning(f"⚠️ Failed to retrieve {url} (Status Code: {response.status_code})")

        except requests.exceptions.Timeout:
            logging.error(f"⏳ Request to {url} timed out")
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error fetching {url}: {str(e)}")

    return relevant_sections

# Function to handle user queries
@infobot_bp.route("/query", methods=["POST"])
def query_handler():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "⚠️ Query parameter is missing"}), 400

        logging.info(f"🔎 User Query: {query}")

        # First, try to find the answer from the FAQs
        faq_answer = match_faq(query)
        if faq_answer:
            return jsonify({"response": faq_answer}), 200

        # If not found in FAQs, perform semantic search
        semantic_answer = semantic_search(query)
        if semantic_answer:
            return jsonify({"response": semantic_answer}), 200

        # If still not found, scrape relevant URLs
        urls = ["https://example.com/faq1", "https://example.com/faq2"]  # Add actual URLs
        scraped_info = scrape_urls(query, urls)
        if scraped_info:
            matched_info = match_extracted_info(query, scraped_info)
            if matched_info:
                return jsonify({"response": matched_info}), 200

        return jsonify({"response": "🤔 Sorry, I couldn't find the information you requested."}), 200

    except Exception as e:
        logging.error(f"❌ Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
