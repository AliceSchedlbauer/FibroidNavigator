# Fibroid Navigator

AI-powered clinical decision support for uterine fibroid risk assessment.

## Stack

- **Backend:** Python, scikit-learn (Gradient Boosting, AUC ~0.95), FastAPI
- **Frontend:** React + Vite

## Quick Start

### 1. Backend

```bash
pip install -r requirements.txt
python fibroid_concierge.py   # local model test
python api.py                 # starts API on http://127.0.0.1:8000
```

### 2. API Test

```bash
curl http://127.0.0.1:8000/health
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Vite dev server proxies `/api` and `/health` to the backend.

## Disclaimer

For clinical decision support only. Not a substitute for professional medical advice.
