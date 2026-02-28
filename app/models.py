from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    # Vehicle
    has_vehicle    = db.Column(db.Boolean, default=False)
    vehicle_type   = db.Column(db.String(10), default='car')    # car / bike
    vehicle_model  = db.Column(db.String(100))
    vehicle_number = db.Column(db.String(20))
    vehicle_capacity = db.Column(db.Integer, default=5)         # 5 or 7 for car, 1 for bike
    vehicle_mileage  = db.Column(db.Float, default=15.0)        # km per litre/kg
    fuel_type      = db.Column(db.String(10), default='petrol') # petrol/diesel/cng/electric
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    hosted_rides   = db.relationship('Ride', backref='host', lazy=True, foreign_keys='Ride.host_id')
    ride_requests  = db.relationship('RideRequest', backref='rider', lazy=True)

    # backward-compat
    @property
    def has_car(self):        return self.has_vehicle
    @property
    def car_model(self):      return self.vehicle_model
    @property
    def car_number(self):     return self.vehicle_number

    def set_password(self, p):  self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)
    def __repr__(self): return f'<User {self.name}>'


class Ride(db.Model):
    __tablename__ = 'rides'
    id              = db.Column(db.Integer, primary_key=True)
    host_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_location  = db.Column(db.String(300), nullable=False)
    start_lat       = db.Column(db.Float)
    start_lng       = db.Column(db.Float)
    destination     = db.Column(db.String(300), default='SRM IST Campus')
    dest_lat        = db.Column(db.Float)
    dest_lng        = db.Column(db.Float)
    departure_time  = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False, default=4)
    total_fuel_cost = db.Column(db.Float, default=0.0)
    distance_km     = db.Column(db.Float, default=0.0)
    vehicle_type    = db.Column(db.String(10), default='car')
    fuel_type       = db.Column(db.String(10), default='petrol')
    status          = db.Column(db.String(20), default='confirmed')
    notes           = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('RideRequest', backref='ride', lazy=True, cascade='all, delete-orphan')

    @property
    def confirmed_passengers(self):
        return [r for r in self.requests if r.status == 'confirmed']

    @property
    def seats_taken(self):
        return len(self.confirmed_passengers)

    @property
    def seats_available(self):
        return max(0, self.available_seats - self.seats_taken)

    @property
    def cost_per_person(self):
        """
        Split total fuel cost equally between host + ALL offered seats.
        This gives a fixed estimated share regardless of how many have joined.
        """
        if self.total_fuel_cost and self.total_fuel_cost > 0:
            return round(self.total_fuel_cost / (self.available_seats + 1), 2)
        return 0.0

    def __repr__(self): return f'<Ride {self.id}>'


class RideRequest(db.Model):
    __tablename__ = 'ride_requests'
    id              = db.Column(db.Integer, primary_key=True)
    ride_id         = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rider_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pickup_location = db.Column(db.String(300), nullable=False)
    pickup_lat      = db.Column(db.Float)
    pickup_lng      = db.Column(db.Float)
    status          = db.Column(db.String(20), default='pending')
    message         = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self): return f'<RideRequest {self.id}>'
