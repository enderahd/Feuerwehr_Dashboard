# Feuerwehr Dashboard

Ein professionelles Web-Dashboard für die Feuerwehr Glienicke/Nordbahn mit Wetterdaten, Dokumentenverwaltung und sicherer Authentifizierung.

## 🚀 Features

- **Authentifizierung**: Sicheres Login-System mit Session-Management
- **Wetterdaten**: Live-Wetterdaten und 5-Tage-Vorhersage via OpenWeather API
- **Dokumentenverwaltung**: Upload und Verwaltung von PDF-Dokumenten
- **Responsive Design**: Optimiert für Desktop und mobile Geräte
- **Sicherheit**: CSRF-Schutz, Rate-Limiting, sichere Session-Konfiguration

## 📁 Projektstruktur

```
Feuerwehr_Dashboard/
├── 📂 config/                          # Konfigurationsdateien
│   ├── feuerwehr-dashboard.service     # Systemd Service
│   └── weather_icon_links.json        # Wetter-Icon Mappings
├── 📂 docs/                           # Dokumentation
│   ├── README_RASPBERRY_PI.md         # Raspberry Pi Setup
│   ├── DEPLOYMENT_FIX.md             # Deployment Fixes
│   └── PRODUKTION_READY.md           # Produktions-Guide
├── 📂 output/                         # Generierte Dateien
│   ├── wetterdaten.json              # Aktuelle Wetterdaten
│   ├── wettervorhersage.json         # Wettervorhersage
│   └── infos.json                    # System-Informationen
├── 📂 pdfs/                          # PDF-Dokumente
├── 📂 scripts/                       # Maintenance & Deployment
│   ├── 📂 deployment/                # Deployment Scripts
│   │   ├── deploy.sh                 # Hauptdeployment
│   │   ├── quick_fix.sh              # Schnelle Fixes
│   │   └── troubleshoot.sh           # Problemdiagnose
│   └── 📂 maintenance/               # Wartung
│       ├── health_check.py           # System Health Check
│       └── change_password.sh        # Passwort ändern
├── 📂 static/                        # Statische Dateien
│   ├── 📂 css/
│   │   └── styles.css                # Haupt-Stylesheet
│   ├── 📂 js/
│   │   └── script.js                 # JavaScript
│   ├── 📂 images/                    # Logo und Bilder
│   └── 📂 Datenback_images/          # Wetter-Icons
├── 📂 templates/                     # HTML Templates
│   ├── index.html                    # Haupt-Dashboard
│   └── login.html                    # Login-Seite
├── API_backend.py                    # Haupt-Flask-Anwendung
├── wetterdaten.py                    # Wetter-API Module
├── wsgi.py                          # WSGI Entry Point
├── requirements.txt                  # Python Dependencies
├── .env                             # Development Konfiguration
└── .env.production                  # Production Konfiguration
```

## 🛠️ Installation & Setup

### Lokale Entwicklung

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd Feuerwehr_Dashboard
   ```

2. **Virtuelle Umgebung erstellen**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren**
   ```bash
   cp .env.example .env
   # .env bearbeiten und API-Keys eintragen
   ```

5. **Anwendung starten**
   ```bash
   python API_backend.py
   ```

### Raspberry Pi Deployment

Siehe [docs/README_RASPBERRY_PI.md](docs/README_RASPBERRY_PI.md) für detaillierte Anweisungen.

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
# OpenWeather API
OPENWEATHER_API_KEY=your_api_key_here

# Flask Konfiguration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True

# Authentifizierung
PASSWORD=your_admin_password

# Sicherheit
CSRF_ENABLED=False  # True für Produktion
RATE_LIMIT_ENABLED=True

# Pfade
zielverzeichnis=/path/to/dashboard
```

## 🚀 Deployment

### Automatisches Deployment

```bash
# Vollständiges Deployment
sudo ./scripts/deployment/deploy.sh

# Nginx-Probleme beheben
sudo ./scripts/deployment/fix_nginx.sh

# Allgemeine Reparaturen
sudo ./scripts/deployment/quick_fix.sh

# Problemdiagnose
sudo ./scripts/deployment/troubleshoot.sh

# Deployment-spezifische Diagnose  
sudo ./scripts/deployment/troubleshoot_deployment.sh
```

### Häufige Deployment-Probleme

**Problem: `cp: cannot stat 'nginx-dashboard.conf': No such file or directory`**
```bash
sudo ./scripts/deployment/fix_nginx.sh
```

**Problem: Service startet nicht**
```bash
sudo ./scripts/deployment/quick_fix.sh
```

**Problem: Port-Konflikte**
```bash
sudo ./scripts/deployment/troubleshoot_deployment.sh
```

### Manuelle Wartung

```bash
# Health Check
python scripts/maintenance/health_check.py

# Passwort ändern
./scripts/maintenance/change_password.sh
```

## 🔒 Sicherheit

- **Authentifizierung**: Session-basierte Anmeldung
- **CSRF-Schutz**: Aktiviert in Produktionsumgebung
- **Rate-Limiting**: Schutz vor Brute-Force-Angriffen
- **Sichere Headers**: HTTPS-Ready Konfiguration
- **Input-Validierung**: Alle Benutzereingaben werden validiert

## 📊 Monitoring

- **Health Check**: Automatische Systemüberwachung
- **Logging**: Strukturierte Logs mit Rotation
- **Error Handling**: Umfassende Fehlerbehandlung

## 🔄 Wartung

### Tägliche Aufgaben
- Logs überprüfen: `tail -f app.log`
- System Status: `python scripts/maintenance/health_check.py`

### Wöchentliche Aufgaben
- Updates prüfen: `pip list --outdated`
- Backup erstellen
- Performance überprüfen

## 📝 Changelog

### v2.0.0 (2025-08-19)
- ✅ Projektstruktur komplett reorganisiert
- ✅ Sicherheit verbessert (keine Passwörter in Logs)
- ✅ CSRF-Handling korrigiert
- ✅ Deployment-Automatisierung
- ✅ Umfassende Dokumentation

### v1.0.0
- Grundfunktionen implementiert

## 🤝 Mitwirken

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📞 Support

Bei Problemen oder Fragen:
- Issue im GitHub Repository erstellen
- Logs mit `./scripts/deployment/troubleshoot.sh` sammeln

## 📄 Lizenz

Dieses Projekt ist für die Feuerwehr Glienicke/Nordbahn entwickelt.

---

**Entwickelt für die Feuerwehr Glienicke/Nordbahn** 🚒
