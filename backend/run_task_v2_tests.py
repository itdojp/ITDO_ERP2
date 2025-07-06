#!/usr/bin/env python3
"""Run all task management v2 tests to verify TDD Red phase."""

import subprocess
import sys

def run_tests(test_path, description):
    """Run tests and capture results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print('='*60)
    
    cmd = ["uv", "run", "pytest", test_path, "-v", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode

def main():
    """Run all test categories for task management v2."""
    test_categories = [
        ("tests/unit/task_management_v2/", "Unit Tests"),
        ("tests/integration/task_management_v2/", "Integration Tests"),
        ("tests/security/test_task_security.py", "Security Tests"),
    ]
    
    all_failed = True
    
    for test_path, description in test_categories:
        returncode = run_tests(test_path, description)
        if returncode == 0:
            all_failed = False
            print(f"WARNING: {description} passed - should be failing in TDD Red phase!")
    
    print("\n" + "="*60)
    print("TDD Red Phase Verification Summary")
    print("="*60)
    
    if all_failed:
        print("✅ All tests are failing as expected (NotImplementedError)")
        print("✅ Ready to proceed to TDD Green phase")
    else:
        print("❌ Some tests are passing - review implementation")
        print("❌ All tests should fail with NotImplementedError in Red phase")
    
    return 0 if all_failed else 1

if __name__ == "__main__":
    sys.exit(main())