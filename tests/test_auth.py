import pytest
from app import create_app
from routes.auth import get_db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():  # Set up application context
            yield client

def test_signup(client):
    # Clear the test database
    db = get_db()
    db.users.delete_many({})  # Clear all users from the test database

    # Perform the signup request
    response = client.post('/signup', data={
        'email': 'testuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'mobile': '+919328823998'
    })

    # Assertions
    assert response.status_code == 302  # Redirect to OTP verification
    assert response.status_code == 302

def test_verify_email_otp(client):
    with client.session_transaction() as session:
        session['email_otp'] = '123456'
        session['user_email'] = 'testuser@example.com'

    response = client.post('/verify_email_otp', data={'otp': '123456'})
    assert response.status_code == 302  # Redirect to the next step
    assert response.headers['Location'] == '/verify_mobile'  # Check redirection URL