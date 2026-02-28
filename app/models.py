from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    has_car = db.Column(db.Boolean, default=False)
    car_model = db.Column(db.String(100))
    car_number = db.Column(db.String(20))
    profile_pic = db.Column(db.String(200), default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hosted_rides = db.relationship('Ride', backref='host', lazy=True, foreign_keys='Ride.host_id')
    ride_requests = db.relationship('RideRequest', backref='rider', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}>'

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_location = db.Column(db.String(300), nullable=False)
    start_lat = db.Column(db.Float)
    start_lng = db.Column(db.Float)
    destination = db.Column(db.String(300), default='College Campus')
    dest_lat = db.Column(db.Float)
    dest_lng = db.Column(db.Float)
    departure_time = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False, default=4)
    total_fuel_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    route_polyline = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('RideRequest', backref='ride', lazy=True, cascade='all, delete-orphan')

    @property
    def confirmed_passengers(self):
        return [r for r in self.requests if r.status == 'confirmed']

    @property
    def seats_taken(self):
        return len(self.confirmed_passengers)

    @property
    def seats_available(self):
        return self.available_seats - self.seats_taken

    @property
    def cost_per_person(self):
        total_riders = self.seats_taken + 1  # +1 for the host
        if total_riders > 0 and self.total_fuel_cost > 0:
            return round(self.total_fuel_cost / total_riders, 2)
        return 0.0

    def __repr__(self):
        return f'<Ride {self.id} from {self.start_location}>'

class RideRequest(db.Model):
    __tablename__ = 'ride_requests'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pickup_location = db.Column(db.String(300), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RideRequest {self.id} for Ride {self.ride_id}>'
