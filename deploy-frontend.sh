#!/bin/bash

echo "🚀 PediZone CRM Frontend Deployment"
echo "===================================="

# Get backend URL first
cd backend
BACKEND_URL=$(flyctl info -j 2>/dev/null | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend henüz deploy edilmemiş!"
    echo "   Önce backend'i deploy edin: ./deploy-backend.sh"
    exit 1
fi

cd ../frontend

# Update fly.toml with actual backend URL
sed -i.bak "s|REACT_APP_BACKEND_URL = \".*\"|REACT_APP_BACKEND_URL = \"https://$BACKEND_URL\"|g" fly.toml

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Flyctl bulunamadı. Lütfen önce yükleyin:"
    echo "   brew install flyctl"
    exit 1
fi

# Check if app exists
if ! flyctl status &> /dev/null 2>&1; then
    echo "📦 Yeni Fly app oluşturuluyor..."
    flyctl launch --no-deploy
fi

echo "🚢 Frontend deploy ediliyor..."
echo "   Backend URL: https://$BACKEND_URL"
flyctl deploy

echo ""
echo "✅ Frontend deployment tamamlandı!"
echo "🌐 URL: https://$(flyctl info -j | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)"
echo ""
echo "🎉 Uygulamanız hazır! Tarayıcıda açmak için:"
echo "   flyctl open"
