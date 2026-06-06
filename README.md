# WombWise

Cycle-based fibroid prevention + AI risk calculator for uterine fibroids.

**One-liner:** WombWise tells women at fibroid risk what to eat, how to manage stress, and what to do today based on their cycle phase, then helps high-risk users find specialist care.

## Features

| Feature | Description |
|---------|-------------|
| **Daily Check-in** | Cycle day + stress + food log -> estrogen risk + 3 micro-actions |
| **Risk Calculator** | AUC ~0.95 Gradient Boosting model for clinical risk assessment |
| **Full Assessment** | Interactive symptoms + profile + lifestyle + blood marker assessment |
| **Appointment Matching** | Specialist booking by region (Germany, UK, USA) |
| **Bleeding Chart** | Interactive Plotly 28-day menstrual flow visualization |
| **Demo Patient** | Black woman, age 32, 87% risk showcase case |

## Stack

- **Backend:** Python, scikit-learn, FastAPI
- **Frontend:** React + Vite + Plotly (deep green + warm white aesthetic)

## Quick Start

### 1. Backend

```bash
pip install -r requirements.txt
python fibroid_concierge.py           # Step 1–2: local model test
python fibroid_shield.py              # Daily prevention engine test
python fibroid_x_predict_voicing.py   # End-to-end MVP test
python wombwise_assessment.py         # Full assessment test
python api.py                         # API on http://127.0.0.1:8000
```

### 2. API Tests

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/demo
curl http://127.0.0.1:8000/api/v1/shield/demo
curl http://127.0.0.1:8000/api/v1/assessment/demo
curl -X POST http://127.0.0.1:8000/analyze -H "Content-Type: application/json" -d "{\"cycle_day\":22,\"stress_level\":4,\"food_log\":\"Coffee, steak with fries, glass of wine\",\"vitamin_d_supplement\":false}"
curl -X POST http://127.0.0.1:8000/api/v1/flow -H "Content-Type: application/json" -d "{\"patient\":{\"age\":32,\"bmi\":28.5,\"family_history\":true,\"heavy_bleeding\":true,\"pelvic_pain_severity\":7,\"anemia\":true,\"fibroid_count\":3,\"largest_fibroid_cm\":5.8,\"african_ancestry\":true,\"nulliparity\":false},\"region\":\"Germany\"}"
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Vite dev server proxies `/api`, `/health`, and `/analyze` to the backend.

## Demo Scenarios

- **Daily Check-in:** Click "Load Demo Check-in" - late luteal phase, high stress, red meat
- **Full Assessment:** Click "Load Full Demo" - symptoms, profile, modifiable risks, and blood markers
- **Risk Assessment:** Click "Load Demo Patient" - Black woman, age 32, 87% risk with bleeding chart

## Disclaimer

For wellness and clinical decision support only. Not a substitute for professional medical advice.
