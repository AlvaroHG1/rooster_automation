"""
Test script for file_storage.py connection management.
Tests lazy initialization, auto-connect, and retry logic.
"""

import os
import sys
import time

# Import the module
from file_storage import CalDAVStorage

def test_lazy_initialization():
    """Test that CalDAVStorage initializes without making a connection."""
    print("=" * 60)
    print("Test 1: Lazy Initialization")
    print("=" * 60)
    
    start = time.time()
    storage = CalDAVStorage()
    duration = time.time() - start
    
    print(f"✓ Initialization completed in {duration:.3f} seconds")
    
    if duration < 1.0:
        print("✓ PASS: Initialization is instant (lazy connection)")
        return True
    else:
        print("✗ FAIL: Initialization took too long (eager connection)")
        return False

def test_auto_connect():
    """Test that connection is automatically made on first use."""
    print("\n" + "=" * 60)
    print("Test 2: Auto-Connect on First Use")
    print("=" * 60)
    
    storage = CalDAVStorage()
    print("Storage initialized (no connection yet)")
    
    # This should trigger auto-connect
    calendars = storage.list_calendars()
    
    if len(calendars) > 0:
        print(f"✓ PASS: Found {len(calendars)} calendars: {calendars}")
        return True
    else:
        print("✗ FAIL: No calendars found")
        return False

def test_connection_test_method():
    """Test the test_connection() method."""
    print("\n" + "=" * 60)
    print("Test 3: Connection Test Method")
    print("=" * 60)
    
    storage = CalDAVStorage()
    result = storage.test_connection()
    
    if result:
        print("✓ PASS: Connection test successful")
        return True
    else:
        print("✗ FAIL: Connection test failed")
        return False

def test_event_upload():
    """Test event upload with existing ICS file."""
    print("\n" + "=" * 60)
    print("Test 4: Event Upload")
    print("=" * 60)
    
    ics_file = "./temp_downloads/rooster_2026_week_04.ics"
    
    if not os.path.exists(ics_file):
        print(f"⚠ SKIP: Test file not found: {ics_file}")
        return None
    
    storage = CalDAVStorage()
    
    try:
        result = storage.save_ics_file(ics_file)
        print(f"✓ PASS: {result}")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_context_manager():
    """Test context manager support."""
    print("\n" + "=" * 60)
    print("Test 5: Context Manager Support")
    print("=" * 60)
    
    try:
        with CalDAVStorage() as storage:
            calendars = storage.list_calendars()
            print(f"Found {len(calendars)} calendars inside context")
        
        print("✓ PASS: Context manager works correctly")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "🧪 File Storage Connection Management Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Lazy Initialization", test_lazy_initialization()))
    results.append(("Auto-Connect", test_auto_connect()))
    results.append(("Connection Test", test_connection_test_method()))
    results.append(("Event Upload", test_event_upload()))
    results.append(("Context Manager", test_context_manager()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    
    for name, result in results:
        if result is True:
            print(f"✓ {name}: PASS")
        elif result is False:
            print(f"✗ {name}: FAIL")
        else:
            print(f"⚠ {name}: SKIP")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
