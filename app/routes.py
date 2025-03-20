from flask import render_template, request, jsonify
from handlers import process_query
from stt_tts import text_to_speech, speech_to_text

def setup_routes(app):
    @app.route("/stt", methods=["POST"])
    def stt():
        audio_file = request.files["audio"]
        lang = request.form.get("lang", "en")
        text = speech_to_text(audio_file, lang)
        return jsonify({"text": text})

    @app.route("/tts", methods=["POST"])
    def tts():
        text = request.json.get("text", "")
        lang = request.json.get("lang", "en")
        audio_path = text_to_speech(text, lang)
        return jsonify({"audio_path": audio_path})