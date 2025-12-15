# Quick Testing Guide

## Step-by-Step Testing Instructions

### Step 1: Verify Services Are Running
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend (open in browser)
open http://localhost:5173
# Or visit: http://localhost:5173
```

**Expected:** Both should respond successfully.

---

### Step 2: Test via Browser (Easiest)

1. **Open Frontend UI**
   ```
   http://localhost:5173
   ```

2. **Start Workflow**
   - Click "Start Pipeline" or "Upload Files"
   - The workflow will run automatically

3. **Monitor Progress**
   - Watch real-time updates in the UI
   - Check the progress bar

---

### Step 3: Test via API (Quick Command)

```bash
# 1. Get API info
curl http://localhost:8000/

# 2. Get target schema
curl http://localhost:8000/schema/target | python -m json.tool

# 3. View API documentation
open http://localhost:8000/docs
```

---

### Step 4: Test Full Workflow (Command Line)

```bash
cd Sample-DataSet-CommercialLending
source venv/bin/activate
export $(grep -v '^#' .env | xargs)

python -c "
import uuid
from datetime import datetime
from src.orchestrator_agent.main import run_orchestration

run_id = f'run_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}'
print(f'Starting workflow: {run_id}')
run_orchestration(run_id, websocket_manager=None, state_store=None, hitl_store=None)
print('Workflow completed!')
"
```

---

### Step 5: Verify Results in BigQuery

```bash
# Check tables were created
source venv/bin/activate
export $(grep -v '^#' .env | xargs)

python -c "
from google.cloud import bigquery
import os
client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
tables = list(client.list_tables(f\"{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET')}\"))
print(f'Found {len(tables)} tables')
for t in tables[:5]:
    print(f'  - {t.table_id}')
"
```

---

## Quick Health Check Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash
echo "=== Quick System Test ==="
echo ""
echo "1. Backend Health:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo "2. Frontend Check:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5173
echo ""
echo "3. Services Running:"
ps aux | grep -E "(uvicorn|vite)" | grep -v grep | wc -l | xargs echo "Active services:"
echo ""
echo "✅ Test complete!"
```

Run: `chmod +x quick_test.sh && ./quick_test.sh`

---

## Common Issues & Quick Fixes

**Backend not responding?**
```bash
cd Sample-DataSet-CommercialLending
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
python -m uvicorn src.nl_agent.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend not responding?**
```bash
cd Sample-DataSet-CommercialLending/frontend
npm run dev
```

**Import errors?**
```bash
cd Sample-DataSet-CommercialLending
source venv/bin/activate
pip install -r requirements.txt
```

---

## Success Indicators

✅ Backend returns: `{"status":"healthy"}`
✅ Frontend loads in browser
✅ API docs accessible at `/docs`
✅ Workflow completes with "Workflow completed successfully!"
✅ Tables appear in BigQuery dataset

