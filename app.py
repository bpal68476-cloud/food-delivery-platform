
import os
from flask import Flask
from routes.auth import auth_bp
from routes.restaurant import restaurant_bp

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

app.register_blueprint(auth_bp)
app.register_blueprint(restaurant_bp)

if __name__ == "__main__":
    app.run(debug=True)
