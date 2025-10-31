# Scan Optimization Guide

This guide helps you dramatically speed up repository scans by excluding unnecessary files and directories.

## 🎯 Quick Answer: What to Exclude

**YES - Exclude these (they contain no useful workflow information):**
- ✅ Package management directories (`node_modules`, `packages`, `vendor`)
- ✅ Build outputs (`bin`, `obj`, `dist`, `build`)
- ✅ Minified/bundled files (`*.min.js`, `*.bundle.js`)
- ✅ Auto-generated files (`*.designer.cs`, `*.g.cs`)
- ✅ IDE/editor directories (`.vs`, `.vscode`, `.idea`)
- ✅ Test coverage reports (`coverage`, `TestResults`)

**NO - Don't exclude these (they contain your application logic):**
- ❌ Your source code directories (`src`, `app`, `Services`, `Controllers`)
- ❌ Your TypeScript/JavaScript components
- ❌ Your C# application code
- ❌ Custom SQL files

## 📊 Performance Impact

### Example Repository Analysis

**Before Optimization:**
```
Repository: 145,000 files total
- node_modules: 120,000 files
- bin/obj: 15,000 files
- Your code: 10,000 files

Scan time: 2+ hours (scanning everything)
```

**After Optimization:**
```
Repository: 145,000 files total
Filtered: 135,000 files
Scanned: 10,000 files (your code only)

Scan time: 12 minutes ✓ (10x faster!)
```

## 🚀 Optimization Steps

### Step 1: Update Your Config

Edit `config/local.yaml` and add comprehensive exclusions:

```yaml
scanner:
  exclude_dirs:
    # Package managers (CRITICAL - excludes thousands of files!)
    - "node_modules"     # npm/yarn packages
    - "packages"         # NuGet packages
    - "vendor"           # Composer/Go packages

    # Build outputs (auto-generated, not source code)
    - "bin"
    - "obj"
    - "dist"
    - "build"
    - "out"
    - ".next"
    - ".nuxt"

    # IDE directories (settings, not code)
    - ".vs"
    - ".vscode"
    - ".idea"

    # Test coverage (reports, not code)
    - "coverage"
    - "TestResults"

    # Temporary/cache
    - "tmp"
    - "temp"
    - ".cache"

  exclude_patterns:
    - "*.min.js"         # Minified - no useful patterns
    - "*.bundle.js"      # Bundled - hard to read
    - "*.min.css"
    - "*.map"            # Source maps
    - "*.designer.cs"    # Auto-generated
    - "*.g.cs"           # Auto-generated
    - "*.generated.cs"   # Auto-generated
```

### Step 2: Verify Exclusions

After updating config, run a scan and check the first line:

```
🔍 Discovering files...
  Filtered: 135 directories, 245 files (minified/generated)
✓ Found 9,161 files to scan
```

**Good signs:**
- High filtered count means exclusions are working
- Found file count matches your actual source code

**Bad signs:**
- Filtered count is 0 (exclusions not working)
- Found count is suspiciously high (e.g., 150K files)

### Step 3: Focus on Source Directories (Advanced)

If you have a specific source directory structure, scan only that:

```yaml
repository:
  path: "/path/to/your/repo/src"  # Point to src directory only
```

Or scan specific directories separately:

```bash
# Backend only
workflow-tracker scan --repo /repo/Backend

# Frontend only
workflow-tracker scan --repo /repo/Frontend
```

## 💡 Understanding the Performance Killer: node_modules

### Why node_modules is So Bad

A typical Angular + C# project:

```
Your project structure:
├── Backend/                    (2,500 .cs files)
├── Frontend/
│   ├── src/                   (1,500 .ts files)
│   └── node_modules/          (120,000+ .js files!) ⚠️
└── Shared/                    (500 .cs files)

Total: 124,500 files
Your code: 4,500 files (3.6%)
Dependencies: 120,000 files (96.4%)
```

**What's in node_modules?**
- Third-party library code
- Already-bundled workflows (not your app's logic)
- Minified, obfuscated code
- Test files from dependencies
- **Not useful for documenting YOUR workflows**

**Performance impact:**
- **Without exclusion**: Scans 124,500 files → 2 hours
- **With exclusion**: Scans 4,500 files → 12 minutes
- **Speed improvement**: 10x faster!

## 📁 Comprehensive Exclusion List by Technology

### For C# / .NET Projects

```yaml
exclude_dirs:
  - "bin"              # Compiled output
  - "obj"              # Intermediate objects
  - "packages"         # NuGet packages
  - ".vs"              # Visual Studio settings
  - "TestResults"      # Test output
  - "artifacts"        # Build artifacts
  - "publish"          # Published output

exclude_patterns:
  - "*.designer.cs"    # Designer-generated
  - "*.g.cs"           # Generated code
  - "*.generated.cs"   # Generated code
  - "AssemblyInfo.cs"  # Assembly metadata
```

### For Angular / TypeScript Projects

```yaml
exclude_dirs:
  - "node_modules"     # NPM packages
  - "dist"             # Build output
  - ".angular"         # Angular cache
  - "coverage"         # Test coverage
  - ".next"            # Next.js build

exclude_patterns:
  - "*.min.js"         # Minified
  - "*.bundle.js"      # Bundled
  - "*.chunk.js"       # Webpack chunks
  - "*.spec.ts"        # Test files (optional)
  - "*.map"            # Source maps
```

### For Full-Stack Projects

Combine both lists above, plus:

```yaml
exclude_dirs:
  - "wwwroot/lib"      # Client-side packages
  - "ClientApp/node_modules"  # Nested node_modules
```

## 🔍 How to Audit Your Repository

### Check What Would Be Scanned

Before running a full scan, check file counts:

```powershell
# Windows PowerShell
# Total files
Get-ChildItem -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count

# By directory
Get-ChildItem -Directory | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -Recurse -File).Count
    "$($_.Name): $count files"
}
```

```bash
# Linux/Mac
# Total files
find . -type f | wc -l

# By directory
for dir in */; do
    echo "$dir: $(find $dir -type f | wc -l) files"
done
```

### Identify Large Directories

```powershell
# Find directories with most files
Get-ChildItem -Directory | ForEach-Object {
    [PSCustomObject]@{
        Directory = $_.Name
        Files = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
    }
} | Sort-Object Files -Descending | Format-Table
```

**Example output:**
```
Directory        Files
---------        -----
node_modules     87453
bin              12345
obj              8901
src              3456  ← This is what you want to scan!
```

## ⚡ Performance Tips

### 1. Exclude Test Files (Optional)

If you don't need to document test workflows:

```yaml
exclude_patterns:
  - "*.spec.ts"
  - "*.test.ts"
  - "*.spec.js"
  - "*Test.cs"
  - "*Tests.cs"
```

**Trade-off:**
- ✅ Faster scans
- ❌ Miss test-specific workflows (usually not important for production docs)

### 2. Limit File Extensions

Only scan the languages you use:

```yaml
include_extensions:
  - ".cs"      # Keep C# backend
  # - ".ts"    # Comment out if pure C# project
  # - ".js"    # Comment out if pure TypeScript
```

### 3. Disable Edge Inference for Very Large Repos

For repositories with 50K+ nodes:

```yaml
scanner:
  edge_inference:
    enabled: false  # Skip edge creation entirely
```

This saves ~10-20% time on very large scans.

### 4. Use Docker with More Memory

```powershell
docker run --rm -m 4g `
  -v /path/to/repo:/repo:ro `
  workflow-tracker scan --repo /repo
```

### 5. Scan in Parallel (Multiple Directories)

If you have multiple independent codebases:

```powershell
# Terminal 1 - Backend
docker run --name wt-backend workflow-tracker scan --repo /repo/Backend

# Terminal 2 - Frontend
docker run --name wt-frontend workflow-tracker scan --repo /repo/Frontend
```

## 📈 Expected Performance

| Repository Size | Files to Scan | Nodes Found | Scan Time |
|----------------|---------------|-------------|-----------|
| Small (1K files) | 1,000 | 3,500 | 2 min |
| Medium (5K files) | 5,000 | 18,000 | 6 min |
| Large (10K files) | 10,000 | 35,000 | 12 min |
| Very Large (25K files) | 25,000 | 80,000 | 30 min |

**If your scan is slower:**
- Check if exclusions are working (look for "Filtered:" message)
- Verify you're not scanning `node_modules` or `packages`
- Check for very large auto-generated files

## 🚨 Common Mistakes

### ❌ Mistake 1: Not Excluding node_modules

```yaml
# BAD - Scans everything
exclude_dirs:
  - ".git"

# GOOD - Excludes dependencies
exclude_dirs:
  - "node_modules"
  - "packages"
  - ".git"
```

### ❌ Mistake 2: Scanning Build Output

```yaml
# BAD - Scans compiled code
exclude_dirs: []

# GOOD - Excludes build artifacts
exclude_dirs:
  - "bin"
  - "obj"
  - "dist"
```

### ❌ Mistake 3: Including Minified Files

```yaml
# BAD - No pattern exclusions
exclude_patterns: []

# GOOD - Excludes minified/bundled
exclude_patterns:
  - "*.min.js"
  - "*.bundle.js"
```

## 🎯 Quick Optimization Checklist

Before running a scan, verify:

- [ ] `node_modules` is in `exclude_dirs`
- [ ] `packages` is in `exclude_dirs` (for C#)
- [ ] `bin` and `obj` are in `exclude_dirs` (for C#)
- [ ] `dist` and `build` are in `exclude_dirs`
- [ ] Minified files (`*.min.js`) are in `exclude_patterns`
- [ ] Auto-generated files (`*.designer.cs`) are in `exclude_patterns`
- [ ] Test coverage directories are excluded

## 💡 Pro Tips

### Use a Separate Config for Large Repos

Create `config/large-repo.yaml`:

```yaml
scanner:
  include_extensions:
    - ".cs"  # Only C# for faster scans

  exclude_dirs:
    # Maximum exclusions
    - "node_modules"
    - "packages"
    - "bin"
    - "obj"
    - "dist"
    # ... all others

  edge_inference:
    enabled: false  # Disable for speed
```

Run with:
```bash
workflow-tracker scan --config config/large-repo.yaml
```

### Monitor File Discovery

Watch the discovery phase:

```
🔍 Discovering files...
  Filtered: 135 directories, 245 files (minified/generated)
✓ Found 9,161 files to scan
```

If "Filtered" count is low, your exclusions aren't working!

## 📚 Summary

**Key takeaways:**
1. **Always exclude `node_modules` and `packages`** - This is the #1 performance killer
2. **Exclude build outputs** - They contain compiled/generated code, not source
3. **Exclude minified files** - They're unreadable and not useful
4. **Focus on source directories** - Only scan your application code
5. **Monitor the "Filtered" count** - It shows exclusions are working

**Expected improvement:**
- 🐌 **Without optimization**: 2 hours, 150K files scanned
- 🚀 **With optimization**: 12 minutes, 10K files scanned
- 💪 **Result**: 10x faster, same valuable workflow data!
