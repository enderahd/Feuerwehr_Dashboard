from flask import Flask, request, jsonify
import os

app = Flask(__name__)
TARGET_DIR = 'app.log'
API_KEY = 'isudhfasbdfjbflk_sdfhcuadgasfi_hisfduihiasd_nhiasdisad_icfd' # <-- Setze hier deinen API-Key

# Log-Datei initialisieren
if os.path.exists(TARGET_DIR):
    os.remove(TARGET_DIR)
with open(TARGET_DIR, 'w') as f:
    pass

def require_api_key(func):
    def wrapper(*args, **kwargs):
        key = request.headers.get('x-api-key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/error', methods=['POST'])
@require_api_key
def log_error():
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    error_message = request.json.get('error')
    if not error_message:
        return jsonify({'error': 'No error message provided'}), 400

    try:
        ip = request.remote_addr
        with open(f'{TARGET_DIR}/{ip}', 'a', encoding='utf-8') as f:
            f.write(f"{error_message}\n")
        return jsonify({'message': 'Error logged successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    app.run(debug=True, host='100.104.101.101', port=5000)