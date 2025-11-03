# Your Tech Stack: Angular + WPF ✅ READY TO TEST

## 🎉 Your Scanner is Fully Configured!

I've built **specialized scanners** for your exact tech stack:
- ✅ **Angular** (web application)
- ✅ **WPF** (hardware-based desktop application)
- ✅ **C#** (backend API)

---

## 🚀 Quick Start (Copy & Paste)

```bash
cd /home/user/workflow-tracker/scanner
streamlit run cli/streamlit_app.py
```

**Opens:** http://localhost:8501

---

## ⚙️ Scan Your Repository

### In the GUI:

**Repository Path:**
```
/path/to/your/angular-wpf-repository
```

**File Extensions:**
```
.cs,.ts,.html,.xaml
```

**Detection Options:**
- ✅ Check ALL boxes (especially "Data Transforms" for UI events)

**Click:** 🔍 Start Scan

---

## 📊 What You'll See

### Angular Web Application

**Detects:**
```html
<!-- Your Angular templates (.html) -->
<button (click)="handleClick()">Click Me</button>
<form (ngSubmit)="onSubmit($event)">...</form>
<input (change)="onSearch($event)">
```

```typescript
// Your Angular components (.ts)
export class MyComponent {
  constructor(private http: HttpClient) {}

  handleClick() {
    this.http.post('/api/endpoint', data).subscribe();
  }
}
```

**Creates:**
- 🟡 Yellow nodes: `Angular: Click`, `Angular: Submit`
- 🔵 Blue nodes: `Angular HTTP POST /api/endpoint`
- ➡️ Arrows connecting them: "Angular Event → HTTP Call"

---

### WPF Desktop Application

**Detects:**
```xml
<!-- Your WPF XAML (.xaml) -->
<Button Click="Button_Click">Start Process</Button>
<TextBox TextChanged="OnTextChanged" />
```

```csharp
// Your WPF code-behind (.xaml.cs)
private async void Button_Click(object sender, RoutedEventArgs e)
{
    var client = new HttpClient();
    var response = await client.GetAsync("http://api.example.com/data");
    // ...
}
```

**Creates:**
- 🟡 Yellow nodes: `WPF: Click`, `WPF: Change`
- 🔵 Blue nodes: `WPF HTTP GET http://api.example.com/data`
- ➡️ Arrows connecting them: "WPF Event → HTTP Call"

---

### C# Backend

**Detects (from your existing C# scanner):**
- 🟢 Database READ operations (Entity Framework queries)
- 🟠 Database WRITE operations (SaveChanges, Add, Update)
- 🔵 API endpoints (`[HttpPost]`, `[HttpGet]`)
- File I/O operations

---

## 🎯 Example: Cross-Platform Workflow

### Scenario: Web App Controls Hardware via Desktop App

**Angular Frontend:**
```typescript
// User clicks in web app
sendHardwareCommand() {
  this.http.post('/api/hardware/command', { action: 'START' })
    .subscribe();
}
```

**C# Backend API:**
```csharp
[HttpPost("/api/hardware/command")]
public async Task<IActionResult> Command([FromBody] CommandDto cmd)
{
    _context.Commands.Add(new Command { Action = cmd.Action });
    await _context.SaveChangesAsync();
    return Ok();
}
```

**WPF Desktop App:**
```csharp
private async void PollCommands_Click(object sender, RoutedEventArgs e)
{
    var client = new HttpClient();
    var response = await client.GetAsync("http://localhost:5000/api/hardware/commands");
    var commands = await response.Content.ReadAsAsync<List<Command>>();

    foreach (var cmd in commands) {
        ExecuteHardwareCommand(cmd);
    }
}
```

**Generated Diagram:**
```
Web Application:
[Angular: Click] → [Angular HTTP POST /api/hardware/command]
                       ↓
Backend:
                  [C# API Controller]
                       ↓
                  [DB Write: Commands table]

Desktop Application:
[WPF: Click] → [WPF HTTP GET /api/hardware/commands]
                   ↓
              [DB Read: Commands table]
```

---

## 🎨 Node Colors in Your Diagrams

**Angular (Web):**
- 🟡 Yellow = UI events from templates
- 🔵 Blue = HTTP calls from components

**WPF (Desktop):**
- 🟡 Yellow = UI events from XAML
- 🔵 Blue = HTTP calls from code-behind

**Backend (C#):**
- 🟢 Green = Database reads
- 🟠 Orange = Database writes
- 🔵 Blue = API endpoints

---

## 📋 What Gets Detected Automatically

### Angular Scanner Finds:

**Event Bindings (in .html):**
- `(click)="..."`
- `(submit)="..."` or `(ngSubmit)="..."`
- `(change)="..."`
- `(input)="..."`
- `(mousedown)="..."`
- `(keyup)="..."`

**HTTP Calls (in .ts):**
- `this.http.get<Type>('url')`
- `this.http.post<Type>('url', data)`
- `this.http.put<Type>('url', data)`
- `this.http.delete<Type>('url')`
- `this.http.patch<Type>('url', data)`

**Automatic Linking:**
- Matches `.html` templates to `.ts` components
- Follows `templateUrl:` references
- Detects component names from `@Component` decorator

---

### WPF Scanner Finds:

**XAML Events (in .xaml):**
- `Click="..."`
- `MouseDown="..."`
- `TextChanged="..."`
- `SelectionChanged="..."`
- `Loaded="..."`
- `KeyDown="..."`, `KeyUp="..."`

**Code-Behind (in .xaml.cs):**
- `private void EventHandler(object sender, EventArgs e)`
- `private async void EventHandler(...)`

**HTTP Calls:**
- `HttpClient.GetAsync("url")`
- `HttpClient.PostAsync("url", content)`
- `HttpClient.PutAsync/DeleteAsync`
- `WebClient` methods (legacy)

**Automatic Linking:**
- Matches `.xaml` files to `.xaml.cs` code-behind
- Connects XAML event names to C# method names
- Example: `Click="Button_Click"` → `void Button_Click(...)`

---

## ✅ Testing Checklist

After scanning your repository, verify:

### Angular Web App:
- [ ] Yellow nodes appear with "Angular:" prefix
- [ ] Blue nodes show "Angular HTTP GET/POST/..."
- [ ] Arrows connect Angular events to HTTP calls
- [ ] Component names detected (from @Component or class name)
- [ ] Routes detected (if you have RouterModule config)

### WPF Desktop App:
- [ ] Yellow nodes appear with "WPF:" prefix
- [ ] Blue nodes show "WPF HTTP GET/POST/..."
- [ ] Arrows connect WPF events to HTTP calls
- [ ] Window/Page names detected correctly
- [ ] XAML events linked to code-behind methods

### Backend (C#):
- [ ] Green nodes for database reads
- [ ] Orange nodes for database writes
- [ ] API controllers detected
- [ ] Table names identified

---

## 🔍 How to View Your Workflows

### Step 1: Scan Complete

After scan finishes, you'll see:
- **Files Scanned**: Total count
- **Workflow Nodes**: All operations detected
- **Connections**: Edges between operations

### Step 2: Go to Visualizations Tab

Click: **📊 Visualizations**

### Step 3: Filter Your View

**For Angular Web App:**
- **Filter By:** Module/Directory
- **Select Filter:** `src/app/components` or `src/app/pages`
- **Max Nodes:** 50
- **Click:** 🎨 Generate Diagram

**For WPF Desktop App:**
- **Filter By:** Module/Directory
- **Select Filter:** `Views`, `Windows`, or your WPF directory
- **Max Nodes:** 50
- **Click:** 🎨 Generate Diagram

**For Backend:**
- **Filter By:** Database Table
- **Select Filter:** Your table name (e.g., "Commands", "Orders")
- **Click:** 🎨 Generate Diagram

---

## 📥 Download Options

Once diagram is generated:

**Download buttons:**
- 📥 **Download Mermaid Code** (.mmd file)
  - Use in GitHub markdown, documentation, wikis
- 📥 **Download as Markdown** (.md file)
  - Complete markdown with embedded diagram

**Output files** (in `./output/` directory):
- `workflow_graph.json` - All data (machine-readable)
- `workflow_graph.html` - Interactive visualization
- `workflow_documentation.md` - Documentation

---

## 🐛 Troubleshooting Your Tech Stack

### "No Angular events detected"

**Check:**
- ✅ File extensions include `.html` (templates)
- ✅ File extensions include `.ts` (components)
- ✅ Using Angular syntax: `(click)="..."` not `onclick="..."`
- ✅ "Data Transforms" detection enabled

---

### "No WPF events detected"

**Check:**
- ✅ File extensions include `.xaml`
- ✅ XAML uses: `Click="MethodName"`
- ✅ Code-behind file exists (`.xaml.cs`)

---

### "Events not connected to HTTP calls"

**This is expected if:**
- HTTP call is >50 lines away (WPF) or >100 lines away (Angular)
- HTTP call is in a different file (service layer)
- Event handler calls another method that calls HTTP

**Workaround:**
- Both nodes will still appear in diagram
- They just won't be connected with an arrow
- Future: Cross-file tracing will fix this

---

## 📚 Complete Documentation

**For Your Stack:** `ANGULAR_WPF_TESTING.md` ← **READ THIS**
**Quick Reference:** `QUICK_TEST.md`
**General Guide:** `TESTING_GUIDE.md`
**Implementation Details:** `UI_WORKFLOW_IMPLEMENTATION_SUMMARY.md`

---

## 💡 What This Enables for Your Team

### Product Management
- See complete user flows across web and desktop
- Understand hardware control sequences
- No code reading required

### Customer Support
- Troubleshoot: "User clicked X, what happened?"
- Trace issues from web UI → backend → desktop app
- Visual training materials

### QA Testing
- Test all detected user workflows
- Ensure coverage of UI interactions
- Identify integration points between platforms

### Development
- Onboard new developers faster
- Document cross-platform architecture
- See all API dependencies
- Understand hardware command flows

### DevOps
- Identify all external API calls
- Plan network rules and firewalls
- Understand service dependencies

---

## 🎊 You're Ready to Test!

Your scanner now fully supports:
- ✅ Angular web application
- ✅ WPF desktop application
- ✅ C# backend APIs
- ✅ Database operations
- ✅ Complete workflow chains

### Start Testing Now:

```bash
cd /home/user/workflow-tracker/scanner
streamlit run cli/streamlit_app.py
```

**Configure:**
- Repository Path: Your Angular/WPF repo path
- File Extensions: `.cs,.ts,.html,.xaml`
- Detection: Enable all

**Then:**
- Start Scan
- Wait for completion
- Visualizations tab
- Filter by your directories
- Generate diagrams
- See your workflows! 🪅

---

**All scanners are ready and committed to your branch!**

Test with your real codebase and see complete UI workflows from both web and desktop applications visualized in beautiful interactive diagrams!

Questions or issues? Check `ANGULAR_WPF_TESTING.md` for detailed examples and troubleshooting.
