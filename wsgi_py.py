"""
WSGI configuration for PythonAnywhere deployment.
This file is used by PythonAnywhere to serve your FastAPI application.
"""

import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/mysite'  # Change 'yourusername' to your actual username
if path not in sys.path:
    sys.path.insert(0, path)

from main import app

# PythonAnywhere expects an 'application' variable
application = app
