from flask import current_app
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from datetime import datetime, timedelta
import jwt
from sqlalchemy import Boolean
from . import db
from time import time

bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_admin =db.Column(db.Boolean, default=False) 

    def __repr__(self):
        return f'<User {self.name}>'

    @property
    def password(self):
        """ Prevent password from being accessed directly. """
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        """ Hash the password before saving it. """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """ Check if the provided password matches the hashed one. """
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """ Check if the user has admin role. """
        return self.role == 'admin'

    def get_reset_password_token(self, expires_in=600):
        """ Generate a token to reset the user's password. """
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        """ Verify the reset password token and return the user if valid. """
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return User.query.get(user_id)


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.today().date)
    sign_in_time = db.Column(db.Time)
    sign_out_time = db.Column(db.Time)
    geo_location = db.Column(db.String(100), nullable=False)
    auto_signed_out = db.Column(Boolean, default=False)

    user = db.relationship('User', backref='attendance_records')

    def __repr__(self):
        return f'<AttendanceRecord {self.user_id} - {self.date}>'

