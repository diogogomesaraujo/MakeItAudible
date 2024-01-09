from flask import Flask, request, send_file, render_template, url_for
import os
from gtts import gTTS
import pdfplumber
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
    if uploaded_file and uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(pdf_path)
        
        # Process the PDF and convert to audio
        texto_total = ""
        with pdfplumber.open(pdf_path) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_total += texto + "\n"

        # Create an instance of the gTTS class and save the audio file
        tts = gTTS(texto_total, lang='pt')
        audio_filename = 'output.mp3'
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        tts.save(audio_path)

        # Generate a URL for the audio file
        audio_url = url_for('get_audio', filename=audio_filename)

        # Return HTML with the audio controls and a download link
        return render_template('audio_player.html', audio_url=audio_url)
    
    # If no file is uploaded, render the 'no_file.html' template instead of just returning a string
    return render_template('no_file.html')

@app.route('/audio/<filename>')
def get_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename), as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True)
