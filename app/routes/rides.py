from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Ride, RideRequest, Message
from app.utils.time import now_local
from config import Config

rides_bp = Blueprint('rides', __name__)

FUEL_TYPES = ('petrol', 'diesel', 'cng', 'electric')
PREFERENCES = ('any', 'female_only', 'male_only')
WAIT_TIMES = (5, 10, 15, 20)


def _map_context():
    from app.utils.fuel_prices import DEFAULTS
    return dict(fuel_defaults=dict(DEFAULTS, electric=Config.ELECTRIC_COST_PER_KM),
                maps_key=Config.GOOGLE_MAPS_API_KEY,
                college_lat=Config.COLLEGE_LOCATION['lat'],
                college_lng=Config.COLLEGE_LOCATION['lng'],
                college_name=Config.COLLEGE_NAME)


def _non_negative(name, default=0.0):
    value = request.form.get(name, default, type=float)
    return value if value is not None and value >= 0 else default


def can_join(ride, user):
    """Whether `user` may ride with this host, given the host's passenger preference."""
    if ride.passenger_preference == 'female_only':
        return user.gender == 'female'
    if ride.passenger_preference == 'male_only':
        return user.gender == 'male'
    return True


@rides_bp.route('/api/fuel-prices')
def fuel_prices_api():
    """Live fuel prices for Chennai — scraped from goodreturns.in, cached 6h."""
    from app.utils.fuel_prices import get_fuel_prices
    return jsonify(get_fuel_prices())


@rides_bp.route('/host', methods=['GET', 'POST'])
@login_required
def host_ride():
    if not current_user.has_vehicle:
        flash('You need to register a vehicle to host rides. Update your profile first.', 'warning')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        start_location = request.form.get('start_location', '').strip()[:300]
        departure_str = request.form.get('departure_time', '')
        available_seats = request.form.get('available_seats', type=int)
        max_seats = current_user.max_passengers

        errors = []
        if not start_location:
            errors.append('Start location is required.')
        if not departure_str:
            errors.append('Departure time is required.')
        if not available_seats or available_seats < 1 or available_seats > max_seats:
            errors.append(f'Available seats must be between 1 and {max_seats}.')

        departure_time = None
        if departure_str:
            try:
                departure_time = datetime.strptime(departure_str, '%Y-%m-%dT%H:%M')
                if departure_time < now_local():
                    errors.append('Departure time must be in the future.')
            except ValueError:
                errors.append('Invalid departure time format.')

        if errors:
            return render_template('rides/host.html', errors=errors, form_data=request.form, **_map_context())

        preference = request.form.get('passenger_preference', 'any')
        # Hosts may only restrict a ride to their own gender
        if preference not in PREFERENCES or (preference != 'any' and preference != f'{current_user.gender}_only'):
            preference = 'any'
        max_wait = request.form.get('max_wait_time', 5, type=int)

        ride = Ride(
            host_id=current_user.id,
            start_location=start_location,
            start_lat=request.form.get('start_lat', type=float),
            start_lng=request.form.get('start_lng', type=float),
            destination=request.form.get('destination', 'SRM IST Campus').strip()[:300] or 'SRM IST Campus',
            dest_lat=request.form.get('dest_lat', type=float) or Config.COLLEGE_LOCATION['lat'],
            dest_lng=request.form.get('dest_lng', type=float) or Config.COLLEGE_LOCATION['lng'],
            departure_time=departure_time,
            available_seats=available_seats,
            total_fuel_cost=_non_negative('fuel_cost'),
            other_charges=_non_negative('other_charges'),
            max_wait_time=max_wait if max_wait in WAIT_TIMES else 5,
            distance_km=_non_negative('distance_km'),
            vehicle_type=current_user.vehicle_type or 'car',
            fuel_type=request.form.get('fuel_type') if request.form.get('fuel_type') in FUEL_TYPES
            else (current_user.fuel_type or 'petrol'),
            passenger_preference=preference,
            notes=request.form.get('notes', '').strip()[:1000],
            status='confirmed'
        )
        db.session.add(ride)
        db.session.commit()
        flash('Ride posted! It is now live — students can request to join.', 'success')
        return redirect(url_for('rides.ride_detail', ride_id=ride.id))

    return render_template('rides/host.html', errors=[], form_data={}, **_map_context())


@rides_bp.route('/find', methods=['GET', 'POST'])
@login_required
def find_ride():
    rides = []
    search_data = {}

    if request.method == 'POST':
        pickup_location = request.form.get('pickup_location', '').strip()
        search_date = request.form.get('search_date', '')
        preferred_time = request.form.get('preferred_time', '')
        girls_only = request.form.get('girls_only') == '1'
        search_data = {
            'pickup_location': pickup_location,
            'search_date': search_date,
            'preferred_time': preferred_time,
            'girls_only': girls_only
        }
        now = now_local()

        query = Ride.query.filter(
            Ride.status.in_(['pending', 'confirmed']),
            Ride.host_id != current_user.id,
            Ride.departure_time >= now,
        )

        # Filter based on passenger preference and user gender
        if current_user.gender == 'female':
            query = query.filter(Ride.passenger_preference != 'male_only')
        elif current_user.gender == 'male':
            query = query.filter(Ride.passenger_preference != 'female_only')
        else:
            query = query.filter(Ride.passenger_preference == 'any')

        # Girls-only filter chip (female users can choose to only see girls-only rides)
        if girls_only and current_user.is_female:
            query = query.filter(Ride.passenger_preference == 'female_only')

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
                        query = query.filter(Ride.departure_time.between(pref_time - timedelta(hours=1),
                                                                         pref_time + timedelta(hours=1)))
                    except ValueError:
                        pass
            except ValueError:
                pass

        rides = query.order_by(Ride.departure_time.asc()).all()

        # Exclude rides the user already requested, and full rides
        user_request_ride_ids = {r.ride_id for r in current_user.ride_requests}
        rides = [r for r in rides if r.id not in user_request_ride_ids and r.seats_available > 0]

    rides_data = [{
        'id': r.id,
        'lat': r.start_lat or 0,
        'lng': r.start_lng or 0,
        'label': r.host.name + ' - ' + r.departure_time.strftime('%I:%M %p')
    } for r in rides]

    today = now_local().date()
    return render_template('rides/find.html', rides=rides, search_data=search_data,
                           rides_data=rides_data,
                           today=today.strftime('%Y-%m-%d'),
                           tomorrow=(today + timedelta(days=1)).strftime('%Y-%m-%d'),
                           **_map_context())


@rides_bp.route('/ride/<int:ride_id>')
@login_required
def ride_detail(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    user_request = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()

    # Get waypoints for confirmed passengers
    waypoints = []
    for req in ride.confirmed_passengers:
        if req.pickup_lat and req.pickup_lng:
            waypoints.append({
                'lat': req.pickup_lat,
                'lng': req.pickup_lng,
                'name': req.rider.name
            })

    return render_template('rides/detail.html', ride=ride, user_request=user_request,
                           waypoints=waypoints,
                           can_join=can_join(ride, current_user),
                           is_upcoming=ride.departure_time >= now_local(),
                           **_map_context())


@rides_bp.route('/ride/<int:ride_id>/chat', methods=['POST'])
@login_required
def send_message(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    content = request.form.get('content', '').strip()[:1000]

    # Safety check: sender must be host or a confirmed passenger
    is_confirmed = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id, status='confirmed').first()
    if not (current_user.id == ride.host_id or is_confirmed):
        flash('You must join the ride to chat.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))

    if content:
        msg = Message(ride_id=ride_id, sender_id=current_user.id, content=content)
        db.session.add(msg)
        db.session.commit()
    return redirect(url_for('rides.ride_detail', ride_id=ride_id) + '#chat')


@rides_bp.route('/ride/<int:ride_id>/request', methods=['POST'])
@login_required
def request_ride(ride_id):
    ride = db.get_or_404(Ride, ride_id)
    back = redirect(url_for('rides.ride_detail', ride_id=ride_id))
    if ride.host_id == current_user.id:
        flash('You cannot request your own ride.', 'danger')
        return back
    if ride.status != 'confirmed' or ride.departure_time < now_local():
        flash('This ride is no longer accepting requests.', 'danger')
        return back
    if not can_join(ride, current_user):
        flash("This ride is restricted by the host's passenger preference.", 'danger')
        return back
    if ride.seats_available <= 0:
        flash('Sorry, this ride is full.', 'danger')
        return back
    existing = RideRequest.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()
    if existing:
        flash('You have already requested this ride.', 'warning')
        return back

    pickup_location = request.form.get('pickup_location', '').strip()[:300]
    if not pickup_location:
        flash('Please enter a pickup location.', 'danger')
        return back

    ride_req = RideRequest(
        ride_id=ride_id,
        rider_id=current_user.id,
        pickup_location=pickup_location,
        pickup_lat=request.form.get('pickup_lat', type=float),
        pickup_lng=request.form.get('pickup_lng', type=float),
        message=request.form.get('message', '').strip()[:500],
        status='pending'
    )
    db.session.add(ride_req)
    db.session.commit()
    flash('Ride request sent! Waiting for host confirmation.', 'success')
    return back


@rides_bp.route('/ride/<int:ride_id>/manage/<int:request_id>/<action>', methods=['POST'])
@login_required
def manage_request(ride_id, request_id, action):
    ride = db.get_or_404(Ride, ride_id)
    if ride.host_id != current_user.id:
        flash('Only the host can manage requests.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))

    ride_req = db.get_or_404(RideRequest, request_id)
    # The request must belong to this ride, otherwise a host could approve requests on other people's rides
    if ride_req.ride_id != ride.id:
        abort(404)
    if ride_req.status != 'pending':
        flash('This request has already been handled.', 'info')
    elif action == 'confirm':
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
    else:
        abort(404)
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))


@rides_bp.route('/ride/<int:ride_id>/status/<status>', methods=['POST'])
@login_required
def update_ride_status(ride_id, status):
    ride = db.get_or_404(Ride, ride_id)
    if ride.host_id != current_user.id:
        flash('Only the host can update ride status.', 'danger')
        return redirect(url_for('rides.ride_detail', ride_id=ride_id))
    if ride.status in ('completed', 'cancelled'):
        flash(f'This ride is already {ride.status}.', 'info')
    elif status in ('completed', 'cancelled'):
        ride.status = status
        db.session.commit()
        flash(f'Ride status updated to {status}.', 'success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))


@rides_bp.route('/ride/<int:ride_id>/cancel-request', methods=['POST'])
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
