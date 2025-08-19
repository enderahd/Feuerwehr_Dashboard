#!/usr/bin/env python3
"""Passwort-Check-Tool für das Feuerwehr Dashboard"""

import os
from werkzeug.security import check_password_hash, generate_password_hash

def check_current_password():
    """Überprüft das aktuell konfigurierte Passwort"""
    
    # Lade Umgebungsvariablen
    from dotenv import load_dotenv
    load_dotenv()
    
    # Hole gespeicherten Hash
    stored_hash = os.getenv('PASSWORD_HASH')
    plain_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    print("=== Passwort-Check ===")
    print(f"Gespeicherter Hash: {stored_hash}")
    print(f"Plain Passwort: {plain_password}")
    
    if stored_hash:
        # Teste mit gespeichertem Hash
        is_valid = check_password_hash(stored_hash, plain_password)
        print(f"Hash-Vergleich: {is_valid}")
        
        # Teste auch mit 'admin'
        is_valid_admin = check_password_hash(stored_hash, 'admin')
        print(f"Hash-Vergleich mit 'admin': {is_valid_admin}")
        
    else:
        print("Kein PASSWORD_HASH gefunden - generiere neuen...")
        new_hash = generate_password_hash(plain_password)
        print(f"Neuer Hash für '{plain_password}': {new_hash}")
        
        # Teste neuen Hash
        test_result = check_password_hash(new_hash, plain_password)
        print(f"Test des neuen Hash: {test_result}")

if __name__ == '__main__':
    check_current_password()
