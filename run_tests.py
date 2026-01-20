import sys
import os
import pytest

# Add current directory to sys.path
sys.path.insert(0, os.getcwd())

print(f"Current working directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

# Run pytest
sys.exit(pytest.main(["tests/test_system_service.py"]))
