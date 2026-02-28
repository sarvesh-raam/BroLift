from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        has_car = request.form.get('has_car') == 'on'
        car_model = request.form.get('car_model', '').strip()
        car_number = request.form.get('car_number', '').strip()

        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or not email.endswith('.edu'):
            errors.append('Only college (.edu) email addresses are allowed.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if has_car and (not car_model or not car_number):
            errors.append('Please provide your car model and number.')

        if errors:
            return render_template('auth/register.html', errors=errors, form_data=request.form)

        user = User(name=name, email=email, has_car=has_car, car_model=car_model, car_number=car_number)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('🎉 Account created! Welcome to BroLift!', 'success')
        login_user(user)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', errors=[], form_data={})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}! 👋', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name).strip()
        current_user.has_car = request.form.get('has_car') == 'on'
        current_user.car_model = request.form.get('car_model', '').strip()
        current_user.car_number = request.form.get('car_number', '').strip()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('auth/profile.html')
