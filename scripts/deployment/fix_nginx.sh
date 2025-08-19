#!/bin/bash
# Enhanced Quick Fix für Nginx-Konfigurationsprobleme

echo "🔧 Feuerwehr Dashboard - Enhanced Quick Fix"
echo "============================================"

PROJECT_NAME="feuerwehr_dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="feuerwehr-dashboard"

# Root-Rechte prüfen
if [[ $EUID -ne 0 ]]; then
   echo "❌ Dieses Script muss als root ausgeführt werden (sudo)"
   exit 1
fi

echo "🔄 Schritt 1: Services stoppen..."
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

echo "📁 Schritt 2: Nginx-Konfiguration neu erstellen..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << 'EOF'
# Frontend Server (Port 80) - Öffentliches Dashboard
server {
    listen 80;
    server_name _;
    
    # Root für statische Frontend-Dateien
    root /opt/feuerwehr_dashboard/static;
    index index.html;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
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
        
        # CORS Headers für Frontend
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept" always;
    }
    
    # Static Assets
    location /static/ {
        alias /opt/feuerwehr_dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable" always;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|py|sh|service)$ {
        deny all;
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
        
        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
}
EOF

echo "🔗 Schritt 3: Site aktivieren..."
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "✅ Schritt 4: Nginx-Konfiguration testen..."
nginx -t
if [ $? -eq 0 ]; then
    echo "✅ Nginx-Konfiguration ist gültig"
else
    echo "❌ Nginx-Konfiguration fehlerhaft - prüfe /var/log/nginx/error.log"
    exit 1
fi

echo "🔧 Schritt 5: Berechtigungen korrigieren..."
chown -R www-data:www-data $INSTALL_DIR
chmod -R 755 $INSTALL_DIR

echo "🚀 Schritt 6: Services starten..."
systemctl daemon-reload
systemctl start nginx
systemctl start $SERVICE_NAME

echo "🧪 Schritt 7: Status prüfen..."
sleep 3

# Status prüfen
nginx_status=$(systemctl is-active nginx)
service_status=$(systemctl is-active $SERVICE_NAME)

echo "Nginx Status: $nginx_status"
echo "Service Status: $service_status"

if [ "$nginx_status" = "active" ] && [ "$service_status" = "active" ]; then
    echo ""
    echo "🎉 Quick Fix erfolgreich!"
    echo ""
    echo "🌐 Dashboard ist verfügbar unter:"
    echo "   Frontend: http://$(hostname -I | awk '{print $1}')/"
    echo "   Backend:  http://$(hostname -I | awk '{print $1}'):5000/"
else
    echo ""
    echo "❌ Problem beim Starten der Services"
    echo ""
    echo "🔍 Debugging:"
    echo "sudo journalctl -u $SERVICE_NAME -n 10"
    echo "sudo journalctl -u nginx -n 10"
fi
