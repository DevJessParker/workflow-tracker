# Angular + WPF Testing Guide

## Quick Start for Your Tech Stack

Your application uses:
- **Angular** (web application)
- **WPF** (hardware-based desktop application)

Both are now fully supported! 🎉

---

## 🚀 Launch the Scanner (3 Commands)

```bash
cd /home/user/workflow-tracker/scanner
pip install -r requirements.txt  # First time only
streamlit run cli/streamlit_app.py
```

**Browser opens at:** http://localhost:8501

---

## ⚙️ Configure Scan for Your Repo

### For Angular + WPF Repository

**Repository Path:**
```
/path/to/your/angular-wpf-repository
```

**File Extensions:**
```
.cs,.ts,.html,.xaml
```

**Why these extensions:**
- `.cs` = C# backend + WPF code-behind
- `.ts` = Angular TypeScript components
- `.html` = Angular templates
- `.xaml` = WPF UI definitions

**Detection Options:**
✅ Check ALL boxes

Click: **🔍 Start Scan**

---

## 📊 What Gets Detected

### Angular Web Application

#### UI Events Detected:
```html
<!-- Angular template (.html) -->
<button (click)="handleCheckout()">Checkout</button>
<form (ngSubmit)="onSubmit($event)">...</form>
<input (change)="onSearch($event)">
```

**Creates nodes:**
- 🟡 `Angular: Click`
- 🟡 `Angular: Submit`
- 🟡 `Angular: Change`

---

#### HTTP Calls Detected:
```typescript
// Angular component (.ts)
export class CheckoutComponent {
  constructor(private http: HttpClient) {}

  handleCheckout() {
    // This gets detected
    this.http.post('/api/orders', orderData)
      .subscribe(result => console.log(result));
  }
}
```

**Creates nodes:**
- 🔵 `Angular HTTP POST /api/orders`

**Complete workflow:**
```
[Angular: Click] → [Angular HTTP POST /api/orders]
```

---

### WPF Desktop Application

#### XAML UI Events Detected:
```xml
<!-- MainWindow.xaml -->
<Window x:Class="MyApp.MainWindow">
    <Button Click="Button_Click">Start Process</Button>
    <TextBox TextChanged="OnTextChanged" />
    <ListBox SelectionChanged="OnSelectionChanged" />
</Window>
```

**Creates nodes:**
- 🟡 `WPF: Click`
- 🟡 `WPF: Change`

---

#### Code-Behind Event Handlers:
```csharp
// MainWindow.xaml.cs
public partial class MainWindow : Window
{
    private async void Button_Click(object sender, RoutedEventArgs e)
    {
        // HTTP call detected
        using (var client = new HttpClient())
        {
            var response = await client.GetAsync("http://api.example.com/data");
            var content = await response.Content.ReadAsStringAsync();
        }
    }
}
```

**Creates nodes:**
- 🔵 `WPF HTTP GET http://api.example.com/data`

**Complete workflow:**
```
[WPF: Click] → [WPF HTTP GET /api/data]
```

---

## 🎨 Example Workflows

### Example 1: Angular Web Form Submission

**Angular Template:**
```html
<form (ngSubmit)="submitOrder()">
  <input [(ngModel)]="order.productId" />
  <button type="submit">Place Order</button>
</form>
```

**Angular Component:**
```typescript
export class OrderComponent {
  submitOrder() {
    this.http.post<Order>('/api/orders', this.order)
      .subscribe(result => {
        console.log('Order created:', result.id);
      });
  }
}
```

**Expected Diagram:**
```
[Angular: Submit] → [Angular HTTP POST /api/orders] → [DB Write: Orders]
  (template)           (component)                      (backend)
```

---

### Example 2: WPF Button Click with API Call

**WPF XAML:**
```xml
<Button Click="StartProcess_Click">Start Process</Button>
```

**WPF Code-Behind:**
```csharp
private async void StartProcess_Click(object sender, RoutedEventArgs e)
{
    var client = new HttpClient();
    var response = await client.PostAsync(
        "http://localhost:5000/api/process/start",
        new StringContent("{}")
    );

    var result = await response.Content.ReadAsStringAsync();
    MessageBox.Show($"Process started: {result}");
}
```

**Expected Diagram:**
```
[WPF: Click] → [WPF HTTP POST /api/process/start] → [Backend API]
  (XAML)          (code-behind)                        (C# controller)
```

---

### Example 3: Complete Cross-Platform Flow

**Angular Frontend:**
```typescript
// User clicks button in web app
<button (click)="triggerHardware()">Control Hardware</button>

triggerHardware() {
  this.http.post('/api/hardware/command', { action: 'start' })
    .subscribe();
}
```

**C# Backend API:**
```csharp
[HttpPost("/api/hardware/command")]
public async Task<IActionResult> SendHardwareCommand([FromBody] CommandDto cmd)
{
    // Store command in database
    _context.Commands.Add(new Command { Action = cmd.Action });
    await _context.SaveChangesAsync();

    // WPF desktop app polls this API or receives notification
    return Ok();
}
```

**WPF Desktop App:**
```csharp
private async void CheckForCommands_Click(object sender, RoutedEventArgs e)
{
    var client = new HttpClient();
    var response = await client.GetAsync("http://localhost:5000/api/hardware/commands");
    var commands = await response.Content.ReadAsAsync<List<Command>>();

    // Execute hardware commands
    foreach (var cmd in commands)
    {
        ExecuteHardwareCommand(cmd);
    }
}
```

**Expected Complete Diagram:**
```
Web App Flow:
[Angular: Click] → [Angular HTTP POST /api/hardware/command]
                       ↓
Backend:              [C# API Controller]
                       ↓
                      [DB Write: Commands]

Desktop App Flow:
[WPF: Click] → [WPF HTTP GET /api/hardware/commands]
                   ↓
                  [DB Read: Commands]
```

---

## 🔍 Viewing Results in the GUI

### Visualizations Tab

After scan completes, go to **📊 Visualizations** tab:

#### For Angular Web App:

**Filter By:** `Module/Directory`
**Select Filter:** Your Angular directory
- `src/app/components`
- `src/app/pages`
- `src/app/services`

**Click:** 🎨 Generate Diagram

**Look for:**
- 🟡 Yellow nodes labeled `Angular: Click`, `Angular: Submit`
- 🔵 Blue nodes labeled `Angular HTTP GET/POST`
- Arrows connecting them

---

#### For WPF Desktop App:

**Filter By:** `Module/Directory`
**Select Filter:** Your WPF directory
- `Views`
- `Windows`
- `Controls`

**Click:** 🎨 Generate Diagram

**Look for:**
- 🟡 Yellow nodes labeled `WPF: Click`, `WPF: Change`
- 🔵 Blue nodes labeled `WPF HTTP GET/POST`
- Arrows connecting XAML events to code-behind calls

---

## 📝 Node Colors Quick Reference

**For Your Applications:**

### Angular Web App:
- 🟡 **Yellow** = Angular events `(click)`, `(ngSubmit)`, `(change)`
- 🔵 **Blue** = Angular HTTP calls `this.http.get/post()`
- 🟢 **Green** = Backend database READ
- 🟠 **Orange** = Backend database WRITE

### WPF Desktop App:
- 🟡 **Yellow** = WPF events `Click="..."`, `TextChanged="..."`
- 🔵 **Blue** = WPF HTTP calls `HttpClient.GetAsync/PostAsync`
- 🟢 **Green** = Backend database READ
- 🟠 **Orange** = Backend database WRITE

---

## 🎯 Angular-Specific Detection

### What Angular Scanner Detects:

**Event Bindings (in .html templates):**
- `(click)="methodName()"`
- `(submit)="methodName()"`
- `(ngSubmit)="methodName()"`
- `(change)="methodName()"`
- `(input)="methodName()"`
- `(mousedown)="methodName()"`
- `(keyup)="methodName()"`

**HTTP Calls (in .ts components):**
- `this.http.get<Type>('url')`
- `this.http.post<Type>('url', data)`
- `this.http.put<Type>('url', data)`
- `this.http.delete<Type>('url')`
- `this.http.patch<Type>('url', data)`

**Component Detection:**
- `@Component({ selector: 'app-name' })`
- `export class MyComponent`

**Route Detection:**
- `{ path: '/checkout', component: CheckoutComponent }`
- `this.router.navigate(['/path'])`

---

### Angular Template + Component Linking

The scanner automatically links:

**Template file:** `checkout.component.html`
```html
<button (click)="placeOrder()">Place Order</button>
```

**Component file:** `checkout.component.ts`
```typescript
export class CheckoutComponent {
  placeOrder() {
    this.http.post('/api/orders', this.order).subscribe();
  }
}
```

**Result:** Detects both and creates workflow chain!

---

## 🎯 WPF-Specific Detection

### What WPF Scanner Detects:

**XAML Event Handlers (in .xaml files):**
- `Click="Button_Click"`
- `MouseDown="OnMouseDown"`
- `SelectionChanged="OnSelectionChanged"`
- `TextChanged="OnTextChanged"`
- `Loaded="Window_Loaded"`
- `KeyDown="OnKeyDown"`

**Code-Behind Event Methods (in .xaml.cs files):**
- `private void Button_Click(object sender, RoutedEventArgs e)`
- `private async void Button_Click(object sender, RoutedEventArgs e)`

**HTTP Calls (in .xaml.cs code-behind):**
- `new HttpClient()`
- `client.GetAsync("url")`
- `client.PostAsync("url", content)`
- `client.PutAsync("url", content)`
- `client.DeleteAsync("url")`
- `new WebClient()` (legacy)
- `webClient.DownloadString("url")`

**Window/Page Detection:**
- `<Window x:Class="MyApp.MainWindow">`
- `<Page x:Class="MyApp.HomePage">`
- `public partial class MainWindow : Window`

---

### WPF XAML + Code-Behind Linking

The scanner automatically links:

**XAML file:** `MainWindow.xaml`
```xml
<Button Click="LoadData_Click">Load Data</Button>
```

**Code-behind:** `MainWindow.xaml.cs`
```csharp
private async void LoadData_Click(object sender, RoutedEventArgs e)
{
    var client = new HttpClient();
    var data = await client.GetAsync("http://api.example.com/data");
    // ...
}
```

**Result:** Creates connected workflow from XAML event to HTTP call!

---

## 🐛 Troubleshooting

### Angular Issues

**Q: No Angular events detected?**

**Check:**
- ✅ File extensions include `.html` (for templates)
- ✅ File extensions include `.ts` (for components)
- ✅ Templates use Angular event binding syntax: `(click)="..."` not `onclick="..."`
- ✅ "Data Transforms" detection enabled

**Test with minimal example:**
```html
<!-- test.component.html -->
<button (click)="test()">Test</button>
```
```typescript
// test.component.ts
export class TestComponent {
  test() { console.log('clicked'); }
}
```

---

**Q: No Angular HTTP calls detected?**

**Check:**
- ✅ Using Angular HttpClient: `this.http.get/post()`
- ✅ Not using `fetch()` or `axios` (those are detected by TypeScript scanner, not Angular scanner)
- ✅ File is `.ts` component file

**Example that WILL be detected:**
```typescript
constructor(private http: HttpClient) {}

loadData() {
  this.http.get<User[]>('/api/users').subscribe();
}
```

**Example that WON'T be detected by Angular scanner:**
```typescript
loadData() {
  fetch('/api/users');  // Detected by TypeScript scanner instead
}
```

---

### WPF Issues

**Q: No WPF events detected?**

**Check:**
- ✅ File extensions include `.xaml`
- ✅ XAML uses proper event syntax: `Click="Button_Click"`
- ✅ Event handler name matches code-behind method

**Test with minimal example:**
```xml
<!-- MainWindow.xaml -->
<Button Click="Test_Click">Test</Button>
```

---

**Q: Events and HTTP calls not connected?**

**Check:**
- ✅ `.xaml` and `.xaml.cs` files have same base name
- ✅ HTTP call is within 50 lines of event handler method
- ✅ Event handler method signature is correct:
  ```csharp
  private void MethodName(object sender, RoutedEventArgs e)
  ```

---

### File Extension Issues

**Q: Some files not being scanned?**

Make sure you include all relevant extensions:

**For Angular + WPF + Backend:**
```
.cs,.ts,.html,.xaml
```

**Optionally add:**
```
.cs,.ts,.html,.xaml,.cshtml,.razor
```
(if you use Razor views too)

---

## 📦 Example Scan Configuration

### For Your Mixed Angular/WPF Repository

**Repository Path:**
```
C:\Projects\MyHardwareApp
```
or
```
/home/user/projects/my-hardware-app
```

**File Extensions:**
```
.cs,.ts,.html,.xaml
```

**Detection Options:**
- ✅ Database Operations
- ✅ API Calls
- ✅ File I/O
- ✅ Message Queues
- ✅ Data Transforms ← **IMPORTANT for UI events**

**Expected Results:**

**Web App (Angular):**
- 🟡 Angular UI triggers from `.html` templates
- 🔵 Angular HTTP calls from `.ts` components
- Workflow chains connecting them

**Desktop App (WPF):**
- 🟡 WPF UI triggers from `.xaml` files
- 🔵 WPF HTTP calls from `.xaml.cs` code-behind
- Workflow chains connecting them

**Backend (C#):**
- 🟢 Database READ operations
- 🟠 Database WRITE operations
- 🔵 API endpoints
- File I/O if detected

---

## ✅ Success Checklist

After scanning your repository, you should see:

### Angular Web App:
- [ ] Yellow nodes: `Angular: Click`, `Angular: Submit`, etc.
- [ ] Blue nodes: `Angular HTTP GET/POST/PUT/DELETE`
- [ ] Arrows labeled: "Angular Event → HTTP Call"
- [ ] Component names detected correctly
- [ ] Routes/URLs associated with components

### WPF Desktop App:
- [ ] Yellow nodes: `WPF: Click`, `WPF: Change`, etc.
- [ ] Blue nodes: `WPF HTTP GET/POST/PUT/DELETE`
- [ ] Arrows labeled: "WPF Event → HTTP Call"
- [ ] Window/Page names detected correctly
- [ ] XAML events linked to code-behind

### Backend (C#):
- [ ] Green/Orange nodes: Database operations
- [ ] API endpoints detected
- [ ] Tables identified

---

## 🎉 What This Enables

### For Your Team:

**Product Managers:**
- See complete user journeys (web AND desktop)
- Understand hardware control flows
- No code reading required

**Customer Support:**
- Troubleshoot: "User clicked X in web app, what happens?"
- Trace: "Desktop app sent command, where does it go?"
- Visual diagrams for training

**QA Testing:**
- Test all detected workflows
- Ensure coverage of all UI interactions
- Identify untested paths

**Developers:**
- Onboard faster (see both Angular and WPF flows)
- Understand cross-platform interactions
- Document architecture automatically

**DevOps:**
- See all external API dependencies
- Identify network calls for firewall rules
- Plan infrastructure needs

---

## 🔮 Next Features Coming

**Priority 1: Backend Route Matching**
- Connect Angular `POST /api/orders` to C# `[HttpPost("/api/orders")]`
- Show complete end-to-end: Angular → C# API → Database

**Priority 2: Cross-Application Flows**
- Visualize: Web App → Backend → Desktop App
- Show shared database access
- Highlight integration points

**Priority 3: Hardware Command Tracing**
- Track hardware commands from web UI to desktop executor
- Visualize command queues
- Show device communication patterns

---

## 📚 Additional Resources

**For React (if you have any):** See `TESTING_GUIDE.md`
**For General Testing:** See `QUICK_TEST.md`
**For Implementation Details:** See `UI_WORKFLOW_IMPLEMENTATION_SUMMARY.md`

---

## 🚀 Ready to Test!

```bash
# 1. Launch
cd /home/user/workflow-tracker/scanner
streamlit run cli/streamlit_app.py

# 2. Configure
Repository Path: /path/to/your/angular-wpf-app
File Extensions: .cs,.ts,.html,.xaml
Detection: Enable all

# 3. Scan
Click: Start Scan
Wait for completion

# 4. Visualize
Tab: Visualizations
Filter: Module/Directory
Select: src/app (Angular) or Views (WPF)
Click: Generate Diagram

# 5. Enjoy!
See your Angular and WPF workflows visualized! 🪅
```

---

**Your scanner now fully supports both Angular web and WPF desktop applications!**

Test it on your codebase and see complete UI workflows from both platforms! 🎊
