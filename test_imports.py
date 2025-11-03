#!/usr/bin/env python3
"""Test script to verify scanner imports work correctly."""

import sys
import traceback
from pathlib import Path

print("=" * 60)
print("TESTING SCANNER IMPORTS")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Current directory: {Path.cwd()}")
print(f"Script location: {__file__}")
print(f"sys.path[0]: {sys.path[0]}")
print()

# Test importing scanner modules
print("Attempting to import scanner modules...")
print()

try:
    print("1. Importing Config...")
    from scanner.config_loader import Config
    print("   ✓ Config imported successfully")

    print("2. Importing models...")
    from scanner.models import WorkflowType, WorkflowNode, WorkflowGraph
    print("   ✓ Models imported successfully")

    print("3. Importing WorkflowGraphBuilder...")
    from scanner.graph.builder import WorkflowGraphBuilder
    print("   ✓ WorkflowGraphBuilder imported successfully")

    print("4. Importing WorkflowRenderer...")
    from scanner.graph.renderer import WorkflowRenderer
    print("   ✓ WorkflowRenderer imported successfully")

    print("5. Importing scanners...")
    from scanner.scanner import AngularScanner, WPFScanner, CSharpScanner
    print("   ✓ Scanners imported successfully")

    print()
    print("=" * 60)
    print("✓ ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)
    print()
    print("The scanner is properly configured.")
    print("You can now run: python -m streamlit run scanner/cli/streamlit_app.py")

except Exception as e:
    print()
    print("=" * 60)
    print("✗ IMPORT FAILED!")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print()
    print("=" * 60)
    print("TROUBLESHOOTING:")
    print("=" * 60)
    print("1. Make sure you're running from /home/user/workflow-tracker")
    print("2. Run: cd /home/user/workflow-tracker")
    print("3. Run: python test_imports.py")
    sys.exit(1)
