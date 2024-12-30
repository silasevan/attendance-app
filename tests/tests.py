import unittest
from attendance import create_app, db
from flask_login import current_user

class TestRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        # Initialize the database
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        # Clean up database after each test
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Attendance App', response.data)

    def test_register_route(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_register_post(self):
        response = self.client.post('/register', data={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'role': 'user'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have successfully registered', response.data)

    def test_login_route(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_custom_404_error(self):
        response = self.client.get('/nonexistent_route')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Oops! The page you're looking for doesn't exist.", response.data)

if __name__ == '__main__':
    unittest.main()
