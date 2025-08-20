# 🚒 Feuerwehr Dashboard

Ein professionelles Web-Dashboard für die Feuerwehr mit Wetterdaten, Dokumentenverwaltung und sicherer Authentifizierung.

## ✨ Features

- **🔐 Authentifizierung**: Sicheres Login-System mit Session-Management
- **🌤️ Wetterdaten**: Live-Wetterdaten und 5-Tage-Vorhersage via OpenWeather API
- **📄 Dokumentenverwaltung**: Upload und Verwaltung von PDF-Dokumenten
- **📱 Responsive Design**: Optimiert für Desktop und mobile Geräte
- **🛡️ Sicherheit**: CSRF-Schutz, Rate-Limiting, sichere Session-Konfiguration

## 📁 Projektstruktur

```
Feuerwehr_Dashboard/
├── 📂 output/                        # Generierte Dateien
│   ├── wetterdaten.json             # Aktuelle Wetterdaten
│   ├── wettervorhersage.json        # Wettervorhersage
│   └── infos.json                   # System-Informationen
├── 📂 pdfs/                         # PDF-Dokumente
├── 📂 static/                       # Statische Dateien
│   ├── 📂 css/
│   │   └── styles.css               # Haupt-Stylesheet
│   ├── 📂 js/
│   │   └── script.js                # JavaScript
│   ├── 📂 images/                   # Logo und Bilder
│   └── 📂 Datenback_images/         # Wetter-Icons
├── 📂 templates/                    # HTML Templates
│   ├── index.html                   # Haupt-Dashboard
│   └── login.html                   # Login-Seite
├── API_backend.py                   # Haupt-Flask-Anwendung
├── wetterdaten.py                   # Wetter-API Module
├── wsgi.py                         # WSGI Entry Point
├── weather_icon_links.json         # Wetter-Icon Mappings
└── requirements.txt                 # Python Dependencies
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
```

## 🚀 Installation

### Schnellstart

1. **Repository klonen**
   ```bash
   git clone https://github.com/enderahd/Feuerwehr_Dashboard.git
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
   # Erstelle .env Datei mit:
   OPENWEATHER_API_KEY=your_api_key_here
   PASSWORD=your_admin_password
   ```

5. **Anwendung starten**
   ```bash
   python API_backend.py
   ```

   Dashboard öffnen: `http://localhost:5000`

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)

```bash
# OpenWeather API (erforderlich)
OPENWEATHER_API_KEY=your_api_key_here

# Admin-Passwort
PASSWORD=your_admin_password

# Optional: Flask Konfiguration
FLASK_SECRET_KEY=auto_generated_if_not_set
FLASK_ENV=production
FLASK_DEBUG=False
```

### OpenWeather API Key

1. Registrierung: https://openweathermap.org/api
2. API Key generieren
3. In `.env` Datei eintragen

## �️ Technische Details

### Architektur
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Wetter-API**: OpenWeatherMap
- **Authentifizierung**: Session-based
- **Sicherheit**: CSRF-Schutz, Rate-Limiting

### Systemanforderungen
- Python 3.8+
- 512MB RAM
- 1GB Speicher

## 🔒 Sicherheitsfeatures

- **� Sichere Authentifizierung**: Session-basiertes Login-System
- **🛡️ CSRF-Schutz**: Schutz vor Cross-Site Request Forgery
- **⚡ Rate-Limiting**: Schutz vor Brute-Force-Angriffen
- **🔒 Sichere Headers**: HTTPS-Ready Konfiguration
- **✅ Input-Validierung**: Alle Benutzereingaben werden validiert

## � Browser-Unterstützung

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🤝 Mitwirken

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## � Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details.

---

**🚒 Professionelles Dashboard für Feuerwehren**
