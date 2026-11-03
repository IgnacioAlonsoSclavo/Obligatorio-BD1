import os
from app import app

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="127.0.0.1", port=puerto)
