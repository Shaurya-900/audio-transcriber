from flask import Flask, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from groq import Groq
from dotenv import load_dotenv 
import os
import uuid
load_dotenv()
app= Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS= {'wav', 'mp3', 'm4a','ogg'}
# Groq's Whisper endpoint rejects files larger than 25 MB
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Created lazily so a missing GROQ_API_KEY doesn't crash the app at import time
groq_client = None
def get_groq_client():
    global groq_client
    if groq_client is None:
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return groq_client
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
def transcribe_audio(filepath):
    try:
        with open(filepath,'rb') as audio_file:
            transcription=get_groq_client().audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format='text'
            )
        return transcription
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
@app.route('/')
def index():
    return redirect(url_for('transcribe'))
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File is too large (max 25 MB)'}), 413
@app.route('/transcribe', methods=['GET','POST'])
def transcribe():
    if request.method=='GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student Lecture Transcription</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1{
                    color: #333;
                    margin-bottom: 20px;}
                input[type="file"]{
                    margin: 20px 0;
                    padding: 10px;
                }
                button{
                background-color: #4CAF50;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                }
                button:hover{
                    background-color: #45a049;
                }
                #result{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 4px;
                    display:none;
                }
                #loading{
                    display:none;
                    color: #666;
                }
                .error{
                    color: #d32f2f;
                    background-color: #ffebee;}
                .success{
                    color: #2e7d32;
                    background-color: #e8f5e9;
                }
            </style>
        </head>
        <body>
            <div class='container'>
                <h1>Audio Transcriber</h1>
                <p>Upload an audio file (MP3, WAV, M4A, OGG) to get the transcription.</p>
                <form id="uploadForm">
                    <input type="file" name="audio" id="audioFile" accept="audio/*" required>
                    <br>
                    <button type="submit">Transcribe</button>
                </form>
                <div id="loading">Transcribing...Please wait for a moment.</div>
                <div id="result"></div>
            </div>
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('audioFile');
                const loading = document.getElementById('loading');
                const result = document.getElementById('result'); 
            if (!fileInput.files[0]) {
                alert('Please select a file');
                return;
            }
        
            loading.style.display = 'block';
            result.style.display = 'none';
        
            const formData = new FormData();
            formData.append('audio', fileInput.files[0]);
        
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
            });
            
            let data;
            try {
                data = await response.json();
            } catch {
                data = { success: false, error: `Server error (${response.status})` };
            }
            
            loading.style.display = 'none';
            result.style.display = 'block';
            
            if (data.success) {
                result.className = 'success';
                result.innerHTML = `
                    <h3>✅ Transcription Complete</h3>
                    <p><strong>Filename:</strong> <span id="resFilename"></span></p>
                    <p><strong>Transcription:</strong></p>
                    <p id="resText" style="white-space: pre-wrap"></p>
                `;
                // textContent, not innerHTML: transcripts are untrusted text
                document.getElementById('resFilename').textContent = data.filename;
                document.getElementById('resText').textContent = data.transcription;
            } else {
                result.className = 'error';
                result.innerHTML = `<h3>❌ Error</h3><p id="resError"></p>`;
                document.getElementById('resError').textContent = data.error || 'Unknown error';
            }
            } catch (error) {
                loading.style.display = 'none';
                result.style.display = 'block';
                result.className = 'error';
                result.innerHTML = `<h3>❌ Error</h3><p id="resError"></p>`;
                document.getElementById('resError').textContent = `Failed to transcribe: ${error.message}`;
            }
        });
        </script>
        </body>
        </html>
        '''
    if 'audio' not in request.files:
        return jsonify({'error': 'No file found'}), 400
    file= request.files['audio']
    if file.filename =='':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp3, wav, m4a, ogg'}), 400
    filename= secure_filename(file.filename)
    # Unique name on disk so concurrent uploads with the same filename don't clobber each other
    ext = file.filename.rsplit('.', 1)[1].lower()
    filepath=os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.{ext}")
    file.save(filepath)
    try:
        transcription = transcribe_audio(filepath)
        if transcription is None:
            return jsonify({'error': 'Transcription failed. Please try again.'}), 502
        return jsonify({
            'success': True,
            'filename': filename,
            'transcription': transcription
        }),200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Transcription failed'}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
@app.route('/test')
def test():
    #1. Get uploaded audio file
    #2. Save it temporarily
    #3. send to groq API
    #4. Return transcription as JSON
    return "<h1>Hello World</h1>"
if __name__ == '__main__':
    app.run(debug=True)