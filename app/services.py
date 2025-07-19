from app import db
from app.models import URL, Analytics, Counter, User
from app.utils import Base62Encoder, URLValidator, CacheManager
from datetime import datetime, timedelta
from flask import current_app

class URLShortenerService:
    """Core URL shortening business logic"""
    
    def __init__(self):
        self.cache = CacheManager(current_app.redis if hasattr(current_app, 'redis') else None)
    
    def create_short_url(self, original_url, api_key=None, custom_code=None, expires_in_days=None):
        """Create a shortened URL"""
        
        # Validate original URL
        is_valid, message = URLValidator.is_valid_url(original_url)
        if not is_valid:
            return {'error': message}, 400
        
        # Get user if API key provided
        user = None
        if api_key:
            user = User.query.filter_by(api_key=api_key, is_active=True).first()
            if not user:
                return {'error': 'Invalid API key'}, 401
        
        # Handle custom code
        if custom_code:
            is_valid_custom, message = URLValidator.is_valid_custom_code(custom_code)
            if not is_valid_custom:
                return {'error': message}, 400
            
            # Check if custom code exists
            existing = URL.query.filter_by(short_code=custom_code, is_active=True).first()
            if existing:
                return {'error': 'Custom code already exists'}, 409
            
            short_code = custom_code
            is_custom = True
        else:
            # Generate unique short code
            counter_id = Counter.get_next_id()
            short_code = Base62Encoder.encode(counter_id)
            is_custom = False
        
        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create URL record
        url_record = URL(
            original_url=original_url,
            short_code=short_code,
            user_id=user.id if user else None,
            expires_at=expires_at,
            is_custom=is_custom
        )
        
        try:
            db.session.add(url_record)
            db.session.commit()
            
            # Cache the mapping
            self.cache.set_url(short_code, original_url)
            
            return {
                'short_url': f"{current_app.config['BASE_URL']}/{short_code}",
                'short_code': short_code,
                'original_url': original_url,
                'created_at': url_record.created_at.isoformat(),
                'expires_at': url_record.expires_at.isoformat() if url_record.expires_at else None
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': 'Failed to create short URL'}, 500
    
    def get_original_url(self, short_code, track_analytics=True, request_data=None):
        """Get original URL and track analytics"""
        
        # Try cache first
        cached_url = self.cache.get_url(short_code)
        if cached_url and not track_analytics:
            return {'original_url': cached_url}, 200
        
        # Query database
        url_record = URL.query.filter_by(short_code=short_code, is_active=True).first()
        
        if not url_record:
            return {'error': 'Short URL not found'}, 404
        
        # Check if expired
        if url_record.is_expired():
            return {'error': 'Short URL has expired'}, 410
        
        # Track analytics
        if track_analytics and request_data:
            self._track_analytics(url_record, request_data)
        
        # Update click count
        url_record.click_count += 1
        db.session.commit()
        
        # Update cache
        self.cache.set_url(short_code, url_record.original_url)
        
        return {
            'original_url': url_record.original_url,
            'click_count': url_record.click_count
        }, 200
    
    def _track_analytics(self, url_record, request_data):
        """Track analytics data"""
        try:
            analytics = Analytics(
                url_id=url_record.id,
                ip_address=request_data.get('ip_address'),
                user_agent=request_data.get('user_agent'),
                referrer=request_data.get('referrer')
            )
            db.session.add(analytics)
            db.session.commit()
        except Exception as e:
            print(f"Analytics tracking error: {e}")
    
    def get_url_stats(self, short_code, api_key=None):
        """Get URL statistics"""
        
        url_record = URL.query.filter_by(short_code=short_code, is_active=True).first()
        if not url_record:
            return {'error': 'Short URL not found'}, 404
        
        # Check authorization
        if api_key:
            user = User.query.filter_by(api_key=api_key).first()
            if not user or url_record.user_id != user.id:
                return {'error': 'Unauthorized'}, 403
        
        # Get analytics data
        analytics = Analytics.query.filter_by(url_id=url_record.id).all()
        
        # Aggregate analytics
        daily_clicks = {}
        total_clicks = len(analytics)
        
        for click in analytics:
            date_key = click.timestamp.strftime('%Y-%m-%d')
            daily_clicks[date_key] = daily_clicks.get(date_key, 0) + 1
        
        return {
            'url_data': url_record.to_dict(),
            'total_clicks': total_clicks,
            'daily_clicks': daily_clicks,
            'recent_clicks': [a.to_dict() for a in analytics[-10:]]
        }, 200
    
    def get_user_urls(self, api_key, limit=50, offset=0):
        """Get URLs created by user"""
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return {'error': 'Invalid API key'}, 401
        
        urls = URL.query.filter_by(user_id=user.id, is_active=True)\
                       .order_by(URL.created_at.desc())\
                       .limit(limit).offset(offset).all()
        
        return {
            'urls': [url.to_dict() for url in urls],
            'total': URL.query.filter_by(user_id=user.id, is_active=True).count()
        }, 200
    
    def delete_url(self, short_code, api_key):
        """Delete a URL"""
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return {'error': 'Invalid API key'}, 401
        
        url_record = URL.query.filter_by(short_code=short_code, user_id=user.id, is_active=True).first()
        if not url_record:
            return {'error': 'URL not found or unauthorized'}, 404
        
        url_record.is_active = False
        db.session.commit()
        
        # Remove from cache
        self.cache.delete_url(short_code)
        
        return {'message': 'URL deleted successfully'}, 200

class UserService:
    """User management service"""
    
    @staticmethod
    def create_user(email=None):
        """Create new user and return API key"""
        
        # Check if email already exists
        if email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                return {'error': 'Email already registered'}, 409
        
        user = User(email=email)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            return {
                'api_key': user.api_key,
                'email': user.email,
                'created_at': user.created_at.isoformat()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': 'Failed to create user'}, 500
    
    @staticmethod
    def get_user_info(api_key):
        """Get user information"""
        
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return {'error': 'Invalid API key'}, 401
        
        url_count = URL.query.filter_by(user_id=user.id, is_active=True).count()
        total_clicks = db.session.query(db.func.sum(URL.click_count))\
                                .filter_by(user_id=user.id, is_active=True).scalar() or 0
        
        return {
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'total_urls': url_count,
            'total_clicks': total_clicks
        }, 200