import pytest
from app.utils import Base62Encoder, URLValidator

class TestBase62Encoder:
    def test_encode_decode(self):
        """Test encoding and decoding"""
        test_numbers = [0, 1, 62, 100000000000, 999999999999]
        
        for num in test_numbers:
            encoded = Base62Encoder.encode(num)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == num
    
    def test_encode_length(self):
        """Test that encoded strings are 7 characters"""
        encoded = Base62Encoder.encode(100000000000)
        assert len(encoded) == 7
    
    def test_encode_zero(self):
        """Test encoding zero"""
        encoded = Base62Encoder.encode(0)
        assert encoded == "0000000"
        assert Base62Encoder.decode(encoded) == 0

class TestURLValidator:
    def test_valid_urls(self):
        """Test valid URL validation"""
        valid_urls = [
            "https://www.google.com",
            "http://example.com",
            "https://subdomain.example.com/path?query=value",
            "https://example.com:8080/path"
        ]
        
        for url in valid_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL {url} should be valid: {message}"
    
    def test_invalid_urls(self):
        """Test invalid URL validation"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "https://localhost",
            "",
            "javascript:alert('xss')"
        ]
        
        for url in invalid_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert not is_valid, f"URL {url} should be invalid"
    
    def test_custom_code_validation(self):
        """Test custom code validation"""
        valid_codes = [
            "abc123", 
            "my-url", 
            "test_code",
            "ABC",
            "123"
        ]
        
        for code in valid_codes:
            is_valid, message = URLValidator.is_valid_custom_code(code)
            assert is_valid, f"Code {code} should be valid: {message}"
        
        invalid_codes = [
            "ab",           # Too short
            "a" * 20,       # Too long
            "invalid@code", # Invalid character
            "",             # Empty
            "code with spaces",  # Spaces
            "code!",        # Special characters
        ]
        
        for code in invalid_codes:
            is_valid, message = URLValidator.is_valid_custom_code(code)
            assert not is_valid, f"Code {code} should be invalid"
    
    def test_blocked_domains(self):
        """Test blocked domain validation"""
        blocked_urls = [
            "http://localhost/test",
            "https://127.0.0.1/test",
            "http://0.0.0.0/test"
        ]
        
        for url in blocked_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert not is_valid, f"URL {url} should be blocked"