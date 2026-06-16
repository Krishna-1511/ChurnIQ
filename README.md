# ChurnIQ — Bank Customer Churn Intelligence Platform

End-to-end ML pipeline: MySQL → XGBoost inference → real-time alerts → dashboard UI.

---

## Project Structure

```
churn_project/
├── db.py            # SQLAlchemy DB helpers (fetch features, write predictions, queries)
├── preprocess.py    # Feature encoding (matches training: France=0, Germany=1, Spain=2)
├── inference.py     # XGBoost scoring, threshold=0.60, 0–100 risk scale
├── pipeline.py      # Orchestrator — fetch → score → write → triggers fire alerts
├── main.py          # FastAPI REST API (all endpoints the dashboard uses)
├── scheduler.py     # APScheduler — nightly batch + hourly incremental re-score
├── db_setup.sql     # View + alert table + triggers to run in MySQL
├── dashboard.html   # Full standalone dashboard (open in browser)
└── models/
    └── churn_model.pkl   ← PUT YOUR EXPORTED MODEL HERE
```

---

## Quick Start

### 1. Export your trained model

In your Kaggle notebook / training environment:
```python
import pickle
with open('churn_model.pkl', 'wb') as f:
    pickle.dump(model, f)
```
Copy `churn_model.pkl` → `churn_project/models/churn_model.pkl`

### 2. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pymysql xgboost scikit-learn \
            pandas numpy apscheduler
```

### 3. Set up the database

```bash
# Run this in your MySQL client (once)
mysql -u root -p bankdb < db_setup.sql
```

### 4. Configure DB connection

```bash
export DATABASE_URL="mysql+pymysql://root:yourpassword@localhost:3306/bankdb"
```

### 5. Start the API server

```bash
cd churn_project
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: http://localhost:8000/docs

### 6. Open the dashboard

Open `dashboard.html` directly in your browser.
(The dashboard works with mock data even without the backend — great for demos.)

### 7. Start the scheduler (optional)

```bash
python scheduler.py
```
This runs nightly full-batch scoring (2am IST) + hourly incremental scoring for recently active customers.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Dashboard KPIs |
| GET | `/api/customers` | Paginated customer list with risk scores |
| GET | `/api/customers/{id}` | Full customer detail |
| GET | `/api/alerts` | Unactioned churn alerts |
| POST | `/api/alerts/action` | Mark alert actioned |
| GET | `/api/risk-distribution` | Pie chart data |
| GET | `/api/country-risk` | Bar chart data |
| POST | `/api/pipeline/run` | Trigger scoring (sync) |
| POST | `/api/pipeline/run-async` | Trigger scoring (background) |

---

## How the Pipeline Works

```
DB (vw_model_features)
        ↓ fetch_features()
   preprocess.py          ← country/gender encoding matches training
        ↓
   XGBoost.predict_proba  ← threshold 0.60
        ↓ risk_score = prob × 100
   Churn_Predictions      ← UPSERT
        ↓ DB TRIGGER fires
   Churn_Alerts           ← alert_sent=0 for Medium/High
        ↓
   Dashboard polls /api/alerts
```

## Model Details

- Algorithm: XGBoost (colsample_bytree=0.8, learning_rate=0.05, max_depth=5, n_estimators=250)
- Threshold: 0.60 (optimises precision on churn class: 56% precision, 71% recall)
- Class imbalance: handled via `scale_pos_weight`
- Test accuracy: 82.55%  |  Train accuracy: 87.68%
- NO StandardScaler applied (raw features fed directly, matching training)

## Country Note

The training data only had France, Germany, Spain. Your DB has India/USA/UK customers too.
Those map to -1 (unknown). Their scores are directionally useful but treat with caution.
Consider retraining with the full country set when you have enough data.
