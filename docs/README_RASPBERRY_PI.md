# Feuerwehr Dashboard - Raspberry Pi Produktions-Setup

## 🚀 Automatisches Deployment

### Voraussetzungen
- Raspberry Pi mit Raspberry Pi OS
- SSH-Zugang mit sudo-Rechten
- Internetverbindung

### Installation

1. **Dateien auf Raspberry Pi kopieren:**
```bash
# Via SCP
scp -r . pi@your-raspberry-pi-ip:/home/pi/feuerwehr_dashboard/

# Oder via Git
git clone https://github.com/your-repo/feuerwehr_dashboard.git
cd feuerwehr_dashboard
```

2. **Deployment ausführen:**
```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

3. **Konfiguration anpassen:**
```bash
sudo nano /opt/feuerwehr_dashboard/.env.production
```

**Wichtige Einstellungen:**
- `OPENWEATHER_API_KEY`: Ihr OpenWeather API-Schlüssel
- `PASSWORD`: Ihr Admin-Passwort
- `FLASK_SECRET_KEY`: Wird automatisch generiert

4. **Service neu starten:**
```bash
sudo systemctl restart feuerwehr-dashboard
```

## 🔧 Wartung

### Wartungs-Script verwenden:
```bash
chmod +x maintenance.sh

# Service-Kontrolle
./maintenance.sh start|stop|restart|status

# Logs anzeigen
./maintenance.sh logs          # Systemd logs
./maintenance.sh app-logs      # Application logs

# Update
./maintenance.sh update

# Backup
./maintenance.sh backup

# Test
./maintenance.sh test
```

### Manuelle Befehle:
```bash
# Service-Status
sudo systemctl status feuerwehr-dashboard

# Logs
sudo journalctl -u feuerwehr-dashboard -f
sudo tail -f /var/log/feuerwehr_dashboard/app.log

# Service neu starten
sudo systemctl restart feuerwehr-dashboard

# Nginx neu starten
sudo systemctl restart nginx
```

## 🌐 Zugriff

- **Lokal:** http://localhost
- **Netzwerk:** http://raspberry-pi-ip
- **Standard-Login:** admin123 (bitte ändern!)

## 📁 Verzeichnisstruktur

```
/opt/feuerwehr_dashboard/
├── API_backend.py          # Hauptanwendung
├── wetterdaten.py          # Wetter-Modul
├── wsgi.py                 # WSGI Entry Point
├── templates/              # HTML Templates
├── static/                 # Statische Dateien
├── pdfs/                   # Hochgeladene PDFs
├── output/                 # Generierte Daten
├── .env.production         # Produktions-Konfiguration
└── venv/                   # Python Virtual Environment

/var/log/feuerwehr_dashboard/
├── app.log                 # Application Logs
├── access.log              # Nginx Access Logs
└── error.log               # Nginx Error Logs
```

## 🔐 Sicherheit

### Empfohlene Sicherheitsmaßnahmen:

1. **Starkes Passwort setzen:**
```bash
sudo nano /opt/feuerwehr_dashboard/.env.production
# PASSWORD=ihr_starkes_passwort
```

2. **SSL/TLS aktivieren (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

3. **Firewall konfigurieren:**
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

4. **Automatische Updates:**
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 📊 Monitoring

### System-Monitoring:
```bash
# CPU und Memory
htop

# Disk Usage
df -h

# Service-Status
sudo systemctl status feuerwehr-dashboard nginx
```

### Application-Monitoring:
```bash
# Live Logs
sudo tail -f /var/log/feuerwehr_dashboard/app.log

# Error Count
sudo grep -c "ERROR" /var/log/feuerwehr_dashboard/app.log

# Response Test
curl -I http://localhost
```

## 🚨 Troubleshooting

### Häufige Probleme:

1. **Service startet nicht:**
```bash
sudo journalctl -u feuerwehr-dashboard --no-pager
sudo systemctl status feuerwehr-dashboard
```

2. **Permission Errors:**
```bash
sudo chown -R www-data:www-data /opt/feuerwehr_dashboard
sudo chmod -R 755 /opt/feuerwehr_dashboard
```

3. **Nginx Errors:**
```bash
sudo nginx -t
sudo tail /var/log/nginx/error.log
```

4. **Python Module Errors:**
```bash
cd /opt/feuerwehr_dashboard
source venv/bin/activate
pip install -r requirements.txt
```

### Log-Locations:
- Application: `/var/log/feuerwehr_dashboard/app.log`
- Systemd: `sudo journalctl -u feuerwehr-dashboard`
- Nginx: `/var/log/nginx/access.log` und `/var/log/nginx/error.log`

## 🔄 Backup & Recovery

### Automatisches Backup:
```bash
# Backup erstellen
./maintenance.sh backup

# Cron Job für tägliches Backup
sudo crontab -e
# 0 2 * * * /opt/feuerwehr_dashboard/maintenance.sh backup
```

### Recovery:
```bash
# Backup wiederherstellen
cd /tmp
tar -xzf feuerwehr_dashboard_backup_*.tar.gz
sudo cp -r feuerwehr_dashboard_backup_*/output /opt/feuerwehr_dashboard/
sudo cp -r feuerwehr_dashboard_backup_*/pdfs /opt/feuerwehr_dashboard/
sudo chown -R www-data:www-data /opt/feuerwehr_dashboard
```

Das Dashboard ist jetzt produktionsbereit für Ihren Raspberry Pi! 🚒
