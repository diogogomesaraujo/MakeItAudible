from flask import Flask, request, send_file, render_template, url_for
import os
from gtts import gTTS
import pdfplumber
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

app = Flask(__name__)

def is_scanned_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        return not bool(text)
    
LANGUAGE_CODES = {
    "English": {"tesseract": "eng", "gtts": "en"},
    "Portuguese": {"tesseract": "por", "gtts": "pt"},
    "Spanish": {"tesseract": "spa", "gtts": "es"},
    "French": {"tesseract": "fra", "gtts": "fr"},
    "German": {"tesseract": "deu", "gtts": "de"},
}

# Ensure the upload and audio directories exist
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    selected_language_name = request.form['language']  # This will be the full language name from the dropdown

    # Get the language codes for pytesseract and gTTS
    language_codes = LANGUAGE_CODES.get(selected_language_name, {})
    pytesseract_lang_code = language_codes.get("tesseract")
    gtts_lang_code = language_codes.get("gtts")

    if uploaded_file and uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(pdf_path)

        texto_total = ""

        if is_scanned_pdf(pdf_path):
            images = convert_from_path(pdf_path)
            for image in images:
                # Use the tesseract language code
                texto_total += pytesseract.image_to_string(image, lang=pytesseract_lang_code)
        else:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texto_total += text + "\n"

        # Use the gTTS language code
        tts = gTTS(texto_total, lang=gtts_lang_code)
        audio_filename = 'output.mp3'
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        tts.save(audio_path)

        audio_url = url_for('get_audio', filename=audio_filename)
        return render_template('audio_player.html', audio_url=audio_url)

    return render_template('no_file.html')


@app.route('/audio/<filename>')
def get_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename), as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True)
