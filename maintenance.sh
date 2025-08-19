#!/bin/bash
# Wartungs-Script für Feuerwehr Dashboard

PROJECT_NAME="feuerwehr_dashboard"
SERVICE_NAME="feuerwehr-dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"

case "$1" in
    start)
        echo "🚀 Starte $SERVICE_NAME..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "⏹️ Stoppe $SERVICE_NAME..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "🔄 Starte $SERVICE_NAME neu..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        echo "📊 Status von $SERVICE_NAME:"
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "📋 Logs von $SERVICE_NAME:"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    app-logs)
        echo "📋 Application Logs:"
        sudo tail -f /var/log/$PROJECT_NAME/app.log
        ;;
    update)
        echo "🔄 Update $PROJECT_NAME..."
        cd $INSTALL_DIR
        git pull
        source venv/bin/activate
        pip install -r requirements.txt
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Update abgeschlossen!"
        ;;
    backup)
        echo "💾 Erstelle Backup..."
        BACKUP_DIR="/tmp/${PROJECT_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        cp -r $INSTALL_DIR/.env.production $BACKUP_DIR/
        cp -r $INSTALL_DIR/output $BACKUP_DIR/
        cp -r $INSTALL_DIR/pdfs $BACKUP_DIR/
        tar -czf "${BACKUP_DIR}.tar.gz" -C /tmp $(basename $BACKUP_DIR)
        rm -rf $BACKUP_DIR
        echo "✅ Backup erstellt: ${BACKUP_DIR}.tar.gz"
        ;;
    test)
        echo "🧪 Teste Service..."
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
            echo "✅ Service antwortet korrekt"
        else
            echo "❌ Service antwortet nicht"
        fi
        ;;
    *)
        echo "Verwendung: $0 {start|stop|restart|status|logs|app-logs|update|backup|test}"
        exit 1
        ;;
esac
