from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, db
import logging
from sqlalchemy.exc import SQLAlchemyError

# Configuración del logger
logger = logging.getLogger(__name__)

# Crear el Blueprint
auth = Blueprint('auth', __name__)

def validate_password(password):
    """Validar requisitos de contraseña"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta de login con manejo de errores mejorado"""
    # Redireccionar si el usuario ya está autenticado
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))

            # Validaciones básicas
            if not email or not password:
                flash('Please fill in all fields.', 'danger')
                return render_template('auth/login.html')

            user = User.query.filter_by(email=email.lower()).first()

            if not user or not user.check_password(password):
                flash('Invalid email or password. Please try again.', 'danger')
                logger.warning(f"Failed login attempt for email: {email}")
                return render_template('auth/login.html')

            # Login exitoso
            login_user(user, remember=remember)
            logger.info(f"Successful login for user: {user.username}")

            # Redireccionar a la página que el usuario intentaba acceder
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        db.session.rollback()

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta de registro con validaciones mejoradas"""
    # Redireccionar si el usuario ya está autenticado
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            # Validaciones de campos
            if not email or not username or not password:
                flash('Please fill in all fields.', 'danger')
                return render_template('auth/register.html')

            # Validar formato de email básico
            if '@' not in email or '.' not in email:
                flash('Please enter a valid email address.', 'danger')
                return render_template('auth/register.html')

            # Validar longitud del username
            if len(username) < 3:
                flash('Username must be at least 3 characters long.', 'danger')
                return render_template('auth/register.html')

            # Validar contraseña
            is_valid, password_message = validate_password(password)
            if not is_valid:
                flash(password_message, 'danger')
                return render_template('auth/register.html')

            # Verificar si el email ya existe
            if User.query.filter_by(email=email).first():
                flash('Email address already registered.', 'danger')
                return render_template('auth/register.html')

            # Verificar si el username ya existe
            if User.query.filter_by(username=username).first():
                flash('Username already taken.', 'danger')
                return render_template('auth/register.html')

            # Crear nuevo usuario
            new_user = User(email=email, username=username)
            new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                logger.info(f"New user registered: {username}")
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))

            except SQLAlchemyError as e:
                logger.error(f"Database error during registration: {str(e)}")
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        flash('An unexpected error occurred. Please try again.', 'danger')

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """Ruta de logout con logging"""
    try:
        username = current_user.username
        logout_user()
        logger.info(f"User logged out: {username}")
        flash('You have been logged out successfully.', 'success')
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout.', 'danger')

    return redirect(url_for('auth.login'))

# Manejador de errores para el blueprint
@auth.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@auth.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500