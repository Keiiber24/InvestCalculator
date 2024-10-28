from flask import Flask, render_template, request, jsonify
from flask_login import login_required, current_user
import os
import logging
from models import db, login_manager, User
from financial_calculator import TradeCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev_key_only_for_development"),
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "investment.db")}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Ensure instance path exists
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    with app.app_context():
        from routes.auth import auth
        app.register_blueprint(auth, url_prefix='/auth')

        # Create all tables
        db.create_all()

        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return render_template('errors/500.html'), 500

        # User loader for Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            try:
                return User.query.get(int(user_id))
            except Exception as e:
                logger.error(f"Error loading user: {str(e)}")
                return None

        # Routes
        @app.route('/')
        @login_required
        def index():
            try:
                return render_template('index.html', active_page='calculator')
            except Exception as e:
                logger.error(f"Error in index route: {str(e)}")
                return render_template('errors/500.html'), 500

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
