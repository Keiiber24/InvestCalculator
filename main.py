from app import app
import os

if __name__ == "__main__":
    # Use production mode
    app.debug = False
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
