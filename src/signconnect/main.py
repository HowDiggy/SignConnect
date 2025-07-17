# src/signconnect/main.py

# Its only job is to call the factory to build the app.
from .app_factory import create_app

app = create_app()