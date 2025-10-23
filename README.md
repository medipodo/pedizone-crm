# PediZone CRM

PediZone CRM - Pediatri klinik yönetim sistemi

## 🚀 Hızlı Deployment

Detaylı rehber için: [QUICKSTART.md](QUICKSTART.md)

## 📚 Dökümanlar

- [QUICKSTART.md](QUICKSTART.md) - Hızlı başlangıç rehberi
- [DEPLOY_FLYIO.md](DEPLOY_FLYIO.md) - Detaylı deployment rehberi

## 💻 Tech Stack

- **Backend**: FastAPI + Python 3.11
- **Frontend**: React 19 + Tailwind CSS + Radix UI
- **Database**: MongoDB Atlas
- **Deployment**: Fly.io

## 🔧 Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --reload
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

## 📦 Deployment

```bash
./deploy-backend.sh
./deploy-frontend.sh
```
