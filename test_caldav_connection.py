"""
Diagnostic script to test iCloud CalDAV connection.
This helps identify the root cause of connection issues.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_caldav_connection():
    """Test CalDAV connection with detailed diagnostics."""
    
    print("=" * 60)
    print("iCloud CalDAV Connection Diagnostic Tool")
    print("=" * 60)
    
    # Get credentials from environment
    caldav_url = os.getenv('CALDAV_URL')
    caldav_username = os.getenv('CALDAV_USERNAME')
    caldav_password = os.getenv('CALDAV_PASSWORD')
    
    print(f"\n1. Configuration Check:")
    print(f"   CalDAV URL: {caldav_url}")
    print(f"   Username: {caldav_username}")
    print(f"   Password: {'*' * len(caldav_password) if caldav_password else 'NOT SET'}")
    
    if not all([caldav_url, caldav_username, caldav_password]):
        print("\n❌ ERROR: Missing CalDAV credentials in .env file")
        return False
    
    # Test 1: Basic URL connectivity
    print(f"\n2. Testing URL connectivity...")
    try:
        import requests
        response = requests.get(caldav_url, timeout=10)
        print(f"   ✓ URL is reachable (Status: {response.status_code})")
    except Exception as e:
        print(f"   ✗ URL connectivity failed: {e}")
        return False
    
    # Test 2: CalDAV client connection
    print(f"\n3. Testing CalDAV client connection...")
    try:
        import caldav
        
        print(f"   Creating DAVClient...")
        client = caldav.DAVClient(
            url=caldav_url,
            username=caldav_username,
            password=caldav_password
        )
        print(f"   ✓ DAVClient created")
        
        print(f"   Attempting to get principal...")
        principal = client.principal()
        print(f"   ✓ Principal obtained successfully!")
        
        # Test 3: List calendars
        print(f"\n4. Listing available calendars...")
        calendars = principal.calendars()
        
        if calendars:
            print(f"   ✓ Found {len(calendars)} calendar(s):")
            for cal in calendars:
                print(f"      - {cal.name}")
        else:
            print(f"   ⚠ No calendars found")
        
        print(f"\n✅ SUCCESS: CalDAV connection is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ CalDAV connection FAILED:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        # Provide specific guidance based on error
        if "10054" in str(e) or "forcibly closed" in str(e):
            print(f"\n💡 Troubleshooting suggestions:")
            print(f"   1. Verify your app-specific password is correct and current")
            print(f"   2. Check if your CalDAV URL needs your iCloud user ID")
            print(f"      Format: https://caldav.icloud.com/<USER_ID>/calendars/")
            print(f"   3. Try generating a new app-specific password at:")
            print(f"      https://appleid.apple.com/account/manage")
            print(f"   4. Check if firewall/antivirus is blocking the connection")
            print(f"   5. Verify two-factor authentication is enabled on your Apple ID")
        
        return False

if __name__ == "__main__":
    success = test_caldav_connection()
    sys.exit(0 if success else 1)
