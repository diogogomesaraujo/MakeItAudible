from flask import Flask, request, send_file, render_template, url_for, send_from_directory
import os
from gtts import gTTS
import pdfplumber
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Set the environment variable for Tesseract OCR data path
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

app = Flask(__name__)

# Define function to check if the PDF contains text or is scanned
def is_scanned_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        return not bool(text)
    
# Define language codes for Tesseract and gTTS
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

# Configure Flask app to use the upload and audio folders
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# Define a function to check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

# Define a route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Define the index route
@app.route('/')
def index():
    return render_template('index.html')

# Define the file upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    selected_language_name = request.form['language']  # This will be the full language name from the dropdown

    # Check if there is a file and if it's a PDF
    if uploaded_file and uploaded_file.filename != '':
        if not allowed_file(uploaded_file.filename):
            return render_template('invalid_file_type.html')
        
        # Get the language codes for pytesseract and gTTS
        language_codes = LANGUAGE_CODES.get(selected_language_name, {})
        pytesseract_lang_code = language_codes.get("tesseract")
        gtts_lang_code = language_codes.get("gtts")

        # Save the uploaded file
        filename = secure_filename(uploaded_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(pdf_path)

        texto_total = ""

        # Check if the PDF is scanned and process accordingly
        if is_scanned_pdf(pdf_path):
            images = convert_from_path(pdf_path)
            for image in images:
                texto_total += pytesseract.image_to_string(image, lang=pytesseract_lang_code)
        else:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texto_total += text + "\n"

        # Convert the text to speech
        tts = gTTS(texto_total, lang=gtts_lang_code)
        audio_filename = 'output.mp3'
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        tts.save(audio_path)

        # Generate URLs for the audio and PDF
        audio_url = url_for('get_audio', filename=audio_filename)
        pdf_url = url_for('uploaded_file', filename=filename)
        return render_template('audio_player.html', audio_url=audio_url, pdf_url=pdf_url, filename=filename)

    return render_template('no_file.html')

# Define a route to serve audio files
@app.route('/audio/<filename>')
def get_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename), as_attachment=False)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
