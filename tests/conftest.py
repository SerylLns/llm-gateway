import os
import tempfile

os.environ.setdefault("MASTER_KEY", "test-master-key")
os.environ.setdefault("GEMINI_API_KEYS", "test-gemini-key")
os.environ.setdefault("DB_PATH", os.path.join(tempfile.mkdtemp(), "gateway.db"))
