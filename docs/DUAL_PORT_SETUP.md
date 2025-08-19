# 🚒 Feuerwehr Dashboard - Dual-Port Setup

## Port-Aufteilung nach Deployment:

### 🌐 **Frontend (Öffentlich)** 
- **URL**: `http://raspberry-pi-ip/`
- **Port**: 80 (Standard HTTP)
- **Zweck**: Öffentliches Dashboard für Besucher
- **Inhalt**: 
  - Live Wetterdaten
  - PDF-Anzeigen 
  - Lauftext
  - Uhrzeit/Datum
- **Authentifizierung**: Keine erforderlich

### 🔧 **Backend (Admin)**
- **URL**: `http://raspberry-pi-ip:5000/`
- **Port**: 5000 (über Nginx Proxy)
- **Intern**: Port 5001 (Flask App)
- **Zweck**: Admin-Interface für Verwaltung
- **Inhalt**:
  - Login erforderlich
  - PDF-Upload/Management
  - Wetter-Updates
  - System-Konfiguration
- **Authentifizierung**: Passwort erforderlich

## 🏗️ Architektur:

```
Internet
    ↓
[Nginx auf Port 80] ← Frontend Dashboard (static/index.html)
    ↓ /api/public/*
[Flask App Port 5001] ← API für Frontend-Daten

[Nginx auf Port 5000] ← Admin-Interface 
    ↓
[Flask App Port 5001] ← Vollständiges Backend
```

## 🚀 Deployment-Befehle:

```bash
# Vollständiges Deployment
sudo ./scripts/deployment/deploy.sh

# Nur Backend neu starten
sudo systemctl restart feuerwehr-dashboard

# Nur Nginx neu starten  
sudo systemctl restart nginx
```

## 🧪 Lokale Tests:

```bash
# Backend Test (Development)
python API_backend.py
# → http://localhost:5001

# Frontend Test  
cd static && python -m http.server 8080
# → http://localhost:8080
```

## ✅ Nach Deployment verfügbar:

1. **Öffentliches Dashboard**: `http://pi-ip/`
   - Automatische Wetter-Updates
   - PDF-Anzeige 
   - Kein Login nötig

2. **Admin-Bereich**: `http://pi-ip:5000/`
   - Login: Password aus .env.production
   - PDF-Upload Management
   - System-Konfiguration

## 🔧 Wartung:

```bash
# Service Status prüfen
sudo systemctl status feuerwehr-dashboard
sudo systemctl status nginx

# Logs anzeigen
sudo journalctl -u feuerwehr-dashboard -f
sudo tail -f /var/log/nginx/access.log

# Konfiguration testen
sudo nginx -t
```
