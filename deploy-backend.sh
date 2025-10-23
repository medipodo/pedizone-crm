#!/bin/bash

echo "🚀 PediZone CRM Backend Deployment"
echo "===================================="

cd backend

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Flyctl bulunamadı. Lütfen önce yükleyin:"
    echo "   brew install flyctl"
    exit 1
fi

# Check if already logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "⚠️  Fly.io'ya giriş yapmanız gerekiyor:"
    flyctl auth login
fi

# Check if app exists
if ! flyctl status &> /dev/null 2>&1; then
    echo "📦 Yeni Fly app oluşturuluyor..."
    flyctl launch --no-deploy
    
    echo "🔐 Environment variables ayarlanıyor..."
    flyctl secrets set MONGO_URL="mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/?retryWrites=true&w=majority&appName=Pedizone"
    flyctl secrets set DB_NAME="pedizone_crm"
    flyctl secrets set CORS_ORIGINS="*"
fi

echo "🚢 Backend deploy ediliyor..."
flyctl deploy

echo ""
echo "✅ Backend deployment tamamlandı!"
echo "🌐 URL: https://$(flyctl info -j | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)"
echo ""
echo "Test için:"
echo "  curl https://$(flyctl info -j | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4)/api/"
