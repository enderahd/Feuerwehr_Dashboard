#!/usr/bin/env python3
"""
Health Check Script für Feuerwehr Dashboard
Überwacht System-Status und Anwendungsgesundheit
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path

def check_service_status():
    """Prüft den systemd Service Status"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'feuerwehr-dashboard'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except Exception:
        return False

def check_web_response():
    """Prüft HTTP-Response der Anwendung"""
    try:
        response = requests.get('http://localhost:5000', timeout=10)
        return response.status_code in [200, 302]  # 302 = Redirect zum Login
    except Exception:
        return False

def check_disk_space():
    """Prüft verfügbaren Festplattenspeicher"""
    try:
        result = subprocess.run(
            ['df', '/opt/feuerwehr_dashboard', '--output=pcent'],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            usage = int(lines[1].replace('%', ''))
            return usage < 90  # Warnung bei >90% Nutzung
    except Exception:
        pass
    return True

def check_log_files():
    """Prüft Log-Dateien auf Errors"""
    log_file = '/var/log/feuerwehr_dashboard/app.log'
    if not os.path.exists(log_file):
        return True
    
    try:
        # Prüfe letzte 100 Zeilen auf CRITICAL/ERROR
        result = subprocess.run(
            ['tail', '-100', log_file],
            capture_output=True,
            text=True
        )
        
        error_count = result.stdout.count('ERROR')
        critical_count = result.stdout.count('CRITICAL')
        
        return error_count < 5 and critical_count == 0
    except Exception:
        return True

def check_memory_usage():
    """Prüft Memory-Verbrauch"""
    try:
        result = subprocess.run(
            ['free', '-m'],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        mem_line = lines[1].split()
        total = int(mem_line[1])
        used = int(mem_line[2])
        
        usage_percent = (used / total) * 100
        return usage_percent < 85  # Warnung bei >85% Memory-Nutzung
    except Exception:
        return True

def check_temperature():
    """Prüft CPU-Temperatur (Raspberry Pi spezifisch)"""
    temp_file = '/sys/class/thermal/thermal_zone0/temp'
    if not os.path.exists(temp_file):
        return True
    
    try:
        with open(temp_file, 'r') as f:
            temp = int(f.read().strip()) / 1000
            return temp < 70  # Warnung bei >70°C
    except Exception:
        return True

def send_alert(message):
    """Sendet Alert (kann erweitert werden für E-Mail, Slack, etc.)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alert_message = f"[{timestamp}] FEUERWEHR DASHBOARD ALERT: {message}"
    
    # Log Alert
    print(alert_message)
    
    # Optional: Sende an externes Monitoring
    # requests.post('your-monitoring-webhook', json={'message': alert_message})

def main():
    """Hauptfunktion für Health Check"""
    print("🚒 Feuerwehr Dashboard - Health Check")
    print("=" * 50)
    
    checks = [
        ("Service Status", check_service_status),
        ("Web Response", check_web_response),
        ("Disk Space", check_disk_space),
        ("Log Health", check_log_files),
        ("Memory Usage", check_memory_usage),
        ("CPU Temperature", check_temperature)
    ]
    
    all_healthy = True
    
    for check_name, check_func in checks:
        try:
            is_healthy = check_func()
            status = "✅ OK" if is_healthy else "❌ FAIL"
            print(f"{check_name:<15}: {status}")
            
            if not is_healthy:
                all_healthy = False
                send_alert(f"{check_name} check failed")
                
        except Exception as e:
            print(f"{check_name:<15}: ❌ ERROR - {e}")
            all_healthy = False
            send_alert(f"{check_name} check error: {e}")
    
    print()
    
    if all_healthy:
        print("🎉 Alle Checks erfolgreich - System ist gesund!")
        sys.exit(0)
    else:
        print("⚠️  Einige Checks sind fehlgeschlagen - Aktion erforderlich!")
        sys.exit(1)

if __name__ == "__main__":
    main()
