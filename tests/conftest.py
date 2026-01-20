import sys
from unittest.mock import MagicMock

# Mock streamlit before importing app modules
sys.modules["streamlit"] = MagicMock()
sys.modules["extra_streamlit_components"] = MagicMock()
sys.modules["OpenSSL"] = MagicMock()
sys.modules["OpenSSL.crypto"] = MagicMock()
sys.modules["bcrypt"] = MagicMock()
