#!/usr/bin/env python3
"""
WSGI Entry Point für Gunicorn
"""

import os
import sys
from pathlib import Path

# Projektpfad zum Python-Pfad hinzufügen
project_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_path))

# Produktionsumgebung laden
if os.path.exists('.env.production'):
    os.environ['FLASK_ENV'] = 'production'
    from dotenv import load_dotenv
    load_dotenv('.env.production')

from API_backend import app

if __name__ == "__main__":
    app.run()
