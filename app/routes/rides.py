from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date as date_type
from app import db
from app.models import Ride, RideRequest, User
from config import Config

rides_bp = Blueprint('rides', __name__)

@rides_bp.route('/host', methods=['GET', 'POST'])
@login_required
def host_ride():
    if not current_user.has_car:
        flash('You need to register a car to host rides. Update your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        start_location = request.form.get('start_location', '').strip()
        start_lat = request.form.get('start_lat', type=float)
        start_lng = request.form.get('start_lng', type=float)
        dest_lat = request.form.get('dest_lat', type=float)
        dest_lng = request.form.get('dest_lng', type=float)
        destination = request.form.get('destination', 'SRM IST Campus').strip()
        departure_str = request.form.get('departure_time', '')
        available_seats = request.form.get('available_seats', type=int)
        fuel_cost = request.form.get('fuel_cost', type=float, default=0.0)
        notes = request.form.get('notes', '').strip()

        errors = []
        if not start_location:
            errors.append('Start location is required.')
        if not departure_str:
            errors.append('Departure time is required.')
        if not available_seats or available_seats < 1 or available_seats > Config.MAX_PASSENGERS:
            errors.append(f'Available seats must be between 1 and {Config.MAX_PASSENGERS}.')

        departure_time = None
        if departure_str:
            try:
                departure_time = datetime.strptime(departure_str, '%Y-%m-%dT%H:%M')
                if departure_time < datetime.now():
                    errors.append('Departure time must be in the future.')
            except ValueError:
                errors.append('Invalid departure time format.')

        if errors:
            return render_template('rides/host.html', errors=errors, form_data=request.form,
                                   maps_key=Config.GOOGLE_MAPS_API_KEY,
                                   college_lat=Config.COLLEGE_LOCATION['lat'],
                                   college_lng=Config.COLLEGE_LOCATION['lng'],
                                   college_name=Config.COLLEGE_NAME)

        ride = Ride(
            host_id=current_user.id,
            start_location=start_location,
            start_lat=start_lat,
            start_lng=start_lng,
            destination=destination,
            dest_lat=dest_lat or Config.COLLEGE_LOCATION['lat'],
            dest_lng=dest_lng or Config.COLLEGE_LOCATION['lng'],
            departure_time=departure_time,
            available_seats=available_seats,
            total_fuel_cost=fuel_cost,
            notes=notes,
            status='pending'
        )
        db.session.add(ride)
        db.session.commit()
        flash('Ride posted successfully! Students can now request to join.', 'success')
        return redirect(url_for('rides.ride_detail', ride_id=ride.id))

    return render_template('rides/host.html', errors=[], form_data={},
                           maps_key=Config.GOOGLE_MAPS_API_KEY,
                           college_lat=Config.COLLEGE_LOCATION['lat'],
                           college_lng=Config.COLLEGE_LOCATION['lng'],
                           college_name=Config.COLLEGE_NAME)

@rides_bp.route('/find', methods=['GET', 'POST'])
@login_required
def find_ride():
    rides = []
    search_data = {}

    if request.method == 'POST':
        pickup_location = request.form.get('pickup_location', '').strip()
        search_date = request.form.get('search_date', '')
        preferred_time = request.form.get('preferred_time', '')
        search_data = {
            'pickup_location': pickup_location,
            'search_date': search_date,
            'preferred_time': preferred_time
        }

        query = Ride.query.filter(
            Ride.status.in_(['pending', 'confirmed']),
            Ride.host_id != current_user.id
        )

        if search_date:
            try:
                search_dt = datetime.strptime(search_date, '%Y-%m-%d')
                day_start = search_dt.replace(hour=0, minute=0, second=0)
                day_end = search_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Ride.departure_time.between(day_start, day_end))
                # If time filter also provided, narrow it down further (+/- 1 hour)
                if preferred_time:
                    try:
                        pref_time = datetime.strptime(f"{search_date} {preferred_time}", '%Y-%m-%d %H:%M')
                        time_from = pref_time - timedelta(hours=1)
                        time_to = pref_time + timedelta(hours=1)
                        query = query.filter(Ride.departure_time.between(time_from, time_to))
                    except ValueError:
                        pass
            except ValueError:
                pass
        else:
            # No date selected — show all upcoming rides
            query = query.filter(Ride.departure_time >= datetime.now())

        rides = query.order_by(Ride.departure_time.asc()).all()

        # Exclude rides the user already joined
        user_request_ride_ids = {r.ride_id for r in current_user.ride_requests}
        rides = [r for r in rides if r.id not in user_request_ride_ids]

    return render_template('rides/find.html', rides=rides, search_data=search_data,
                           maps_key=Config.GOOGLE_MAPS_API_KEY,
                           college_lat=Config.COLLEGE_LOCATION['lat'],
                           college_lng=Config.COLLEGE_LOCATION['lng'])

@rides_bp.route('/ride/<int:ride_id>')
@login_required
def ride_detail(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    user_request = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()
    return render_template('rides/detail.html', ride=ride, user_request=user_request,
                           maps_key=Config.GOOGLE_MAPS_API_KEY,
                           college_lat=Config.COLLEGE_LOCATION['lat'],
                           college_lng=Config.COLLEGE_LOCATION['lng'])

@rides_bp.route('/ride/<int:ride_id>/request', methods=['POST'])
@login_required
def request_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.host_id == current_user.id:
        flash('You cannot request your own ride.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))
    if ride.seats_available <= 0:
        flash('Sorry, this ride is full.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))
    existing = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()
    if existing:
        flash('You have already requested this ride.', 'warning')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))

    pickup_location = request.form.get('pickup_location', '').strip()
    pickup_lat = request.form.get('pickup_lat', type=float)
    pickup_lng = request.form.get('pickup_lng', type=float)
    message = request.form.get('message', '').strip()

    ride_req = RideRequest(
        ride_id=ride_id,
        rider_id=current_user.id,
        pickup_location=pickup_location,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        message=message,
        status='pending'
    )
    db.session.add(ride_req)
    db.session.commit()
    flash('Ride request sent! Waiting for host confirmation.', 'success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/ride/<int:ride_id>/manage/<int:request_id>/<action>')
@login_required
def manage_request(ride_id, request_id, action):
    ride = Ride.query.get_or_404(ride_id)
    if ride.host_id != current_user.id:
        flash('Only the host can manage requests.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))

    ride_req = RideRequest.query.get_or_404(request_id)
    if action == 'confirm':
        if ride.seats_available <= 0:
            flash('No more seats available.', 'danger')
        else:
            ride_req.status = 'confirmed'
            db.session.commit()
            flash(f"{ride_req.rider.name}'s request confirmed!", 'success')
    elif action == 'reject':
        ride_req.status = 'rejected'
        db.session.commit()
        flash(f"{ride_req.rider.name}'s request rejected.", 'info')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/ride/<int:ride_id>/status/<status>')
@login_required
def update_ride_status(ride_id, status):
    ride = Ride.query.get_or_404(ride_id)
    if ride.host_id != current_user.id:
        flash('Only the host can update ride status.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))
    if status in ['confirmed', 'completed', 'cancelled']:
        ride.status = status
        db.session.commit()
        flash(f'Ride status updated to {status}.', 'success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/ride/<int:ride_id>/cancel-request')
@login_required
def cancel_request(ride_id):
    ride_req = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first_or_404()
    if ride_req.status == 'confirmed':
        flash('Cannot cancel a confirmed request. Contact the host.', 'warning')
    else:
        db.session.delete(ride_req)
        db.session.commit()
        flash('Ride request cancelled.', 'info')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))
