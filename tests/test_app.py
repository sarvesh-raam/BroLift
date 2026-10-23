from datetime import timedelta

import pytest
from sqlalchemy import create_engine, inspect, text

from app import create_app, db
from app.models import Ride, RideRequest
from app.utils.time import now_local
from config import Config


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        SQLALCHEMY_ENGINE_OPTIONS = {}

    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def register(client, email, gender='male', vehicle=True, vehicle_type='car'):
    data = dict(name='Test ' + email[:6], email=email, password='secret123', confirm_password='secret123',
                gender=gender, vehicle_type=vehicle_type, vehicle_capacity='5', vehicle_model='Swift',
                vehicle_number='TN01AB1234', vehicle_mileage='18', fuel_type='petrol')
    if vehicle:
        data['has_vehicle'] = 'on'
    return client.post('/register', data=data)


def host_ride(client, **overrides):
    data = dict(start_location='Tambaram', start_lat='12.92', start_lng='80.12',
                departure_time=(now_local() + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'),
                available_seats='2', fuel_cost='300', other_charges='0', max_wait_time='5',
                distance_km='20', fuel_type='petrol', passenger_preference='any')
    data.update(overrides)
    return client.post('/host', data=data)


@pytest.fixture
def host(app):
    c = app.test_client()
    register(c, 'ab1234@srmist.edu.in')
    return c


@pytest.fixture
def rider(app):
    c = app.test_client()
    register(c, 'cd5678@srmist.edu.in', vehicle=False)
    return c


def test_public_pages(app):
    c = app.test_client()
    for path in ['/', '/login', '/register', '/healthz']:
        assert c.get(path).status_code == 200
    assert c.get('/dashboard').status_code == 302
    assert c.get('/no-such-page').status_code == 404


def test_registration_rejects_non_srm_email(app):
    r = register(app.test_client(), 'someone@gmail.com')
    assert r.status_code == 200
    assert b'Only valid SRM IST emails' in r.data


def test_full_ride_flow(host, rider, app):
    assert host_ride(host).headers['Location'].endswith('/ride/1')
    for c in (host, rider):
        for path in ['/dashboard', '/find', '/profile', '/ride/1']:
            assert c.get(path).status_code == 200, path
    assert b'Tambaram' in rider.post('/find', data={}).data

    rider.post('/ride/1/request', data=dict(pickup_location='Guduvanchery', pickup_lat='12.84', pickup_lng='80.06'))
    host.post('/ride/1/manage/1/confirm')
    rider.post('/ride/1/chat', data=dict(content='hello <script>x</script>'))
    page = host.get('/ride/1').data
    assert b'&lt;script&gt;x' in page and b'<script>x' not in page
    with app.app_context():
        assert db.session.get(RideRequest, 1).status == 'confirmed'


def test_host_cannot_manage_request_on_another_ride(app, host, rider):
    attacker = app.test_client()
    register(attacker, 'ef9012@srmist.edu.in')
    host_ride(host)       # ride 1
    host_ride(attacker)   # ride 2
    rider.post('/ride/1/request', data=dict(pickup_location='X'))
    assert attacker.post('/ride/2/manage/1/confirm').status_code == 404
    with app.app_context():
        assert db.session.get(RideRequest, 1).status == 'pending'


def test_state_changes_require_post(host):
    host_ride(host)
    assert host.get('/ride/1/status/cancelled').status_code == 405


def test_preference_enforced_on_request(app, rider):
    female_host = app.test_client()
    register(female_host, 'gh3456@srmist.edu.in', gender='female')
    host_ride(female_host, passenger_preference='female_only')
    rider.post('/ride/1/request', data=dict(pickup_location='X'))
    with app.app_context():
        assert RideRequest.query.count() == 0


def test_cannot_join_cancelled_ride(app, host, rider):
    host_ride(host)
    host.post('/ride/1/status/cancelled')
    rider.post('/ride/1/request', data=dict(pickup_location='X'))
    with app.app_context():
        assert RideRequest.query.count() == 0


def test_bike_owner_can_offer_one_seat(app):
    c = app.test_client()
    register(c, 'ij7890@srmist.edu.in', vehicle_type='bike')
    assert b'name="available_seats" value="1"' in c.get('/host').data
    host_ride(c, available_seats='1')
    host_ride(c, available_seats='3')
    with app.app_context():
        assert [r.available_seats for r in Ride.query.all()] == [1]


def test_profile_update_keeps_vehicle_settings(app):
    c = app.test_client()
    register(c, 'kl1234@srmist.edu.in', vehicle_type='bike')
    c.post('/profile', data=dict(name='New Name', gender='male', has_vehicle='on',
                                 vehicle_model='Pulsar', vehicle_number='TN02', vehicle_mileage='40'))
    from app.models import User
    with app.app_context():
        u = User.query.first()
        assert (u.name, u.vehicle_type, u.vehicle_capacity) == ('New Name', 'bike', 1)


def test_login_rejects_external_next(app):
    c = app.test_client()
    register(c, 'mn5678@srmist.edu.in')
    c.get('/logout')
    r = c.post('/login?next=https://evil.example/', data=dict(email='mn5678@srmist.edu.in', password='secret123'))
    assert r.headers['Location'] == '/dashboard'


def test_migration_adds_missing_columns(tmp_path):
    """A database created by the very first release must be upgraded in place."""
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, '
                          'email VARCHAR(120) NOT NULL UNIQUE, password_hash VARCHAR(256) NOT NULL, '
                          'has_car BOOLEAN, car_model VARCHAR(100), car_number VARCHAR(20), created_at DATETIME)'))
        conn.execute(text("INSERT INTO users (name, email, password_hash, has_car, car_model, car_number) "
                          "VALUES ('Old', 'op1234@srmist.edu.in', 'x', 1, 'Alto', 'TN09')"))
        conn.execute(text('CREATE TABLE rides (id INTEGER PRIMARY KEY, host_id INTEGER NOT NULL, '
                          'start_location VARCHAR(300) NOT NULL, departure_time DATETIME NOT NULL, '
                          'available_seats INTEGER NOT NULL)'))
    engine.dispose()

    class LegacyConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = url
        SQLALCHEMY_ENGINE_OPTIONS = {}

    app = create_app(LegacyConfig)
    with app.app_context():
        cols = {c['name'] for c in inspect(db.engine).get_columns('users')}
        assert {'has_vehicle', 'vehicle_type', 'gender', 'fuel_type'} <= cols
        row = db.session.execute(text('SELECT has_vehicle, vehicle_model FROM users')).one()
        assert bool(row[0]) and row[1] == 'Alto'
        db.session.remove()
        db.engine.dispose()


def test_csrf_tokens_present_and_enforced(tmp_path):
    import re

    class CsrfConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'csrf.db'}"
        SQLALCHEMY_ENGINE_OPTIONS = {}

    app = create_app(CsrfConfig)
    c = app.test_client()

    def token(path):
        return re.search(rb'name="csrf_token" value="([^"]+)"', c.get(path).data).group(1).decode()

    assert c.post('/login', data=dict(email='x', password='y')).status_code == 400
    r = c.post('/register', data=dict(csrf_token=token('/register'), name='A', email='qr1234@srmist.edu.in',
                                      password='secret123', confirm_password='secret123', gender='male',
                                      has_vehicle='on', vehicle_type='car', vehicle_capacity='5',
                                      vehicle_model='Swift', vehicle_number='TN01', fuel_type='petrol'))
    assert r.status_code == 302
    r = c.post('/host', data=dict(csrf_token=token('/host'), start_location='Tambaram', available_seats='1',
                                  departure_time=(now_local() + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')))
    assert r.headers['Location'].endswith('/ride/1')
    detail = c.get('/ride/1').data
    assert detail.count(b'name="csrf_token"') >= 3  # chat, complete, cancel
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
