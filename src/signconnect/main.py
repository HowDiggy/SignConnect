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