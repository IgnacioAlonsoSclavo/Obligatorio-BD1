import os
from app import app

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(debug=True, host=host, port=puerto)
