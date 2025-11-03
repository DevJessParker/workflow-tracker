# Windows Quick Start Guide

## Fix the Flickering Issue

**The flickering happens because Streamlit watches for file changes and reloads when output files are written.**

### Solution: Pull the latest changes

```powershell
# Pull the fix from your branch
git pull origin claude/evaluate-codebase-011CUm8owxwPG2GueWZxoG1q
```

This will create `.streamlit/config.toml` which disables the file watcher.

### Verify the Config File Exists

After pulling, check that this file exists:
```
C:\Users\jparker\github\workflow-tracker\.streamlit\config.toml
```

If it doesn't exist, create it manually:

**1. Create the directory:**
```powershell
mkdir .streamlit
```

**2. Create `config.toml` file with this content:**
```toml
[server]
# Disable file watcher to prevent flickering when output files are written
fileWatcherType = "none"

# Disable auto-reload on file changes
runOnSave = false

# Set headless mode for better stability
headless = true

[browser]
# Automatically open browser
gatherUsageStats = false

[client]
# Disable toolbar to reduce UI flickering
toolbarMode = "minimal"

# Show error details
showErrorDetails = true
```

## Running the Scanner

**1. Stop the current Streamlit app:**
- Press `CTRL+C` multiple times (2-3 times rapidly)
- If that doesn't work, close the terminal and open a new one

**2. Navigate to your repo:**
```powershell
cd C:\Users\jparker\github\workflow-tracker
```

**3. Run Streamlit:**
```powershell
python -m streamlit run scanner\cli\streamlit_app.py
```

**4. Open:** http://localhost:8501

## The Flickering Should Be Gone! ✅

The config file tells Streamlit:
- ✅ Don't watch for file changes (`fileWatcherType = "none"`)
- ✅ Don't auto-reload when files are saved (`runOnSave = false`)
- ✅ Use minimal UI to reduce flickering (`toolbarMode = "minimal"`)

## Testing Your Angular + WPF Repository

Once the GUI loads without flickering:

### 1. Configure the Scan

**Repository Path:** Enter your Angular/WPF repo path
```
C:\Users\jparker\path\to\your\project
```

**File Extensions:**
```
.cs,.ts,.html,.xaml
```

**Detection Options:** ✅ Check all boxes

**Click:** 🔍 Start Scan

### 2. View Results

After scanning completes (should stay stable now, no flickering):

Go to **📊 Visualizations** tab:
- **Filter By:** Module/Directory
- **Select:** Your components folder
- **Max Nodes:** 50
- **Click:** 🎨 Generate Diagram

### What You'll See

Complete user workflows from UI to backend:

```
[UI: Click] → [HTTP POST /api/save] → [DB Read: Users] → [DB Write: Audit]
```

**Node Colors:**
- 🟡 **Yellow** - UI events (Angular `(click)`, WPF `Click=""`)
- 🔵 **Blue** - HTTP calls (`this.http.get()`, `HttpClient.GetAsync()`)
- 🟢 **Green** - Database reads
- 🟠 **Orange** - Database writes

## Troubleshooting

### Still Flickering?
1. Make sure `.streamlit/config.toml` exists
2. Restart Streamlit completely (close terminal, reopen)
3. Clear browser cache: `Shift + F5`

### Can't Stop Streamlit?
```powershell
# Find and kill the process
taskkill /F /IM streamlit.exe

# Or close the terminal window
```

### App Won't Start?
```powershell
# Make sure you're in the right directory
cd C:\Users\jparker\github\workflow-tracker

# Verify imports work
python test_imports.py
```

## Output Files

After scanning, check the `output` folder:
```
C:\Users\jparker\github\workflow-tracker\output\
```

You'll find:
- `workflow_graph.json` - Raw data
- `workflow_graph.html` - Interactive visualization (open in browser)
- `workflow_diagram.md` - Mermaid diagram (paste into GitHub)

## Next Steps

- See `ANGULAR_WPF_TESTING.md` for tech-stack-specific examples
- See `TESTING_GUIDE.md` for comprehensive testing guide
- See `YOUR_TECH_STACK_SUMMARY.md` for Angular + WPF quick reference

---

**The flickering was caused by Streamlit's file watcher detecting output files being written. The config file disables this watcher, solving the problem!** ✅
