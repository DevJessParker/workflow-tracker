#!/usr/bin/env python3
"""
Diagnostic tool to check what files would be scanned.
Run this to verify your exclusions are working properly.

Usage:
    python tools/check_scan_stats.py /path/to/your/repo
"""
import os
import sys
import fnmatch
from pathlib import Path
from collections import Counter

def analyze_repository(repo_path, exclude_dirs, exclude_patterns, extensions):
    """Analyze what files would be scanned."""
    exclude_dirs_set = set(exclude_dirs)

    stats = {
        'total_files': 0,
        'would_scan': 0,
        'by_extension': Counter(),
        'excluded_dirs': Counter(),
        'excluded_patterns': Counter(),
        'largest_dirs': Counter()
    }

    files_to_scan = []

    print(f"Analyzing repository: {repo_path}")
    print("This may take a minute for large repos...\n")

    for root, dirs, files in os.walk(repo_path):
        # Count files in this directory
        stats['total_files'] += len(files)

        # Track large directories
        if len(files) > 100:
            rel_path = os.path.relpath(root, repo_path)
            stats['largest_dirs'][rel_path] = len(files)

        # Check which directories would be excluded
        excluded = []
        for d in dirs[:]:
            if d in exclude_dirs_set or d.startswith('.'):
                excluded.append(d)
                stats['excluded_dirs'][d] += 1

        # Remove excluded directories (prevents os.walk from descending)
        dirs[:] = [d for d in dirs if d not in excluded]

        # Check files
        for filename in files:
            # Count by extension
            ext = os.path.splitext(filename)[1]
            stats['by_extension'][ext] += 1

            # Check exclude patterns
            excluded_by_pattern = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    stats['excluded_patterns'][pattern] += 1
                    excluded_by_pattern = True
                    break

            if excluded_by_pattern:
                continue

            # Check if matches target extension
            if any(filename.endswith(e) for e in extensions):
                stats['would_scan'] += 1
                files_to_scan.append(os.path.join(root, filename))

    return stats, files_to_scan


def main():
    # Get repo path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.exists(repo_path):
        print(f"Error: Repository path not found: {repo_path}")
        sys.exit(1)

    # Default configuration (should match config.example.yaml)
    exclude_dirs = [
        "node_modules", "packages", "vendor", "bower_components",
        "bin", "obj", "dist", "build", "out", "target", ".next", ".nuxt",
        ".git", ".svn", ".hg",
        ".vs", ".vscode", ".idea", ".eclipse",
        "coverage", "TestResults", ".nyc_output",
        "tmp", "temp", ".cache", ".sass-cache",
        "docs/_build", "site", ".docker"
    ]

    exclude_patterns = [
        "*.min.js", "*.bundle.js", "*.min.css", "*.map",
        "*.designer.cs", "*.g.cs", "*.generated.cs"
    ]

    extensions = [".cs", ".ts", ".js", ".sql"]

    # Analyze repository
    stats, files_to_scan = analyze_repository(repo_path, exclude_dirs, exclude_patterns, extensions)

    # Print results
    print("="*70)
    print("SCAN ANALYSIS RESULTS")
    print("="*70)
    print(f"\nTotal files in repository: {stats['total_files']:,}")
    print(f"Files that WOULD be scanned: {stats['would_scan']:,}")
    print(f"Reduction: {(1 - stats['would_scan']/stats['total_files'])*100:.1f}%")

    # Estimated scan time
    files_per_second = 14  # Conservative estimate
    estimated_minutes = stats['would_scan'] / files_per_second / 60
    print(f"\nEstimated scan time: ~{estimated_minutes:.1f} minutes (at ~{files_per_second} files/sec)")

    # Top excluded directories
    print("\n" + "="*70)
    print("TOP EXCLUDED DIRECTORIES")
    print("="*70)
    for dirname, count in stats['excluded_dirs'].most_common(10):
        print(f"  {dirname}: {count:,} occurrences")

    # Files excluded by pattern
    if stats['excluded_patterns']:
        print("\n" + "="*70)
        print("FILES EXCLUDED BY PATTERN")
        print("="*70)
        for pattern, count in stats['excluded_patterns'].most_common(10):
            print(f"  {pattern}: {count:,} files")

    # File extensions found
    print("\n" + "="*70)
    print("FILE EXTENSIONS IN REPO (Top 20)")
    print("="*70)
    for ext, count in stats['by_extension'].most_common(20):
        ext_display = ext if ext else "(no extension)"
        will_scan = ext in extensions
        marker = "✓ WILL SCAN" if will_scan else ""
        print(f"  {ext_display:20s} {count:6,} files  {marker}")

    # Largest directories
    print("\n" + "="*70)
    print("LARGEST DIRECTORIES (>100 files)")
    print("="*70)
    for dirname, count in stats['largest_dirs'].most_common(10):
        print(f"  {dirname}: {count:,} files")

    # Warnings
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)

    if stats['would_scan'] > 15000:
        print("⚠️  WARNING: You would scan more than 15,000 files!")
        print("   This will take a LONG time. Consider adding more exclusions.")

    if 'node_modules' in stats['excluded_dirs']:
        print("✓ node_modules is being excluded (good!)")
    else:
        print("⚠️  WARNING: node_modules doesn't appear to be excluded")
        print("   Check that your config includes 'node_modules' in exclude_dirs")

    if stats['excluded_dirs'].get('bin', 0) > 0 or stats['excluded_dirs'].get('obj', 0) > 0:
        print("✓ C# build directories (bin/obj) are being excluded (good!)")

    # Check for common problem directories
    problem_dirs = []
    for dirname in ['node_modules', 'packages', 'bin', 'obj', 'dist', 'build']:
        if dirname in stats['largest_dirs']:
            problem_dirs.append(dirname)

    if problem_dirs:
        print(f"\n⚠️  WARNING: These directories should be excluded but appear in 'largest':")
        for dirname in problem_dirs:
            print(f"   - {dirname}")
        print("\n   Make sure your config/local.yaml includes these in exclude_dirs!")

    # Sample of files that would be scanned
    if files_to_scan:
        print("\n" + "="*70)
        print("SAMPLE FILES THAT WOULD BE SCANNED (first 20)")
        print("="*70)
        for f in files_to_scan[:20]:
            rel_path = os.path.relpath(f, repo_path)
            print(f"  {rel_path}")

        if len(files_to_scan) > 20:
            print(f"\n  ... and {len(files_to_scan) - 20:,} more files")

    print("\n" + "="*70)
    print()


if __name__ == '__main__':
    main()
