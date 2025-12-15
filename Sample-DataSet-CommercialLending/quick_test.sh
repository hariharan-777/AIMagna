#!/bin/bash
echo "=== Quick System Test ==="
echo ""
echo "1. Backend Health:"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Backend not responding"
echo ""
echo "2. Frontend Check:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5173
echo ""
echo "3. Services Running:"
SERVICES=$(ps aux | grep -E "(uvicorn|vite)" | grep -v grep | wc -l | xargs)
echo "Active services: $SERVICES"
if [ "$SERVICES" -ge 2 ]; then
    echo "✅ Both services running"
else
    echo "⚠️  Some services may be down"
fi
echo ""
echo "4. Quick Agent Import Test:"
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null
python -c "from src.orchestrator_agent.main import run_orchestration; print('✅ All agents OK')" 2>/dev/null || echo "❌ Agent import failed"
echo ""
echo "=== Test Complete ==="

