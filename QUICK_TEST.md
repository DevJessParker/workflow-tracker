# Quick Test Reference Card

## 🚀 Launch in 3 Commands

```bash
cd /home/user/workflow-tracker/scanner
pip install -r requirements.txt  # First time only
streamlit run cli/streamlit_app.py
```

**Open:** http://localhost:8501

---

## ⚡ Test UI Workflows in 4 Steps

### 1. Configure Scan
- **Repository Path:** `/path/to/your/react-app`
- **File Extensions:** `.cs,.ts,.tsx,.jsx,.js`
- **Detection:** ✅ All checkboxes

### 2. Start Scan
Click: **🔍 Start Scan**

### 3. Wait for Completion
Watch the 🪅 pinata move across the rainbow progress bar

### 4. View Results
**Visualizations Tab** → Filter by Module → **🎨 Generate Diagram**

---

## 📊 What You'll See

### UI Workflow Nodes

```
🟡 [UI: Click]              ← UI trigger (yellow)
    ↓
🔵 [HTTP POST /api/orders]  ← API call (blue)
    ↓
🟢 [DB Read: Inventory]     ← Database (green/orange)
    ↓
🟠 [DB Write: Orders]
```

### Node Colors Quick Reference
- 🟡 Yellow = UI Events / Transforms
- 🔵 Blue = API Calls
- 🟢 Green = Database READ
- 🟠 Orange = Database WRITE
- 🟣 Purple = File I/O

---

## 🎯 Quick Test Cases

### Test Case 1: Button Click
```typescript
<button onClick={handleClick}>Click</button>
const handleClick = () => fetch('/api/data');
```
**Expected:** UI Click → HTTP GET (2 nodes, 1 edge)

### Test Case 2: Form Submit
```typescript
<form onSubmit={handleSubmit}>...</form>
const handleSubmit = () => axios.post('/api/submit', data);
```
**Expected:** UI Submit → HTTP POST (2 nodes, 1 edge)

---

## 🔍 Where to Look

### Scan Repository Tab
- **Files Scanned** = Total files processed
- **Workflow Nodes** = Total operations found
- **Connections** = Edges between nodes

### Visualizations Tab
1. Filter By: **Module/Directory**
2. Select: `src/components` or `src/pages`
3. Max Nodes: **50**
4. Click: **🎨 Generate Diagram**

### Database Schema Tab
- View all tables
- See operation counts
- Sample queries from code

### Data Analysis Tab
- Hot spots (busiest files)
- Workflow patterns
- Connected operations

---

## ⚠️ Troubleshooting

**No UI triggers?**
- ✅ Extensions include `.tsx` or `.jsx`
- ✅ Code has `onClick`, `onSubmit`, etc.
- ✅ "Data Transforms" detection enabled

**Scan too slow?**
- Scan specific directory instead of root
- Reduce file extensions (only `.tsx,.cs`)

**No diagram?**
- Select different filter
- Try "Module/Directory" filter
- Increase "Max Nodes" to 100

---

## 💾 Output Files

Check `./output/` directory:
- `workflow_graph.json` - All data
- `workflow_graph.html` - Interactive viz
- `workflow_documentation.md` - Docs

---

## 📖 Full Guide

See **TESTING_GUIDE.md** for complete documentation.

---

**That's it! Happy testing! 🪅**
