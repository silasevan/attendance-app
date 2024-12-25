from flask import Blueprint,render_template, redirect, url_for, flash

from flask_login import login_required, current_user,login_user,logout_user
from .models import User
from .forms import LoginForm, RegistrationForm,PasswordResetRequestForm
from sqlalchemy.exc import IntegrityError
from . import db
from geopy.distance import geodesic
from datetime import datetime
from flask import request
from .models import AttendanceRecord
from datetime import datetime, time
from .utils import send_reset_email




main = Blueprint('main', __name__)

COMPANY_LOCATION = (7.130402
                    , 3.362196)  # Example: Lagos, Nigeria
SIGN_IN_DEADLINE = time(8, 0)  # 9:00 AM
SIGN_OUT_START_TIME = time(5, 0)  # 5:00 PM

def is_within_company_location(user_lat, user_lon):
    user_location = (user_lat, user_lon)
    distance = geodesic(COMPANY_LOCATION, user_location).meters
    print(f"User location: {user_location}, Company location: {COMPANY_LOCATION}, Distance: {distance} meters")
    return distance <= 100  # Allow sign-in within 100 meters

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data,
                name=form.name.data,
                password=form.password.data
            )
            db.session.add(user)
            db.session.commit()
            flash('You have successfully registered', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists', 'warning')
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            flash('You have successfully logged in', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.login'))




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
            record = AttendanceRecord(
                user_id=current_user.id,
                date=today,
                sign_in_time=datetime.now().time(),
                geo_location=f"{user_lat},{user_lon}"
            )
            db.session.add(record)
            db.session.commit()
            flash('Sign-in successful!', 'success')
        else:
            flash('Already signed in for today.', 'info')
    else:
        flash('You must be within the company location to sign in.', 'danger')
    return redirect(url_for('main.dashboard'))

@main.route('/sign-out', methods=['POST'])
@login_required
def sign_out():
    user_lat = request.form.get('latitude', type=float)
    user_lon = request.form.get('longitude', type=float)
    print(f"Received coordinates: Latitude: {user_lat}, Longitude: {user_lon}")
    if user_lat is None or user_lon is None:
        flash('Unable to retrieve location data. Please ensure location services are enabled.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    
    if is_within_company_location(user_lat, user_lon):
        today = datetime.today().date()
        record = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()
        if record and not record.sign_out_time:
            record.sign_out_time = datetime.now().time()
            db.session.commit()
            flash('Sign-out successful!', 'success')
        else:
            flash('No sign-in record found or already signed out.', 'info')
    else:
        flash('You must be within the company location to sign out.', 'danger')
    return redirect(url_for('main.dashboard'))




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



@main.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_records = AttendanceRecord.query.filter_by(user_id=current_user.id).order_by(AttendanceRecord.date.desc()).all()
    today = datetime.today().date()
    record_today = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()
    
    late_status = None
    if record_today and record_today.sign_in_time:
        late_status = record_today.sign_in_time > SIGN_IN_DEADLINE

    return render_template(
        'dashboard.html',
        records=user_records,
        record_today=record_today,
        late_status=late_status,
        current_time=datetime.now().time(),
        SIGN_OUT_START_TIME=SIGN_OUT_START_TIME
    )





@main.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access restricted to admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    all_records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).all()
    return render_template('admin_dashboard.html', records=all_records)





@main.route('/admin/register', methods=['GET', 'POST'])
@login_required
def admin_register_user():
    if not current_user.is_admin():
        flash('Access restricted to admins only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            new_user = User(
                email=form.email.data,
                name=form.name.data,
                password=form.password.data
            )
            db.session.add(new_user)
            db.session.commit()
            flash('New user successfully registered!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists!', 'danger')
    return render_template('admin_register.html', form=form)



@main.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)  # Implement this function to send email
        flash('Check your email for the instructions to reset your password.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html', form=form)


@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_reset_token(token)  # Implement token verification
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


