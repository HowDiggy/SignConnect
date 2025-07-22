# src/signconnect/main.py

from .app_factory import create_app

# Create the app instance at the module level.
# Uvicorn will import this 'app' object when it starts.
app = create_app()

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