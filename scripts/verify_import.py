
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import lifespan
    print("Successfully imported lifespan from main.py")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
