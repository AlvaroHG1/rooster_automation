"""
Root entry point for Rooster Automation.
Redirects to the actual application entry point in app/main.py.
"""

import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main()
