import sys
import os

# Add backend/ to sy.path so 'import core' works on CI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))