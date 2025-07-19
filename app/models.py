from app import db
from datetime import datetime, timedelta
import secrets
import string

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    urls = db.relationship('URL', backref='user', lazy=True)
    
    def __init__(self, email=None):
        self.email = email
        self.api_key = self.generate_api_key()
    
    def generate_api_key(self):
        """Generate secure API key"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

class URL(db.Model):
    __tablename__ = 'urls'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    click_count = db.Column(db.Integer, default=0)
    is_custom = db.Column(db.Boolean, default=False)
    
    # Analytics relationship
    analytics = db.relationship('Analytics', backref='url', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<URL {self.short_code}>'
    
    def is_expired(self):
        """Check if URL has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'click_count': self.click_count,
            'is_custom': self.is_custom
        }

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    url_id = db.Column(db.BigInteger, db.ForeignKey('urls.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)
    country = db.Column(db.String(10))
    
    def __repr__(self):
        return f'<Analytics {self.id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'referrer': self.referrer,
            'country': self.country
        }

class Counter(db.Model):
    """Counter for distributed ID generation"""
    __tablename__ = 'counters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.BigInteger, default=100000000000)  # Start from large number
    
    @classmethod
    def get_next_id(cls):
        """Get next counter value for URL generation"""
        counter = cls.query.filter_by(name='url_counter').first()
        if not counter:
            counter = cls(name='url_counter', value=100000000000)
            db.session.add(counter)
        
        counter.value += 1
        db.session.commit()
        return counter.value