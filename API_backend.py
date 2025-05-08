from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import json
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from wetterdaten import main, auto_update_wetterdaten

load_dotenv(dotenv_path=".env")  # Umgebungsvariablen laden, falls benötigt

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Geheimschlüssel für Sitzungen

# Zielverzeichnisse basierend auf der Nummer
TARGET_DIRS = {
    1: 'pdfs',
    2: 'pdfs',
    3: 'pdfs',
    4: 'pdfs',
    5: 'pdfs',
    6: 'pdfs'
}

# Sicherstellen, dass das Zielverzeichnis existiert
os.makedirs('pdfs', exist_ok=True)

# Passwort für den Zugriff
PASSWORD = os.getenv('PASSWORD', 'default_password')  # Passwort aus Umgebungsvariablen oder Standardwert
# Auto-Update-Status aus Umgebungsvariablen laden

@app.route("/", methods=['GET', 'POST'])
def login():
    user_ip = request.remote_addr
    app.logger.info(f"Login von IP-Adresse: {user_ip}")
    print(f"Login von IP-Adresse: {user_ip}")
    if request.method == 'POST':
        entered_password = request.form.get('password')
        if entered_password == PASSWORD:
            session['authenticated'] = True
            app.logger.info("Erfolgreicher Login.")
            return redirect(url_for('dashboard'))
        else:
            app.logger.warning("Fehlgeschlagener Login-Versuch.")
            return render_template("login.html", error="Falsches Passwort!")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'number' not in request.form:
        app.logger.error("Fehler: Keine Datei oder Nummer angegeben.")
        return jsonify({'error': 'No file or number provided'}), 400

    file = request.files['file']
    number = int(request.form['number'])

    if number not in TARGET_DIRS:
        app.logger.error(f"Ungültige Nummer angegeben: {number}")
        return jsonify({'error': 'Invalid number provided'}), 400

    if file.filename == '' or not file.filename.endswith('.pdf'):
        app.logger.error("Ungültiger Dateityp. Nur PDFs sind erlaubt.")
        return jsonify({'error': 'Invalid file type, only PDFs are allowed'}), 400

    target_dir = TARGET_DIRS[number]
    file_path = os.path.join(target_dir, f'{number}.pdf')

    try:
        file.save(file_path)
        app.logger.info(f"Datei erfolgreich hochgeladen: {file.filename} in Slot {number}.")
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
        with open('output/infos.json', 'w', encoding='utf-8') as f:
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
        with open('output/auto_update_status.json', 'w', encoding='utf-8') as f:
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


if __name__ == '__main__':
    # Logging konfigurieren
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)  # INFO und höher loggen
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)  # RotatingFileHandler

    # Logs auch in der Konsole ausgeben
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)  # StreamHandler

    # werkzeug-Logger konfigurieren
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(handler)

    # Test-Log
    app.logger.info("Test-Log: Die Anwendung wurde gestartet.")
    print("Logging wurde konfiguriert.")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)