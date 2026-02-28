from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import re
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

def is_valid_srm_email(email):
    """Validate SRM IST email: 2 letters + 4 digits @srmist.edu.in"""
    pattern = r'^[a-zA-Z]{2}\d{4}@srmist\.edu\.in$'
    return bool(re.match(pattern, email.lower()))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        has_vehicle = request.form.get('has_vehicle') == 'on'
        vehicle_type = request.form.get('vehicle_type', 'car')
        vehicle_model = request.form.get('vehicle_model', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip()
        vehicle_capacity = request.form.get('vehicle_capacity', 5, type=int)
        vehicle_mileage = request.form.get('vehicle_mileage', 15.0, type=float)

        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or not is_valid_srm_email(email):
            errors.append('Only valid SRM IST emails allowed (e.g. st6546@srmist.edu.in).')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if has_vehicle and (not vehicle_model or not vehicle_number):
            errors.append('Please provide your vehicle model and number.')

        if errors:
            return render_template('auth/register.html', errors=errors, form_data=request.form)

        user = User(
            name=name, email=email,
            has_vehicle=has_vehicle,
            vehicle_type=vehicle_type,
            vehicle_model=vehicle_model,
            vehicle_number=vehicle_number,
            vehicle_capacity=vehicle_capacity if vehicle_type == 'car' else 1,
            vehicle_mileage=vehicle_mileage
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Welcome to BroLift.', 'success')
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
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
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
        current_user.has_vehicle = request.form.get('has_vehicle') == 'on'
        current_user.vehicle_type = request.form.get('vehicle_type', 'car')
        current_user.vehicle_model = request.form.get('vehicle_model', '').strip()
        current_user.vehicle_number = request.form.get('vehicle_number', '').strip()
        current_user.vehicle_mileage = request.form.get('vehicle_mileage', 15.0, type=float)
        if current_user.vehicle_type == 'car':
            current_user.vehicle_capacity = request.form.get('vehicle_capacity', 5, type=int)
        else:
            current_user.vehicle_capacity = 1
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('auth/profile.html')
