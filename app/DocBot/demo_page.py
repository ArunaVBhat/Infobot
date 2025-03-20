import os
import logging
from dotenv import load_dotenv
from flask import Flask
from PyPDF2 import PdfReader
from docx import Document
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
logging.getLogger("urllib3").setLevel(logging.WARNING)
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins


from langchain_huggingface import HuggingFaceEmbeddings  # ✅ Correct module
  # ✅ Use correct module

# ✅ Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_documents_text(files):
    """Extract text from uploaded documents."""
    text_data = []
    for file in files:
        try:
            if file.filename.endswith('.pdf'):
                pdf_reader = PdfReader(file)
                text = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
            elif file.filename.endswith('.docx'):
                docx_reader = Document(file)
                text = "\n".join(paragraph.text for paragraph in docx_reader.paragraphs)
            else:
                logger.warning(f"⚠ Unsupported file type: {file.filename}")
                continue
            text_data.append({"text": text, "source": file.filename})
        except Exception as e:
            logger.error(f"❌ Error processing file {file.filename}: {e}")
    return text_data


def get_text_chunks(text_data):
    """Split extracted text into smaller chunks for processing."""
    chunks = []
    for item in text_data:
        chunks.append({"chunk": item["text"], "source": item["source"]})
    return chunks


def get_vectorstore(text_chunks):
    """Create FAISS vectorstore with embeddings."""
    try:
        texts = [item["chunk"] for item in text_chunks]

        if not texts:
            logger.error("❌ No text chunks available for vectorstore creation!")
            return None

        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embeddings = embedding_model.embed_documents(texts)  # ✅ Use correct method

        vectorstore = FAISS.from_embeddings(list(zip(texts, embeddings)), embedding_model.embed_query)

        logger.info(f"✅ Successfully created FAISS vectorstore with {len(texts)} documents")
        return vectorstore
    except Exception as e:
        logger.error(f"❌ Error creating vectorstore: {e}", exc_info=True)
        return None



def get_conversation_chain(vectorstore):
    """Initialize the conversation chain."""
    try:
        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            You are a helpful assistant. Answer the question using the provided context.
            If you don't know, say so.

            Context: {context}
            Question: {question}

            Answer:
            """
        )

        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        llm = ChatGroq(api_key=groq_api_key, temperature=0.5, max_tokens=500)

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, output_key="answer"
        )

        retriever = vectorstore.as_retriever()

        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt_template},
            return_source_documents=True,
            output_key="answer",  # ✅ Explicitly define output_key
            verbose=True
        )

        logger.info("✅ Successfully created conversation chain")
        return conversation_chain
    except Exception as e:
        logger.error(f"❌ Error creating conversation chain: {e}")
        return None

def handle_userinput(user_question, session_id, conversation_chain):
    """Process user input and return a response."""
    try:
        if not user_question or not session_id:
            return jsonify({"error": "Missing question or session_id"}), 400

        response = conversation_chain.invoke({'question': user_question})

        answer = response.get("answer", "No response generated.")
        return jsonify({"answer": answer})

    except Exception as e:
        logger.error(f"❌ Error processing user question: {e}")
        return jsonify({"error": str(e)}), 500
