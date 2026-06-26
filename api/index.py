import os
import sys

# Add project root directory to sys.path to allow Vercel to resolve 'src' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.api import app
