import os
import json
import logging
import requests
from flask import request, jsonify
from fuzzywuzzy import process, fuzz
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from app.infobot import infobot_bp
from deep_translator import GoogleTranslator

# Ensure consistent language detection
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logging.warning("⚠️ GROQ_API_KEY environment variable not set. Some features may not work.")

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

# Load FAQs
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

FAQs = load_faqs()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Detects the language of the query
def detect_language(text):
    try:
        return detect(text)  # Returns language code (e.g., "fr", "es", "hi")
    except Exception as e:
        logging.warning(f"⚠️ Language detection failed: {str(e)}")
        return "en"  # Default to English if detection fails

# Translates text to a target language
def translate_text(text, source_lang, target_lang):
    try:
        if source_lang == target_lang:
            return text  # No translation needed
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception as e:
        logging.warning(f"⚠️ Translation failed ({source_lang} ➝ {target_lang}): {str(e)}")
        return text  # Return original text if translation fails

# Function to match a query to the FAQ with fuzzy matching
def match_faq(query):
    logging.debug(f"Matching query: {query}")
    max_ratio = 0
    best_match_answer = None
    for faq_question, faq_answer in FAQs.items():
        ratio = process.extractOne(query, [faq_question], scorer=fuzz.partial_ratio)
        if ratio and ratio[1] > max_ratio:
            max_ratio = ratio[1]
            best_match_answer = faq_answer

    if max_ratio >= 65:
        logging.info(f"Best match found with ratio {max_ratio}: {best_match_answer}")
        return best_match_answer
    return None

# Function to perform semantic search using Hugging Face Transformers
def semantic_search(query):
    try:
        if not FAQs:
            return None

        query_embedding = model.encode(query, convert_to_tensor=True)
        faq_questions = list(FAQs.keys())
        faq_embeddings = model.encode(faq_questions, convert_to_tensor=True)

        similarities = util.pytorch_cos_sim(query_embedding, faq_embeddings)
        best_match_idx = similarities.argmax().item()

        if similarities[0][best_match_idx] > 0.75:
            return FAQs[faq_questions[best_match_idx]]

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

        # 🔍 Detect query language
        detected_language = detect_language(query)
        logging.info(f"🔎 Detected Language: {detected_language}")

        # 🌍 Translate query to English for processing
        translated_query = translate_text(query, detected_language, "en")
        logging.info(f"🔎 Translated Query: {translated_query}")

        # 1️⃣ Check FAQs for an answer
        faq_answer = match_faq(translated_query)
        if faq_answer:
            translated_answer = translate_text(faq_answer, "en", detected_language)
            return jsonify({"response": translated_answer}), 200

        # 2️⃣ If not found, perform semantic search
        semantic_answer = semantic_search(translated_query)
        if semantic_answer:
            translated_answer = translate_text(semantic_answer, "en", detected_language)
            return jsonify({"response": translated_answer}), 200

        # 3️⃣ If still not found, scrape relevant URLs
        urls = ["https://klsvdit.edu.in/"]
        scraped_info = scrape_urls(translated_query, urls)
        if scraped_info:
            matched_info = max(scraped_info, key=lambda x: fuzz.partial_ratio(translated_query.lower(), x.lower()), default=None)
            if matched_info:
                translated_answer = translate_text(matched_info, "en", detected_language)
                return jsonify({"response": translated_answer}), 200

        # 4️⃣ If no answer is found, return a fallback response
        fallback_response = "🤔 Sorry, I couldn't find the information you requested."
        translated_fallback = translate_text(fallback_response, "en", detected_language)
        return jsonify({"response": translated_fallback}), 200

    except Exception as e:
        logging.error(f"❌ Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
