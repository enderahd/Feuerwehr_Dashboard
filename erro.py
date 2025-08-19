import os
import sys
import traceback
import requests
import datetime

# Konfiguration
LOG_FILE = "/var/log/linux_error_log.txt"  # Passe den Pfad ggf. an
ALERT_IP = "http://192.168.1.100:5000/error"  # Ziel-IP und Port anpassen
WATCHED_SCRIPT = "/pfad/zum/anderen_script.py"  # Pfad zum zu überwachenden Script

def log_error(error_msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {error_msg}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def send_alert(error_msg):
    try:
        requests.post(ALERT_IP, json={"error": error_msg})
    except Exception as e:
        log_error(f"Fehler beim Senden der Benachrichtigung: {e}")

def restart_script():
    os.execv(sys.executable, ['python3', WATCHED_SCRIPT])

def restart_system():
    os.system("sudo reboot")

def main():
    try:
        # Hier kann beliebiger Code stehen, der überwacht werden soll
        # Beispiel: exec(open(WATCHED_SCRIPT).read())
        pass
    except Exception as e:
        error_msg = ''.join(traceback.format_exception(*sys.exc_info()))
        log_error(error_msg)
        send_alert(error_msg)
        # Wähle eine der folgenden Zeilen:
        # restart_script()  # Nur das andere Python-Skript neu starten
        # restart_system()  # Das ganze System neu starten

if __name__ == "__main__":
    main()