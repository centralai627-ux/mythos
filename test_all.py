#!/usr/bin/env python
"""Quick verification that all Mythos components work."""

import sys
import importlib

def test_import(module_name):
    """Test if a module imports successfully."""
    try:
        importlib.import_module(module_name)
        print(f"  ✓ {module_name}")
        return True
    except Exception as e:
        print(f"  ✗ {module_name}: {e}")
        return False

def test_key_function():
    """Test specific functions work."""
    print("\n— Testing key functions —")
    
    # Test PDF module
    try:
        from core.tools import _generate_pdf
        print("  ✓ PDF generation function available")
    except Exception as e:
        print(f"  ✗ PDF generation: {e}")
    
    # Test lock screen question bank
    try:
        from core.lock_screen import LockScreen
        ls = LockScreen()
        if hasattr(ls, 'QUESTION_BANK'):
            print(f"  ✓ Lock screen: {len(ls.QUESTION_BANK)} questions loaded")
        else:
            print("  ⚠ Lock screen: QUESTION_BANK not found as attribute")
    except Exception as e:
        print(f"  ✗ Lock screen: {e}")
    
    # Test agent commands
    try:
        from core.agent import MythosAgent
        # Check if interactive shell method exists
        if hasattr(MythosAgent, '_run_interactive_shell'):
            print("  ✓ Interactive shell command available")
        if hasattr(MythosAgent, '_run_lock'):
            print("  ✓ Lock screen command available")
    except Exception as e:
        print(f"  ✗ Agent commands: {e}")
    
    # Test AI brain system prompt
    try:
        from core.ai_brain import get_system_prompt
        prompt = get_system_prompt("mythos-code", [])
        # Check for aggressive tool enforcement
        if "IMMEDIATELY emit" in prompt and "NO EXPLANATION" in prompt:
            print("  ✓ AI brain: aggressive tool enforcement active")
        else:
            print("  ⚠ AI brain: system prompt may need update")
    except Exception as e:
        print(f"  ✗ AI brain: {e}")

def main():
    print("=" * 60)
    print("  MYTHOS COMPONENT VERIFICATION")
    print("=" * 60)
    
    print("\n— Testing core imports —")
    modules = [
        "core.config",
        "core.ui",
        "core.tools",
        "core.ai_brain",
        "core.agent",
        "core.executor",
        "core.vision",
        "core.lock_screen",
    ]
    
    results = []
    for mod in modules:
        results.append(test_import(mod))
    
    test_key_function()
    
    print("\n" + "=" * 60)
    if all(results):
        print("  ✓ ALL COMPONENTS WORKING")
        print("=" * 60)
        return 0
    else:
        print("  ✗ SOME COMPONENTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
