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
curl http://127.0.0.1:8000/api/v1/demo
curl -X POST http://127.0.0.1:8000/api/v1/risk -H "Content-Type: application/json" -d "{\"age\":32,\"bmi\":28.5,\"family_history\":true,\"heavy_bleeding\":true,\"pelvic_pain_severity\":7,\"anemia\":true,\"fibroid_count\":3,\"largest_fibroid_cm\":5.8,\"african_ancestry\":true,\"nulliparity\":false}"
```

### Demo Patient

Click **Load Demo Patient** in the UI or call `GET /api/v1/demo` for the showcase case:
Black woman, age 32, **87% risk**, with a 28-day menstrual bleeding chart.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Vite dev server proxies `/api` and `/health` to the backend.

## Disclaimer

For clinical decision support only. Not a substitute for professional medical advice.
