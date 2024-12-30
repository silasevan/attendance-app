from flask import Blueprint, render_template, redirect, url_for, flash, request,abort
from flask_login import login_required, current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from geopy.distance import geodesic
from datetime import datetime, time
from . import db
from .models import User, AttendanceRecord
from .forms import LoginForm, RegistrationForm, PasswordResetRequestForm, ResetPasswordForm
from .utils import send_reset_email
from functools import wraps
from .error import render_error_page

main = Blueprint('main', __name__)

# Configuration Constants
COMPANY_LOCATION = (7.130402, 3.362196)  # Example: Lagos, Nigeria
SIGN_IN_DEADLINE = time(0, 10)  # 7:00 AM
SIGN_OUT_START = time(0, 12)  # 5:00 PM
AUTO_SIGN_OUT_TIME = time(0, 13)  # 7:00 PM

# Utility function to check if user is within company location
def is_within_company_location(user_lat, user_lon):
    user_location = (user_lat, user_lon)
    distance = geodesic(COMPANY_LOCATION, user_location).meters
    print(f"User location: {user_location}, Company location: {COMPANY_LOCATION}, Distance: {distance} meters")
    return distance <= 100  # Allow sign-in within 100 meters

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
           return render_error_page(403)
        return f(*args, **kwargs)
    return decorated_function

# Route for user registration

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            role = form.role.data  # Get role from form
            user = User(email=form.email.data, name=form.name.data, password=form.password.data, role=role)
            db.session.add(user)
            db.session.commit()
            flash(f'Successfully registered as a {role}!', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists.', 'warning')
    return render_template('register.html', form=form)



# Route for user login
@main.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('You have successfully logged in', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

# Route for user logout
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.login'))

# Helper function to add attendance record
def add_attendance_record(user_id, geo_location, action='sign_in'):
    today = datetime.today().date()
    time_now = datetime.now().time()

    record = AttendanceRecord.query.filter_by(user_id=user_id, date=today).first()

    if not record:
        record = AttendanceRecord(user_id=user_id, date=today, geo_location=geo_location)
        if action == 'sign_in':
            record.sign_in_time = time_now
        db.session.add(record)
    else:
        if action == 'sign_out' and not record.sign_out_time:
            record.sign_out_time = time_now
        else:
            return False  # Either already signed out or trying to sign out without signing in

    db.session.commit()
    return True

# Route for user sign-in
@main.route('/sign-in', methods=['POST'])
@login_required
def sign_in():
    user_lat = request.form.get('latitude', type=float)
    user_lon = request.form.get('longitude', type=float)
    print(f"Received coordinates: Latitude: {user_lat}, Longitude: {user_lon}")
    
    if is_within_company_location(user_lat, user_lon):
        today = datetime.today().date()
        existing_record = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()
        if not existing_record:
            add_attendance_record(current_user.id, f"{user_lat},{user_lon}", 'sign_in')
            flash('Sign-in successful!', 'success')
        else:
            flash('Already signed in for today.', 'info')
    else:
        flash('You must be within the company location to sign in.', 'danger')
    return redirect(url_for('main.dashboard'))

# Route for user sign-out
@main.route('/sign-out', methods=['POST'])
@login_required
def sign_out():
    user_lat = request.form.get('latitude', type=float)
    user_lon = request.form.get('longitude', type=float)
    print(f"Received coordinates: Latitude: {user_lat}, Longitude: {user_lon}")
    
    # Set time constraints
    current_time = datetime.now().time()
    today = datetime.today().date()
    record = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()

    if not record:
        flash('No sign-in record found for today.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Check if already signed out
    if record.sign_out_time:
        flash('You have already signed out.', 'info')
        return redirect(url_for('main.dashboard'))

    # Automatic sign-out if past the set time
    if current_time >= AUTO_SIGN_OUT_TIME:
        record.sign_out_time = AUTO_SIGN_OUT_TIME
        record.auto_signed_out = True
        db.session.commit()
        flash('You were automatically signed out.', 'info')
    elif current_time >= SIGN_OUT_START:
        record.sign_out_time = datetime.now().time()
        db.session.commit()
        flash('Sign-out successful!', 'success')
    else:
        flash(f'You can only sign out manually starting from {SIGN_OUT_START}.', 'warning')

    return redirect(url_for('main.dashboard'))

# Route for user dashboard
@main.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_records = AttendanceRecord.query.filter_by(user_id=current_user.id).order_by(AttendanceRecord.date.desc()).all()

    # Handle filtering by month
    month = request.args.get('month', default=None, type=int)
    if month:
        user_records = [record for record in user_records if record.date.month == month]
    
    today = datetime.today().date()
    record_today = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()

    late_status = None
    if record_today and record_today.sign_in_time:
        late_status = record_today.sign_in_time > SIGN_IN_DEADLINE

    # Calculate the distance from user's current location to company's location
    user_lat = request.form.get('latitude', type=float)
    user_lon = request.form.get('longitude', type=float)
    distance = geodesic(COMPANY_LOCATION, (user_lat, user_lon)).meters
    distance = round(distance, 2)

    return render_template(
        'dashboard.html',
        records=user_records,
        record_today=record_today,
        late_status=late_status,
        current_time=datetime.now().time(),
        SIGN_OUT_START=SIGN_OUT_START,
        COMPANY_LOCATION=COMPANY_LOCATION,
        distance=distance,
        filtered_records=user_records
    )


# Route for admin dashboard
@main.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access restricted to admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    all_records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).all()
    return render_template('admin_dashboard.html', records=all_records)



# Route for password reset request
@main.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('Check your email for the instructions to reset your password.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html', form=form)

# Route for resetting the password
@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('main.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form)






@main.route('/register-admin', methods=['GET', 'POST'])
@login_required
def register_admin():
    if not current_user.is_admin:
        flash('Access denied. Only admins can register new admins.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered.', 'danger')
            return redirect(url_for('main.register_admin'))

        # Create a new admin user
        admin_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

        flash(f'Admin {name} registered successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('register_admin.html')




@main.route('/admin/attendance-records', methods=['GET', 'POST'])
@admin_required
def admin_attendance_records():
    if not current_user.is_admin:
        flash('Access denied. Only admins can view attendance records.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Get query parameters
    search_query = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '')
    sign_in_status = request.args.get('sign_in_status', '')
    sign_out_status = request.args.get('sign_out_status', '')

    # Query attendance records
    query = AttendanceRecord.query.join(User).order_by(AttendanceRecord.date.desc())

    # Apply filters
    if search_query:
        query = query.filter(
            (User.name.ilike(f'%{search_query}%')) | (User.email.ilike(f'%{search_query}%'))
        )
    if date_filter:
        query = query.filter(AttendanceRecord.date == date_filter)
    if sign_in_status == 'signed_in':
        query = query.filter(AttendanceRecord.sign_in_time.isnot(None))
    elif sign_in_status == 'not_signed_in':
        query = query.filter(AttendanceRecord.sign_in_time.is_(None))
    if sign_out_status == 'signed_out':
        query = query.filter(AttendanceRecord.sign_out_time.isnot(None))
    elif sign_out_status == 'not_signed_out':
        query = query.filter(AttendanceRecord.sign_out_time.is_(None))

    records = query.all()

    return render_template('admin_attendance_records.html', records=records)

