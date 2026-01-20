import sys
import os
import pytest

# Add current directory to sys.path
sys.path.insert(0, os.getcwd())
# Add src directory to sys.path to allow direct imports like 'import api_client'
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

print(f"Current working directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

# Run pytest
sys.exit(pytest.main(["tests/"]))
