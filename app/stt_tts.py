import speech_recognition as sr
from gtts import gTTS
import os

def speech_to_text(audio_file, lang="en"):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language=lang)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError:
            return "Speech recognition service unavailable."

def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    audio_path = f"static/audio/output.mp3"
    tts.save(audio_path)
    return audio_path
