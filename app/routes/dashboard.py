from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ride, RideRequest
from app.utils.time import now_local

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    now = now_local()
    hosted_rides = Ride.query.filter_by(host_id=current_user.id)\
        .order_by(Ride.departure_time.desc()).limit(5).all()

    my_requests = RideRequest.query.filter_by(rider_id=current_user.id)\
        .order_by(RideRequest.created_at.desc()).limit(5).all()

    upcoming_hosted = Ride.query.filter(
        Ride.host_id == current_user.id,
        Ride.status == 'confirmed',
        Ride.departure_time >= now,
    ).order_by(Ride.departure_time.asc()).all()

    upcoming_joined = RideRequest.query.join(Ride).filter(
        RideRequest.rider_id == current_user.id,
        RideRequest.status == 'confirmed',
        Ride.status == 'confirmed',
        Ride.departure_time >= now,
    ).order_by(Ride.departure_time.asc()).all()

    return render_template('dashboard/index.html', hosted_rides=hosted_rides,
                           my_requests=my_requests,
                           upcoming_hosted=upcoming_hosted,
                           upcoming_joined=upcoming_joined,
                           now=now)
