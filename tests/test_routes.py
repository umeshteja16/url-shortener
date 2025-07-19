import pytest
import json
from app import create_app, db
from app.models import User, URL, Counter

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['REDIS_URL'] = ''  # Disable Redis for tests
    
    with app.app_context():
        db.create_all()
        
        # Create initial counter
        counter = Counter(name='url_counter', value=100000000000)
        db.session.add(counter)
        db.session.commit()
        
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_user(app):
    """Create a sample user"""
    with app.app_context():
        user = User(email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user

class TestRoutes:
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'URL Shortener' in response.data
    
    def test_create_short_url(self, client):
        """Test URL shortening"""
        data = {'url': 'https://www.google.com'}
        
        response = client.post('/api/shorten', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'short_url' in result
        assert 'short_code' in result
        assert result['original_url'] == 'https://www.google.com'
    
    def test_create_custom_url(self, client, sample_user):
        """Test custom URL creation"""
        data = {
            'url': 'https://www.google.com',
            'custom_code': 'google',
            'api_key': sample_user.api_key
        }
        
        response = client.post('/api/shorten',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['short_code'] == 'google'
    
    def test_url_redirect(self, client):
        """Test URL redirection"""
        # First create a short URL
        data = {'url': 'https://www.google.com'}
        response = client.post('/api/shorten',
                             data=json.dumps(data),
                             content_type='application/json')
        
        result = json.loads(response.data)
        short_code = result['short_code']
        
        # Test redirection
        response = client.get(f'/{short_code}')
        assert response.status_code == 302
        assert response.location == 'https://www.google.com'
    
    def test_invalid_url(self, client):
        """Test invalid URL handling"""
        data = {'url': 'not-a-valid-url'}
        
        response = client.post('/api/shorten',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_user_creation(self, client):
        """Test user creation"""
        data = {'email': 'newuser@example.com'}
        
        response = client.post('/api/user/create',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'api_key' in result
        assert result['email'] == 'newuser@example.com'
    
    def test_duplicate_custom_code(self, client, sample_user):
        """Test duplicate custom code rejection"""
        data = {
            'url': 'https://www.google.com',
            'custom_code': 'test',
            'api_key': sample_user.api_key
        }
        
        # First request should succeed
        response = client.post('/api/shorten',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Second request with same code should fail
        response = client.post('/api/shorten',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 409
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['status'] == 'healthy'
    
    def test_not_found_url(self, client):
        """Test accessing non-existent short code"""
        response = client.get('/nonexistent')
        assert response.status_code == 404