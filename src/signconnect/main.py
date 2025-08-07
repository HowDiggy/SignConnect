# src/signconnect/main.py

from .app_factory import create_app
from .core.config import get_settings

# Get the application settings
# This will load from your .env file or environment variables
settings = get_settings()

# Create the FastAPI application instance using the factory
# This is the main entry point for the production application
app = create_app(settings=settings)

# The 'app' variable is what Uvicorn will use to run the application.

# We no longer need the 'if __name__ == "__main__"' block,
# as Uvicorn handles running the server via the command line.

# how to run this:
# uvicorn signconnect.main:app --app-dir src --reload
"""
# src/signconnect/main.py

import uvicorn
from .app_factory import create_app

# This line is now inside the __main__ block, so it's safe from imports.
# app = create_app()

if __name__ == "__main__":
    # Create the app instance only when running the script directly
    app = create_app()

    # Run the Uvicorn server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )

# how to run this:
python -m src.signconnect.main
"""