from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import json
import logging
import datetime
import requests
import subprocess
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from wetterdaten import main, auto_update_wetterdaten
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

load_dotenv(dotenv_path=".env")  # Umgebungsvariablen laden, falls benötigt

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key')
TARGET_DIR = os.getenv('zielverzeichnis')
  # Geheimschlüssel für Sitzungen

csrf = CSRFProtect(app)
send = requests
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# Zielverzeichnisse basierend auf der Nummer
TARGET_DIRS = {
    1: f'{TARGET_DIR}/pdfs',
    2: f'{TARGET_DIR}/pdfs',
    3: f'{TARGET_DIR}/pdfs',
    4: f'{TARGET_DIR}/pdfs',
    5: f'{TARGET_DIR}/pdfs',
    6: f'{TARGET_DIR}/pdfs'
}

# Sicherstellen, dass das Zielverzeichnis existiert
os.makedirs(f'{TARGET_DIR}/pdfs', exist_ok=True)

# Passwort für den Zugriff
PASSWORD = os.getenv('PASSWORD', 'default_password')  # Passwort aus Umgebungsvariablen oder Standardwert
# Auto-Update-Status aus Umgebungsvariablen laden

class LoginForm(FlaskForm):
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    file = FileField('PDF auswählen', validators=[FileAllowed(['pdf'], 'Nur PDF erlaubt!')])
    submit = SubmitField('Hochladen')

@app.route("/", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    user_ip = request.remote_addr
    app.logger.info(f"Login von IP-Adresse: {user_ip}")
    print(f"Login von IP-Adresse: {user_ip}")
    if form.validate_on_submit():
        entered_password = form.password.data
        if entered_password == PASSWORD:
            session['authenticated'] = True
            app.logger.info("Erfolgreicher Login.")
            return redirect(url_for('dashboard'))
        else:
            app.logger.warning("Fehlgeschlagener Login-Versuch.")
            return render_template("login.html", form=form, error="Falsches Passwort!")
    return render_template("login.html", form=form)

@app.route("/dashboard")
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    form = UploadForm()
    return render_template("index.html", form=form)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if 'file' not in request.files or 'number' not in request.form:
        app.logger.error("Fehler: Keine Datei oder Nummer angegeben.")
        return jsonify({'error': 'No file or number provided'}), 400

    file = request.files['file']
    number = int(request.form['number'])

    if number not in TARGET_DIRS:
        app.logger.error(f"Ungültige Nummer angegeben: {number}")
        return jsonify({'error': 'Invalid number provided'}), 400

    if file.filename == '':
        app.logger.error("Kein Dateiname angegeben.")
        return jsonify({'error': 'No filename provided'}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.pdf'):
        app.logger.error("Ungültiger Dateityp. Nur PDFs sind erlaubt.")
        return jsonify({'error': 'Invalid file type, only PDFs are allowed'}), 400

    target_dir = TARGET_DIRS[number]
    file_path = os.path.join(target_dir, f'{number}.pdf')

    try:
        file.save(file_path)
        app.logger.info(f"Datei erfolgreich hochgeladen: {filename} in Slot {number}.")
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        app.logger.error(f"Fehler beim Hochladen der Datei: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    if 'number' not in request.form:
        app.logger.error("Fehler: Keine Nummer angegeben.")
        return jsonify({'error': 'No number provided'}), 400

    number = int(request.form['number'])

    if number not in TARGET_DIRS:
        app.logger.error(f"Ungültige Nummer angegeben: {number}")
        return jsonify({'error': 'Invalid number provided'}), 400

    target_dir = TARGET_DIRS[number]
    file_path = os.path.join(target_dir, f'{number}.pdf')

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info(f"Datei erfolgreich gelöscht: Slot {number}.")
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            app.logger.warning(f"Datei nicht gefunden: Slot {number}.")
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        app.logger.error(f"Fehler beim Löschen der Datei: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/update_infos', methods=['POST'])
def update_infos():
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    infos = request.json['info']
    print(infos)
    
    try:
        with open(f'{TARGET_DIR}/output/infos.json', 'w', encoding='utf-8') as f:
            json.dump({'infos': infos}, f, ensure_ascii=False, indent=4)
        return jsonify({'message': 'Infos updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/wetter_update', methods=['GET'])
def wetter_update():
    main()
    return jsonify({'message': 'Wetterdaten wurden aktualisiert'}), 200

@app.route('/toggle_auto_update', methods=['POST'])
def toggle_auto_update():
    if 'auto_update' not in request.json:
        return jsonify({'error': 'No auto_update status provided'}), 400
    auto_update = request.json['auto_update']

    if not isinstance(auto_update, bool):
        return jsonify({'error': 'auto_update should be a boolean'}), 400

    try:
        with open(f'{TARGET_DIR}/output/auto_update_status.json', 'w', encoding='utf-8') as f:
            json.dump({'auto_update': auto_update}, f, ensure_ascii=False, indent=4)
        return jsonify({'message': 'Auto-update status toggled successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/pdf_belegt", methods=['GET'])
def pdf_belegt():
    pdf_files = []
    target_dir = 'pdfs'
    for file in os.listdir(target_dir):
        if file.endswith('.pdf'):
            pdf_files.append(file)
    print(pdf_files)

    return jsonify({'pdf_files': pdf_files}), 200
@app.route('/error', methods=['GET'])
def log_error():
    url = "http://100.104.101.101:5000/error"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "isudhfasbdfjbflk_sdfhcuadgasfi_hisfduihiasd_nhiasdisad_icfd"
    }
    data = {"error": "Das ist ein Testfehler"}

    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    return jsonify({'message': 'Error logged successfully'}), 200

if __name__ == '__main__':
    # Logging-Konfiguration (wird immer ausgeführt, egal ob direkt oder via Gunicorn)
    if os.path.exists('app.log'):
        os.remove('app.log')
    try:
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)

        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.INFO)
        werkzeug_logger.addHandler(handler)

        app.logger.info("Test-Log: Die Anwendung wurde (Gunicorn-kompatibel) geladen.")
    except Exception as e:
        print(f"Fehler beim Logging-Setup: {str(e)}")
        app.logger.error(f"Fehler beim Logging-Setup: {str(e)}")

    # Anwendung starten
    try:
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Fehler beim Starten der Anwendung: {str(e)}")
        app.logger.error(f"Fehler beim Starten der Anwendung: {str(e)}")
        error = f"Fehler {str(e)} um {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        requests.post("http://100.104.101.101:6000/error", json={"error": str(e)})  # Beispiel-URL, an die der Fehler gesendet werden soll
        print(f"Fehler wurde an die URL gesendet: {error}")
        app.logger.error(f"Fehler wurde an die URL gesendet: {error}")
        print("Server wird neu gestartet...")
        app.logger.info(f"Server wird neu gestartet{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        exit(1)
        subprocess.run(["sudo reboot"], shell=True)