#!/usr/bin/env python3
"""
Test runner utility for The Interview Agent.
Runs all backend tests and outputs a formatted status dashboard.
"""
import sys
import unittest
import time

def run_all_tests():
    print("====================================================")
    print("    THE INTERVIEW AGENT - TEST VALIDATION SUITE    ")
    print("====================================================")
    print("Initializing test discovery...")
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    print("\n====================================================")
    print("                 TEST RUN SUMMARY                   ")
    print("====================================================")
    print(f"Duration:     {duration:.3f} seconds")
    print(f"Tests Run:    {result.testsRun}")
    print(f"Passed:       {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:     {len(result.failures)}")
    print(f"Errors:       {len(result.errors)}")
    print("----------------------------------------------------")
    
    if result.wasSuccessful():
        print("  BUILD STATUS: SUCCESS (GREEN)")
        print("  Ready for submission to Stage 1 Verification!")
        print("====================================================")
        sys.exit(0)
    else:
        print("  BUILD STATUS: FAILED (RED)")
        print("  Please fix errors before submitting.")
        print("====================================================")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
