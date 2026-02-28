from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Ride, RideRequest

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def landing():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    hosted_rides = Ride.query.filter_by(host_id=current_user.id)\
        .order_by(Ride.departure_time.desc()).limit(5).all()

    my_requests = RideRequest.query.filter_by(rider_id=current_user.id)\
        .order_by(RideRequest.created_at.desc()).limit(5).all()

    upcoming = []
    for ride in hosted_rides:
        if ride.departure_time >= datetime.now() and ride.status != 'cancelled':
            upcoming.append({'type': 'host', 'ride': ride})
    for req in my_requests:
        if req.status == 'confirmed' and req.ride.departure_time >= datetime.now():
            upcoming.append({'type': 'passenger', 'ride': req.ride, 'request': req})

    upcoming.sort(key=lambda x: x['ride'].departure_time)

    stats = {
        'rides_hosted': len(hosted_rides),
        'rides_joined': len([r for r in my_requests if r.status == 'confirmed']),
        'pending_requests': len([r for r in hosted_rides for req in r.requests if req.status == 'pending']),
    }

    return render_template('dashboard/index.html', hosted_rides=hosted_rides,
                           my_requests=my_requests, upcoming=upcoming, stats=stats)
