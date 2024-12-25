from . import db

from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from time import time
import jwt
from datetime import datetime, timedelta


bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Rename column to avoid conflict
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return f'<User {self.name}>'

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_reset_password_token(self, expires_in=600):
        """Generate a reset token for password reset."""
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256'  # Use current_app
        )

    @staticmethod
    def verify_reset_password_token(token):
        """Verify the reset password token and return the user if valid."""
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception:
            return None
        return User.query.get(id)
    
    

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.today().date)
    sign_in_time = db.Column(db.Time)
    sign_out_time = db.Column(db.Time)
    geo_location = db.Column(db.String(100), nullable=False)

    user = db.relationship('User', backref='attendance_records')

    def __repr__(self):
        return f'<AttendanceRecord {self.user_id} - {self.date}>'





