# Docker Port Forwarding Troubleshooting (Windows)

## Problem
Container shows healthy and Streamlit serves internally, but `netstat -ano | findstr :8501` shows nothing listening on Windows host. Browser shows ERR_CONNECTION_RESET.

## Root Cause
Docker Desktop port forwarding from container to Windows host is not working.

## Solutions to Try (in order)

### 1. **Check Docker Desktop Backend**

Docker Desktop for Windows can use either WSL2 or Hyper-V backend. WSL2 sometimes has networking issues.

**Check your backend:**
- Open Docker Desktop → Settings → General
- Look for "Use the WSL 2 based engine"

**If using WSL2:**
```powershell
# Restart WSL networking
wsl --shutdown
# Wait 10 seconds, then start Docker Desktop again
```

### 2. **Disconnect VPN**

Corporate VPNs frequently block Docker port forwarding.

```powershell
# Disconnect from VPN
# Try accessing http://localhost:8501 again
```

If this works, you'll need to either:
- Run without VPN when using Docker GUI
- Configure VPN split tunneling to exclude localhost
- Use `host.docker.internal` instead (see solution #7)

### 3. **Check Windows Firewall**

```powershell
# Run as Administrator
# Check if Docker is allowed through firewall
Get-NetFirewallRule -DisplayName "*docker*" | Select-Object DisplayName, Enabled, Direction

# If blocked, allow Docker Desktop:
New-NetFirewallRule -DisplayName "Docker Desktop" -Direction Inbound -Action Allow -Program "C:\Program Files\Docker\Docker\resources\com.docker.backend.exe"
```

### 4. **Restart Docker Desktop**

Sometimes Docker Desktop networking gets stuck:

```powershell
# Full restart sequence
docker-compose down
# Close Docker Desktop completely (right-click system tray → Quit Docker Desktop)
# Wait 10 seconds
# Start Docker Desktop
# Wait for it to fully start
docker-compose up workflow-tracker-gui
```

### 5. **Try Different Port Binding Format**

Edit `docker-compose.yml` and change the ports line:

```yaml
# Original
ports:
  - "8501:8501"

# Try this instead
ports:
  - "127.0.0.1:8501:8501"

# Or try a different host port
ports:
  - "8502:8501"  # Access via http://localhost:8502
```

Then rebuild:
```powershell
docker-compose down
docker-compose up workflow-tracker-gui
```

### 6. **Check Docker Desktop Network Settings**

In Docker Desktop:
1. Settings → Resources → Network
2. Try unchecking "Use kernel networking for UDP" (if present)
3. Note the "Docker subnet" setting
4. Click "Apply & Restart"

### 7. **Use host.docker.internal (Alternative)**

If port forwarding won't work, you can reverse the connection direction:

Edit `.streamlit/config.toml`:
```toml
[server]
address = "0.0.0.0"
port = 8501
enableCORS = true  # Enable instead of disable
enableXsrfProtection = true

[browser]
serverAddress = "host.docker.internal"
serverPort = 8501
```

### 8. **Test with Simple Container**

Verify Docker port forwarding works at all:

```powershell
# Run a simple web server
docker run -d -p 8080:80 --name test-nginx nginx

# Check if port appears
netstat -ano | findstr :8080

# Try accessing http://localhost:8080 in browser

# Clean up
docker stop test-nginx
docker rm test-nginx
```

If this doesn't work either, Docker Desktop networking is broken.

### 9. **Check for Port Conflicts**

```powershell
# See all listening ports
netstat -ano | findstr LISTENING

# Check if something else claimed 8501
Get-Process -Id (Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue
```

### 10. **Nuclear Option: Reset Docker Desktop**

If nothing else works:

1. Docker Desktop → Settings → Troubleshoot → "Reset to factory defaults"
2. This will delete all containers, images, volumes
3. Restart Windows
4. Reinstall Docker Desktop if needed

## Diagnostic Commands

Run these and share output for further help:

```powershell
# 1. Show Docker version and backend
docker version
docker info | findstr -i "operating kernel"

# 2. Show container port bindings
docker port workflow-tracker-gui

# 3. Show container network
docker inspect workflow-tracker-gui | findstr -i "ports ipaddress network"

# 4. Test from inside container
docker exec workflow-tracker-gui curl -v http://localhost:8501/

# 5. Check Windows listening ports
netstat -ano | findstr :8501

# 6. Check Docker Desktop is running
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
```

## Most Likely Causes

Based on your symptoms:

1. **VPN blocking Docker networking** (80% likely if on corporate network)
2. **WSL2 networking issue** (15% likely if using WSL2 backend)
3. **Windows Firewall** (5% likely)

Try disconnecting VPN first!
