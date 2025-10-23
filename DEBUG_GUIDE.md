# MPA Flask App - Step-by-Step Debug Guide

## Quick Start Command
```bash
cd "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app" && ./start_app.sh
```

## Stop Command
```bash
cd "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app" && ./stop_app.sh
```

## Manual Troubleshooting Steps

### 1. Environment Check
```bash
# Check Python
which python3
python3 --version

# Check app directory
ls -la "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app/"
```

### 2. Dependency Check
```bash
cd "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app"

# Test critical imports
python3 -c "import flask; print('✓ Flask OK')"
python3 -c "import pandas; print('✓ Pandas OK')"
python3 -c "import gfwapiclient; print('✓ GFW Client OK')"

# Install if missing
pip3 install flask pandas gfw-api-python-client reportlab flask-cors
```

### 3. Port Check
```bash
# Check if port 5000 is free
ss -tlnp | grep :5000
# OR
python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 5000)); print('Port 5000 available'); s.close()"
```

### 4. Manual Start (for debugging)
```bash
cd "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app"
python3 app.py
```

### 5. Check Logs
```bash
# View startup logs
cat "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app/startup.log"

# View Flask logs
cat "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app/flask_app.log"
```

### 6. Health Check
```bash
# Test connectivity
curl -I http://127.0.0.1:5000
# OR
curl http://127.0.0.1:5000 | head -20
```

## Common Issues & Solutions

### Issue: "python: command not found"
**Solution:** Use `python3` instead:
```bash
python3 app.py
```

### Issue: "Port 5000 already in use"
**Solution:** Kill existing process:
```bash
# Find process
ss -tlnp | grep :5000
# Kill process by PID
kill <PID>
# OR use stop script
./stop_app.sh
```

### Issue: "Module not found"
**Solution:** Install dependencies:
```bash
pip3 install -r requirements.txt
# OR individually
pip3 install flask pandas gfw-api-python-client reportlab flask-cors
```

### Issue: "Permission denied"
**Solution:** Make scripts executable:
```bash
chmod +x start_app.sh stop_app.sh
```

### Issue: App starts but not accessible
**Solution:** Check firewall/WSL network:
- Ensure Windows firewall allows port 5000
- Try accessing via `localhost:5000` instead of `127.0.0.1:5000`
- For WSL2, check port forwarding

## Debug Output Interpretation

### Successful Start
```
[SUCCESS] Environment checks passed
[SUCCESS] Dependencies checked  
[SUCCESS] Port 5000 available
[SUCCESS] App process running
[SUCCESS] Health check passed
🚀 MPA Flask App is running!
🌐 URL: http://127.0.0.1:5000
```

### Failed Start Indicators
- `[ERROR] python3 not found` → Install Python 3
- `[ERROR] Port 5000 already in use` → Stop existing process
- `[ERROR] Missing dependencies` → Install packages
- `[ERROR] Health check failed` → Check flask_app.log

## Emergency Recovery

If all else fails:
```bash
# Kill all Python processes (CAUTION!)
pkill -f python3

# Remove PID file
rm -f "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app/app.pid"

# Clean start
cd "/mnt/d/EJSN 2025 grant/GFW-Extract/mpa_app"
./start_app.sh
```

## Testing Checklist

After successful start, verify:
- [ ] App responds at http://127.0.0.1:5000
- [ ] MPA search autocomplete works
- [ ] Date picker functions
- [ ] Test analysis with "Lyme Bay" MPA
- [ ] Check browser console for errors
- [ ] Verify export buttons work

## Performance Monitoring

```bash
# Monitor process
watch -n 2 'ps aux | grep python3'

# Monitor port
watch -n 2 'ss -tlnp | grep :5000'

# Monitor logs
tail -f flask_app.log startup.log
```