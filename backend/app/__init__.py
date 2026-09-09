import os
import sys

# Ensure repository root (c:\SanTrapik) is in sys.path so 'backend' package is always resolvable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
