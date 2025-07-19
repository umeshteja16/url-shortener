import string
import validators
from urllib.parse import urlparse

class Base62Encoder:
    """Base62 encoding for URL shortening"""
    
    ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
    BASE = len(ALPHABET)
    
    @classmethod
    def encode(cls, num):
        """Convert number to base62 string"""
        if num == 0:
            return cls.ALPHABET[0]
        
        result = []
        while num > 0:
            result.append(cls.ALPHABET[num % cls.BASE])
            num //= cls.BASE
        
        # Pad to 7 characters for consistency
        encoded = ''.join(reversed(result))
        return encoded.zfill(7)
    
    @classmethod
    def decode(cls, string):
        """Convert base62 string to number"""
        num = 0
        for char in string:
            num = num * cls.BASE + cls.ALPHABET.index(char)
        return num

class URLValidator:
    """URL validation utilities"""
    
    ALLOWED_SCHEMES = ['http', 'https']
    BLOCKED_DOMAINS = [
        'localhost', '127.0.0.1', '0.0.0.0'
    ]
    
    @classmethod
    def is_valid_url(cls, url):
        """Validate URL format and safety"""
        if not validators.url(url):
            return False, "Invalid URL format"
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                return False, "Only HTTP and HTTPS URLs are allowed"
            
            # Check for blocked domains
            domain = parsed.netloc.lower()
            if any(blocked in domain for blocked in cls.BLOCKED_DOMAINS):
                return False, "Domain is not allowed"
            
            return True, "Valid URL"
            
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
    
    @classmethod
    def is_valid_custom_code(cls, code):
        """Validate custom short code"""
        if not code:
            return False, "Custom code cannot be empty"
        
        if len(code) < 3 or len(code) > 16:
            return False, "Custom code must be between 3 and 16 characters"
        
        # Only allow alphanumeric and some special characters
        allowed_chars = string.ascii_letters + string.digits + '-_'
        if not all(c in allowed_chars for c in code):
            return False, "Custom code can only contain letters, numbers, hyphens, and underscores"
        
        return True, "Valid custom code"

class CacheManager:
    """Redis cache management"""
    
    def __init__(self, redis_client, ttl=3600):
        self.redis = redis_client
        self.ttl = ttl
    
    def get_url(self, short_code):
        """Get URL from cache"""
        if not self.redis:
            return None
        
        try:
            cached = self.redis.get(f"url:{short_code}")
            return cached.decode('utf-8') if cached else None
        except:
            return None
    
    def set_url(self, short_code, original_url):
        """Cache URL mapping"""
        if not self.redis:
            return
        
        try:
            self.redis.setex(f"url:{short_code}", self.ttl, original_url)
        except:
            pass
    
    def delete_url(self, short_code):
        """Remove URL from cache"""
        if not self.redis:
            return
        
        try:
            self.redis.delete(f"url:{short_code}")
        except:
            pass