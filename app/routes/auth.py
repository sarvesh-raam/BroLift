from urllib.parse import urlsplit

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import re
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

VEHICLE_TYPES = ('car', 'bike')
FUEL_TYPES = ('petrol', 'diesel', 'cng', 'electric')
GENDERS = ('male', 'female', 'other')
CAPACITIES = (5, 7)


def is_valid_srm_email(email):
    """Validate SRM IST email: 2 letters + 4 digits @srmist.edu.in"""
    pattern = r'^[a-zA-Z]{2}\d{4}@srmist\.edu\.in$'
    return bool(re.match(pattern, email.lower()))


def _choice(value, allowed, default):
    return value if value in allowed else default


def _is_safe_next(target):
    """Only allow redirects back into this site (blocks ?next=https://evil.example)."""
    if not target:
        return False
    parts = urlsplit(target)
    return not parts.scheme and not parts.netloc and target.startswith('/') and not target.startswith('//')


def _read_vehicle_form(defaults):
    """Parse the vehicle fields, falling back to `defaults` for anything not submitted."""
    vehicle_type = _choice(request.form.get('vehicle_type'), VEHICLE_TYPES, defaults['vehicle_type'])
    capacity = request.form.get('vehicle_capacity', type=int)
    mileage = request.form.get('vehicle_mileage', type=float)
    return {
        'vehicle_type': vehicle_type,
        'vehicle_model': request.form.get('vehicle_model', '').strip()[:100],
        'vehicle_number': request.form.get('vehicle_number', '').strip().upper()[:20],
        'vehicle_capacity': 1 if vehicle_type == 'bike' else _choice(capacity, CAPACITIES, defaults['vehicle_capacity']),
        'vehicle_mileage': mileage if mileage and 0 < mileage <= 200 else defaults['vehicle_mileage'],
        'fuel_type': _choice(request.form.get('fuel_type'), FUEL_TYPES, defaults['fuel_type']),
    }


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:100]
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        has_vehicle = request.form.get('has_vehicle') == 'on'
        gender = _choice(request.form.get('gender'), GENDERS, 'other')
        vehicle = _read_vehicle_form({'vehicle_type': 'car', 'vehicle_capacity': 5,
                                      'vehicle_mileage': 15.0, 'fuel_type': 'petrol'})

        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or not is_valid_srm_email(email):
            errors.append('Only valid SRM IST emails allowed (e.g. st6546@srmist.edu.in).')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if has_vehicle and (not vehicle['vehicle_model'] or not vehicle['vehicle_number']):
            errors.append('Please provide your vehicle model and number.')

        if errors:
            return render_template('auth/register.html', errors=errors, form_data=request.form)

        user = User(name=name, email=email, has_vehicle=has_vehicle, gender=gender, **vehicle)
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
            login_user(user, remember=request.form.get('remember') == 'on')
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page if _is_safe_next(next_page) else url_for('dashboard.index'))
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
        name = request.form.get('name', '').strip()[:100]
        has_vehicle = request.form.get('has_vehicle') == 'on'
        # Fields missing from the form keep their current values instead of being reset
        vehicle = _read_vehicle_form({
            'vehicle_type': current_user.vehicle_type or 'car',
            'vehicle_capacity': current_user.vehicle_capacity or 5,
            'vehicle_mileage': current_user.vehicle_mileage or 15.0,
            'fuel_type': current_user.fuel_type or 'petrol',
        })

        if has_vehicle and (not vehicle['vehicle_model'] or not vehicle['vehicle_number']):
            flash('Please provide your vehicle model and number.', 'danger')
            return render_template('auth/profile.html')

        current_user.name = name or current_user.name
        current_user.gender = _choice(request.form.get('gender'), GENDERS, current_user.gender)
        current_user.has_vehicle = has_vehicle
        for key, value in vehicle.items():
            setattr(current_user, key, value)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html')
