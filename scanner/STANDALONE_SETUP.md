# Running Scanner Standalone (Without Docker)

The scanner can run independently without Docker for quick local testing.

## Installation

```bash
# Navigate to the workflow-tracker directory (parent of scanner)
cd /home/user/workflow-tracker

# Install dependencies
pip install -r scanner/requirements.txt
```

## Running the GUI

**IMPORTANT:** Run from the `workflow-tracker` directory (parent), not from inside `scanner/`:

```bash
# Make sure you're in workflow-tracker directory
cd /home/user/workflow-tracker

# Run Streamlit using Python module syntax
python -m streamlit run scanner/cli/streamlit_app.py
```

**Open:** http://localhost:8501

## Why Run from Parent Directory?

The scanner code uses relative imports like `from ..models import ...`. These imports require:
1. The `scanner` directory to be treated as a Python package
2. Running from the parent directory so Python can resolve `scanner.graph.builder` correctly

If you run from inside `scanner/`, you'll get: `attempted relative import beyond top-level package`

## Alternative: Direct Python Execution

```bash
cd /home/user/workflow-tracker
export PYTHONPATH=/home/user/workflow-tracker:$PYTHONPATH
python -m streamlit run scanner/cli/streamlit_app.py
```

## Testing Your Angular + WPF Repository

Once the GUI loads at http://localhost:8501:

1. **Repository Path:** Enter your Angular/WPF repo path (e.g., `/path/to/your/project`)
2. **File Extensions:** `.cs,.ts,.html,.xaml`
3. **Detection Options:** ✅ Check all boxes (especially "Data Transforms" for UI events)
4. **Click:** 🔍 Start Scan

### Expected Output

You'll see workflows like:
- 🟡 **Angular UI Events** `(click)="handler()"`
- 🟡 **WPF Click Events** `Click="Button_Click"`
- 🔵 **HTTP GET/POST** `this.http.get()` or `HttpClient.GetAsync()`
- 🟢 **Database READ** Entity Framework queries
- 🟠 **Database WRITE** SaveChanges operations

### Visualization

Go to **📊 Visualizations** tab:
1. **Filter By:** Module/Directory
2. **Select:** Your components directory (e.g., `src/app/components`)
3. **Max Nodes:** 50
4. **Click:** 🎨 Generate Diagram

You'll see complete user workflows:
```
[UI: Click] → [HTTP POST /api/save] → [DB Read: Users] → [DB Write: Audit]
```

## Troubleshooting

### Error: "No module named 'src.config_loader'"
- **Cause:** Running from wrong directory
- **Fix:** Run from `/home/user/workflow-tracker`, not `/home/user/workflow-tracker/scanner`

### Error: "attempted relative import beyond top-level package"
- **Cause:** Running from inside scanner directory
- **Fix:** `cd /home/user/workflow-tracker` then run command above

### Error: "streamlit: command not found"
- **Cause:** Dependencies not installed
- **Fix:** `pip install -r scanner/requirements.txt`

## What Gets Scanned

The scanner detects:

### Angular (TypeScript + HTML)
- Event bindings: `(click)="..."`, `(ngSubmit)="..."`, `(change)="..."`
- HTTP calls: `this.http.get()`, `this.http.post()`, `this.http.put()`, `this.http.delete()`
- Automatically links `.html` templates to `.ts` components

### WPF (C# + XAML)
- XAML events: `Click="..."`, `TextChanged="..."`, `Loaded="..."`
- C# handlers: `private void Button_Click(...)`, `async void OnLoad(...)`
- HTTP calls: `HttpClient.GetAsync()`, `HttpClient.PostAsync()`
- Automatically links `.xaml` files to `.xaml.cs` code-behind

### C# Backend
- Database reads: `context.Users.Where(...)`, `FirstOrDefault()`, `ToList()`
- Database writes: `context.Add(...)`, `context.Update(...)`, `SaveChanges()`
- API endpoints: `[HttpGet]`, `[HttpPost]`, `[Route]` attributes

## Output Files

After scanning, check `outputs/` directory:
- `workflow_graph.json` - Raw workflow data
- `workflow_diagram.md` - Mermaid diagram (paste into GitHub/Notion)
- `workflow_graph.html` - Interactive visualization

## See Also

- `ANGULAR_WPF_TESTING.md` - Tech stack specific examples
- `YOUR_TECH_STACK_SUMMARY.md` - Quick reference for Angular + WPF
- `TESTING_GUIDE.md` - Comprehensive testing guide
