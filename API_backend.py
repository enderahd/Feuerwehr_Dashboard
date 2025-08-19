from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import os
import json
import logging
import datetime
import requests
import signal
import sys
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from wetterdaten import main
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

# Umgebung laden (Development hat Vorrang für lokales Testen)
flask_env = 'development'
if os.path.exists('.env') and not os.path.exists('.env.production'):
    # Nur .env vorhanden -> Development
    load_dotenv('.env')
    flask_env = os.getenv('FLASK_ENV', 'development')
elif os.path.exists('.env.production') and not os.path.exists('.env'):
    # Nur .env.production vorhanden -> Production  
    load_dotenv('.env.production')
    flask_env = 'production'
elif os.path.exists('.env') and os.path.exists('.env.production'):
    # Beide vorhanden -> Prüfe ENV Variable oder nutze .env für Development
    env_override = os.getenv('FORCE_PRODUCTION', 'false').lower()
    if env_override == 'true':
        load_dotenv('.env.production')
        flask_env = 'production'
    else:
        load_dotenv('.env')  # Development hat Vorrang
        flask_env = os.getenv('FLASK_ENV', 'development')
else:
    # Fallback
    load_dotenv()
    flask_env = os.getenv('FLASK_ENV', 'development')

app = Flask(__name__, template_folder='templates', static_folder='static')

# Konfiguration basierend auf Umgebung
if flask_env == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('SESSION_TIMEOUT', 3600))
else:
    app.config['DEBUG'] = True

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key_for_development_only')
TARGET_DIR = os.getenv('zielverzeichnis', '/opt/feuerwehr_dashboard')

# CSRF Schutz - nur in Produktion aktivieren
csrf_enabled = os.getenv('CSRF_ENABLED', 'False').lower() == 'true' and flask_env == 'production'
csrf = None

# CSRF-Token für Templates verfügbar machen (immer)
@app.context_processor
def inject_csrf_token():
    if csrf_enabled and csrf:
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=lambda: generate_csrf())
    else:
        return dict(csrf_token=lambda: None)

if csrf_enabled:
    try:
        csrf = CSRFProtect(app)
        app.logger.info("CSRF Protection aktiviert")
            
        # CSRF Error Handler
        @app.errorhandler(400)
        def csrf_error(reason):
            app.logger.warning(f"CSRF Fehler: {reason}")
            # Fallback zu einfachem Login
            return redirect(url_for('simple_login'))
            
    except Exception as e:
        app.logger.warning(f"CSRF Setup fehlgeschlagen: {e}")
        csrf = None
        csrf_enabled = False
else:
    csrf = None
    app.logger.info("CSRF Protection deaktiviert (Development-Modus)")

# Rate Limiting
rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
if rate_limit_enabled:
    limiter = Limiter(key_func=get_remote_address)
    limiter.init_app(app)
    default_rate_limit = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
    login_rate_limit = os.getenv('RATE_LIMIT_LOGIN', '5 per minute')
else:
    limiter = None
    default_rate_limit = None
    login_rate_limit = None

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
def login():
    if limiter and login_rate_limit:
        @limiter.limit(login_rate_limit)
        def rate_limited_login():
            return _login()
        return rate_limited_login()
    else:
        return _login()

def _login():
    # Versuche zuerst Flask-WTF Form (nur wenn CSRF aktiviert ist)
    if csrf_enabled:
        try:
            form = LoginForm()
            user_ip = request.remote_addr
            app.logger.info(f"Login-Versuch von IP-Adresse: {user_ip} (mit CSRF)")
            
            if form.validate_on_submit():
                entered_password = form.password.data
                if entered_password == PASSWORD:
                    session['authenticated'] = True
                    app.logger.info("Erfolgreicher Login mit Flask-WTF.")
                    return redirect(url_for('dashboard'))
                else:
                    app.logger.warning("Fehlgeschlagener Login-Versuch.")
                    return render_template("login.html", form=form, error="Falsches Passwort!")
            
            # Wenn Form nicht validiert hat, prüfe ob CSRF das Problem ist
            if request.method == 'POST' and form.errors:
                app.logger.warning(f"Form-Validierung fehlgeschlagen: {form.errors}")
                # Bei CSRF-Fehlern, leite zu einfachem Login weiter
                if any('csrf' in str(error).lower() for error in form.errors.values() if error):
                    app.logger.info("CSRF-Fehler erkannt, weiterleitung zu einfachem Login")
                    return redirect(url_for('simple_login'))
            
            return render_template("login.html", form=form)
        
        except Exception as e:
            app.logger.warning(f"Flask-WTF Fehler: {e}, verwende einfaches Login")
            # Fallback: Einfaches Login ohne WTF
            return redirect(url_for('simple_login'))
    else:
        # Kein CSRF aktiviert, nutze einfaches Login
        return _simple_login()

@app.route("/simple_login", methods=['GET', 'POST'])
def simple_login():
    """Einfaches Login ohne Flask-WTF für CSRF-Probleme"""
    return _simple_login()

def _simple_login():
    """Einfache Login-Logik ohne CSRF"""
    user_ip = request.remote_addr
    app.logger.info(f"Einfacher Login-Versuch von IP-Adresse: {user_ip}")
    
    if request.method == 'POST':
        entered_password = request.form.get('password', '')
        expected_password = PASSWORD
        
        # Debug-Informationen (nur in Development) - ohne Passwort-Details
        if flask_env == 'development':
            app.logger.info(f"Passwort-Vergleich: {entered_password == expected_password}")
        
        if entered_password == expected_password:
            session['authenticated'] = True
            session.permanent = True
            app.logger.info("Erfolgreicher Login (einfach).")
            return redirect(url_for('dashboard'))
        else:
            app.logger.warning(f"Fehlgeschlagener Login-Versuch (einfach). IP: {user_ip}")
            if flask_env == 'development':
                return render_template("login_simple.html", 
                                     error=f"Falsches Passwort! Erwartet: '{expected_password}', Eingegeben: '{entered_password}'")
            else:
                return render_template("login_simple.html", error="Falsches Passwort!")
    
    return render_template("login_simple.html")

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

    if file.filename is None or file.filename == '':
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

# ===== ÖFFENTLICHE API ENDPOINTS FÜR FRONTEND =====

@app.route('/api/public/weather', methods=['GET'])
def public_weather():
    """Öffentlicher Wetter-Endpoint für Frontend"""
    try:
        weather_file = os.path.join(TARGET_DIR, 'output', 'wetterdaten.json')
        if os.path.exists(weather_file):
            with open(weather_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Weather data not available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/forecast', methods=['GET'])
def public_forecast():
    """Öffentlicher Vorhersage-Endpoint für Frontend"""
    try:
        forecast_file = os.path.join(TARGET_DIR, 'output', 'wettervorhersage.json')
        if os.path.exists(forecast_file):
            with open(forecast_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Forecast data not available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/info', methods=['GET'])
def public_info():
    """Öffentlicher Info-Endpoint für Lauftext"""
    try:
        info_file = os.path.join(TARGET_DIR, 'output', 'infos.json')
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data), 200
        else:
            return jsonify({'infos': 'Willkommen beim Feuerwehr Dashboard Glienicke/Nordbahn'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/public/pdfs/<int:number>.pdf', methods=['GET'])
def public_pdf(number):
    """Öffentlicher PDF-Endpoint für Frontend"""
    if number not in TARGET_DIRS:
        return "PDF not found", 404
    
    target_dir = TARGET_DIRS[number]
    file_path = os.path.join(target_dir, f'{number}.pdf')
    
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/pdf')
    else:
        # Leere PDF senden wenn keine vorhanden
        return send_file('static/empty.pdf', mimetype='application/pdf') if os.path.exists('static/empty.pdf') else ("PDF not found", 404)

@app.route('/toggle_auto_update', methods=['POST'])
def toggle_auto_update():
    if not request.json or 'auto_update' not in request.json:
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
    target_dir = f'{TARGET_DIR}/pdfs'
    if os.path.exists(target_dir):
        for file in os.listdir(target_dir):
            if file.endswith('.pdf'):
                pdf_files.append(file)
    print(pdf_files)

    return jsonify({'pdf_files': pdf_files}), 200
@app.route('/debug_info')
def debug_info():
    """Debug-Informationen (nur in Development)"""
    if flask_env != 'development':
        return "Debug-Informationen nur in Development verfügbar", 403
    
    info = {
        'flask_env': flask_env,
        'password_configured': PASSWORD,
        'csrf_enabled': csrf_enabled,
        'target_dir': TARGET_DIR,
        'session_authenticated': session.get('authenticated', False),
        'remote_addr': request.remote_addr
    }
    
    return f"""
    <h2>🔧 Debug-Informationen</h2>
    <pre>{json.dumps(info, indent=2, ensure_ascii=False)}</pre>
    <p><a href="/">Zurück zum Login</a></p>
    <p><a href="/simple_login">Einfaches Login</a></p>
    """

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

def setup_logging():
    """Konfiguriert das Logging für Produktion und Development"""
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
    
    # Log-Verzeichnis erstellen
    if flask_env == 'production':
        log_dir = Path('/var/log/feuerwehr_dashboard')
        log_file = log_dir / 'app.log'
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_file = Path('app.log')
        # Versuche alte Log-Datei zu löschen, ignoriere Fehler
        try:
            if log_file.exists():
                log_file.unlink()
        except (PermissionError, OSError):
            pass  # Ignoriere Fehler beim Löschen
    
    # Rotating File Handler
    max_bytes = int(os.getenv('MAX_LOG_SIZE', 10485760))  # 10MB
    backup_count = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    handler = RotatingFileHandler(
        str(log_file), 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    handler.setLevel(log_level)
    
    # Formatter
    if flask_env == 'production':
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    handler.setFormatter(formatter)
    
    # App Logger
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    # Console Handler nur in Development
    if flask_env != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)
    
    # Werkzeug Logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.addHandler(handler)
    
    app.logger.info(f"Logging konfiguriert - Umgebung: {flask_env}")

def create_directories():
    """Erstellt erforderliche Verzeichnisse"""
    directories = [
        f'{TARGET_DIR}/pdfs',
        f'{TARGET_DIR}/output'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    if flask_env == 'production':
        os.makedirs('/var/log/feuerwehr_dashboard', exist_ok=True)

# Initialisierung
create_directories()
setup_logging()

def graceful_shutdown(signum: int, frame: Any) -> None:
    """Graceful shutdown handler für Produktion"""
    app.logger.info("Graceful shutdown initiiert")
    sys.exit(0)

if __name__ == '__main__':
    # Signal Handler für graceful shutdown
    if flask_env == 'production':
        signal.signal(signal.SIGTERM, graceful_shutdown)
        signal.signal(signal.SIGINT, graceful_shutdown)
    
    # Server-Konfiguration
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5001))  # Backend auf Port 5001
    debug = flask_env != 'production'
    
    app.logger.info(f"Starte Feuerwehr Dashboard - Umgebung: {flask_env}")
    
    try:
        if flask_env == 'production':
            # In Produktion: Verwende Gunicorn oder andere WSGI Server
            app.logger.info("Produktionsumgebung erkannt. Verwende WSGI Server.")
            app.run(host=host, port=port, debug=False, use_reloader=False)
        else:
            # Development: Flask Development Server
            app.run(host=host, port=port, debug=debug, use_reloader=True)
    except Exception as e:
        app.logger.error(f"Fehler beim Starten der Anwendung: {str(e)}")
        error_msg = f"Kritischer Fehler {str(e)} um {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Fehler-Reporting (nur wenn konfiguriert)
        error_url = os.getenv('ERROR_REPORTING_URL')
        if error_url:
            try:
                requests.post(error_url, json={"error": str(e)}, timeout=5)
                app.logger.info("Fehler wurde an Monitoring-System gesendet")
            except Exception:
                app.logger.warning("Fehler-Reporting fehlgeschlagen")
        
        sys.exit(1)