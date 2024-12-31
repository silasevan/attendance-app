import unittest
from flask import Flask
from flask_testing import TestCase
from flask_login import login_user, current_user
from app import create_app, db
from app.models import User, AttendanceRecord
from app.routes import main


class TestRoutes(unittest.TestCase):
    
    def create_app(self):
        app = create_app(config_object="testing")  # Use the testing config
        app.register_blueprint(main)  # Register blueprint to app
        return app

    def setUp(self):
        # Create app and use a test configuration (if needed)
        self.app = create_app('testing')  # Adjust based on your app's config
        self.client = self.app.test_client()

        # Push the app context
        with self.app.app_context():
            # Set up the database
            db.create_all()

    def tearDown(self):
        """ Rollback the database after each test. """
        db.session.remove()
        db.drop_all()

    def test_register_user(self):
        """ Test the registration route. """
        response = self.client.post('/register', data=dict(
            email='newuser@example.com',
            name='New User',
            password='password123',
            role='user'
        ), follow_redirects=True)
        
        # Assert successful registration and redirect to login page
        self.assertIn(b'Successfully registered as a user!', response.data)
        self.assertRedirects(response, '/login')

    def test_login_user(self):
        """ Test user login route. """
        response = self.client.post('/login', data=dict(
            email='testuser@example.com',
            password='password123'
        ), follow_redirects=True)

        # Assert login successful
        self.assertIn(b'You have successfully logged in', response.data)
        self.assertRedirects(response, '/dashboard')

    def test_sign_in(self):
        """ Test user sign-in route within company location. """
        response = self.client.post('/sign-in', data=dict(
            latitude=7.130400,
            longitude=3.362200
        ), follow_redirects=True)

        # Check for successful sign-in
        self.assertIn(b'Sign-in successful!', response.data)

    def test_sign_out(self):
        """ Test user sign-out route after sign-in. """
        # First, simulate sign-in
        self.client.post('/sign-in', data=dict(
            latitude=7.130400,
            longitude=3.362200
        ))

        # Now, test sign-out
        response = self.client.post('/sign-out', data=dict(
            latitude=7.130400,
            longitude=3.362200
        ), follow_redirects=True)

        self.assertIn(b'Sign-out successful!', response.data)

    def test_admin_dashboard_access(self):
        """ Test access to the admin dashboard for non-admin user. """
        # Simulate login for non-admin user
        login_user(self.test_user)
        
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access restricted to admins only.', response.data)

    def test_admin_attendance_records(self):
        """ Test the admin can access attendance records. """
        # Set up an admin user
        admin_user = User(email="admin@example.com", name="Admin User", password="adminpass", role="admin")
        db.session.add(admin_user)
        db.session.commit()

        # Simulate admin login
        login_user(admin_user)

        # Add an attendance record for the user
        attendance = AttendanceRecord(user_id=self.test_user.id, date="2024-12-31", geo_location="7.130400,3.362200")
        db.session.add(attendance)
        db.session.commit()

        # Test admin access to attendance records
        response = self.client.get('/admin/attendance-records', follow_redirects=True)
        self.assertIn(b'admin@example.com', response.data)

    def test_password_reset_request(self):
        """ Test password reset request functionality. """
        response = self.client.post('/reset-password-request', data=dict(
            email='testuser@example.com'
        ), follow_redirects=True)
        
        self.assertIn(b'Check your email for the instructions to reset your password.', response.data)

    def test_password_reset(self):
        """ Test password reset functionality. """
        # Generate a token for reset (mocking real functionality)
        token = 'valid_reset_token'
        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)

        # Assert password reset page is loaded
        self.assertIn(b'Your password has been updated!', response.data)

if __name__ == '__main__':
    unittest.main()
