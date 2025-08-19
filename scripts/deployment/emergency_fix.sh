#!/bin/bash
# Sofort-Fix für das aktuelle Problem auf dem Server

echo "🚨 SOFORT-FIX für Frontend/Login-Probleme"
echo "========================================="

PROJECT_NAME="feuerwehr_dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="feuerwehr-dashboard"

# Root-Rechte prüfen
if [[ $EUID -ne 0 ]]; then
   echo "❌ Dieses Script muss als root ausgeführt werden (sudo)"
   exit 1
fi

echo "🔄 Schritt 1: Service stoppen..."
systemctl stop $SERVICE_NAME
systemctl stop nginx

echo "📝 Schritt 2: Korrigierte Nginx-Konfiguration erstellen..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << 'EOF'
# Frontend Server (Port 80) - Öffentliches Dashboard
server {
    listen 80;
    server_name _;
    
    # Root für statische Frontend-Dateien
    root /opt/feuerwehr_dashboard/static;
    index index.html;
    
    # Frontend Route - Hauptseite
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API Endpoints für Frontend (ohne Auth)
    location /api/public/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static Assets
    location /static/ {
        alias /opt/feuerwehr_dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Backend Server (Port 5000) - Admin Interface
server {
    listen 5000;
    server_name _;
    
    client_max_body_size 16M;
    
    # Backend Admin Interface
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "🔧 Schritt 3: CSRF deaktivieren in .env.production..."
if [ -f "$INSTALL_DIR/.env.production" ]; then
    # CSRF_ENABLED auf False setzen
    if grep -q "CSRF_ENABLED" "$INSTALL_DIR/.env.production"; then
        sed -i 's/CSRF_ENABLED=.*/CSRF_ENABLED=False/' "$INSTALL_DIR/.env.production"
    else
        echo "CSRF_ENABLED=False" >> "$INSTALL_DIR/.env.production"
    fi
    echo "✅ CSRF deaktiviert"
else
    echo "❌ .env.production nicht gefunden!"
fi

echo "🔗 Schritt 4: Sites aktivieren..."
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "✅ Schritt 5: Nginx testen..."
nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Nginx-Konfiguration fehlerhaft!"
    exit 1
fi

echo "🔧 Schritt 6: Berechtigungen sicherstellen..."
chown -R www-data:www-data $INSTALL_DIR
chmod -R 755 $INSTALL_DIR

echo "🚀 Schritt 7: Services starten..."
systemctl daemon-reload
systemctl start nginx
systemctl start $SERVICE_NAME

echo "⏳ Schritt 8: Warten auf Service-Start..."
sleep 5

# Status prüfen
nginx_status=$(systemctl is-active nginx)
service_status=$(systemctl is-active $SERVICE_NAME)

echo ""
echo "📊 Status:"
echo "Nginx: $nginx_status"
echo "Backend: $service_status"

if [ "$nginx_status" = "active" ] && [ "$service_status" = "active" ]; then
    echo ""
    echo "🎉 FIX ERFOLGREICH!"
    echo ""
    echo "🌐 Jetzt verfügbar:"
    echo "   Frontend (Öffentlich): http://$(hostname -I | awk '{print $1}')/"
    echo "   Backend (Admin):       http://$(hostname -I | awk '{print $1}'):5000/"
    echo ""
    echo "🔑 Login-Daten für Backend:"
    echo "   Passwort: test1234"
    echo ""
    echo "✅ Frontend sollte jetzt ohne Login erreichbar sein!"
    echo "✅ Backend-Login sollte ohne CSRF-Fehler funktionieren!"
else
    echo ""
    echo "❌ Problem beim Service-Start"
    echo ""
    echo "🔍 Debug-Befehle:"
    echo "sudo journalctl -u $SERVICE_NAME -n 10"
    echo "sudo journalctl -u nginx -n 10"
    echo "sudo tail -f /var/log/feuerwehr_dashboard/app.log"
fi
