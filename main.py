from flask import Flask
from views import main_bp
from auth import auth_bp
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    return app

app = create_app()

if __name__ == '__main__': 
    app.run(debug=True)