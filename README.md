# Attendance App

This project is a web-based attendance management system. It allows users to register, authenticate, and sign in/out when within the company's geo-location. The app records the date and time of sign-ins and sign-outs and displays these records on user dashboards. Additionally, HR administrators can view and manage all attendance records.

## Features

- **User Authentication**: Secure user registration and login.
- **Role-Based Access Control**:
  - Users can view their attendance records.
  - HR administrators can view all attendance records.
- **Geo-Location Verification**: Ensures users can only sign in/out when within the company's specified location.
- **Database Management**: Migrated from SQLite to MySQL using SQLAlchemy.
- **Responsive Design**: Built with Flask and Bootstrap for seamless access on various devices.

## Prerequisites

- Python 3.10+
- MySQL 5.7+
- Flask and Flask extensions:
  - Flask-SQLAlchemy
  - Flask-Migrate
  - Flask-Login
  - Flask-WTF
- Additional Python packages:
  - PyMySQL
  - cryptography

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/silasevan/attendance-app.git
   cd attendance-app
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and configure the following:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@localhost/attendance_db
   ```

5. **Initialize the Database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

6. **Run the Application**:
   ```bash
   flask run
   ```

   Visit `http://127.0.0.1:5000` in your browser.

## Usage

1. **Registration**:
   - Users can register with their name, email, and password.
   - Passwords must meet the security requirements (e.g., at least 8 characters with uppercase, lowercase, numeric, and special characters).

2. **Login**:
   - Users can log in with their email and password.

3. **Attendance**:
   - Users can sign in/out when within the company's geo-location.
   - Attendance records are displayed on the user's dashboard.

4. **Admin Dashboard**:
   - HR administrators can view and manage attendance records for all users.

## Project Structure

```
attendance-app/
├── app/
│   ├── templates/       # HTML templates
│   ├── static/          # Static files (CSS, JS, images)
│   ├── models.py        # Database models
│   ├── routes.py        # Application routes
│   └── __init__.py      # App factory
├── migrations/          # Database migrations
├── requirements.txt     # Python dependencies
├── run.py               # Entry point for the application
└── README.md            # Project documentation
```

## Known Issues and Future Improvements

- **Geo-Location Feature**:
  - Improve accuracy and efficiency for devices with limited GPS capabilities.
- **Notification System**:
  - Notify users and HR admins of missed sign-ins or irregularities.
- **Reports**:
  - Generate attendance reports for specific periods.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

Happy coding!
