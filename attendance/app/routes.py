from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from geopy.distance import geodesic
from datetime import datetime, time
from . import db
from .models import User, AttendanceRecord
from .forms import LoginForm, RegistrationForm, PasswordResetRequestForm, ResetPasswordForm
from .utils import send_reset_email

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
    return distance <= 100000  # Allow sign-in within 100 meters

# Route for user registration
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(email=form.email.data, name=form.name.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('You have successfully registered', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists', 'warning')
    return render_template('register.html', form=form)

# Route for user login
@main.route('/login', methods=['GET', 'POST'])
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

# Route for admin user registration
@main.route('/admin/register', methods=['GET', 'POST'])
@login_required
def admin_register_user():
    if current_user.role != 'admin':
        flash('Access restricted to admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            new_user = User(email=form.email.data, name=form.name.data, password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash('New user successfully registered!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists!', 'danger')
    return render_template('admin_register.html', form=form)

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
