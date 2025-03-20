import os
import logging
import uuid
from flask import request, jsonify
from dotenv import load_dotenv  # Import dotenv for loading .env variables
from .demo_page import handle_userinput, get_documents_text, get_text_chunks, get_vectorstore, get_conversation_chain
from . import docbot_bp
from flask import render_template

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Fetch Groq API key from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set in the .env file")

# Store conversation sessions
conversation_store = {}

@docbot_bp.route('/upload', methods=['POST'])
def upload_documents():
    """Handle document uploads and create a conversation chain."""
    try:
        files = request.files.getlist("files")  # Ensure key matches frontend
        if not files:
            logger.error("No files uploaded")
            return jsonify({"error": "No files uploaded"}), 400

        text_data = get_documents_text(files)
        if not text_data:
            logger.error("No valid text extracted")
            return jsonify({"error": "No valid text extracted"}), 400

        text_chunks = get_text_chunks(text_data)
        vectorstore = get_vectorstore(text_chunks)
        if not vectorstore:
            logger.error("Failed to create vectorstore")
            return jsonify({"error": "Failed to create vectorstore"}), 500

        conversation_chain = get_conversation_chain(vectorstore)
        if not conversation_chain:
            logger.error("Failed to initialize conversation chain")
            return jsonify({"error": "Failed to initialize conversation chain"}), 500

        session_id = str(uuid.uuid4())  # Unique session ID
        conversation_store[session_id] = conversation_chain

        logger.info(f"New session created: {session_id}")
        return jsonify({"session_id": session_id}), 200
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        return jsonify({"error": str(e)}), 500

@docbot_bp.route('/query', methods=['POST'])
def query_handler():
    """Handle user queries and fetch relevant answers."""
    try:
        data = request.get_json()

        logger.debug(f"Received data: {data}")

        query = data.get("query", "").strip()
        session_id = data.get("session_id")

        if not query:
            logger.error("Query parameter is missing.")
            return jsonify({"error": "Query parameter is missing"}), 400

        if not session_id:
            logger.error("Session ID is missing.")
            return jsonify({"error": "Session ID is missing"}), 400

        if session_id not in conversation_store:
            logger.error(f"Invalid session_id '{session_id}'")
            return jsonify({"error": f"Invalid session_id '{session_id}'. Please upload documents again."}), 400

        conversation_chain = conversation_store[session_id]

        # Correct function call
        return handle_userinput(query, session_id, conversation_chain)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@docbot_bp.route('/')
def docbot_home():
    return render_template('docbot.html')