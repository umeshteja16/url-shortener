import pytest
import os
from app.utils import Base62Encoder, URLValidator, CacheManager
from unittest.mock import Mock, MagicMock

class TestBase62Encoder:
    def test_encode_decode_basic(self):
        """Test basic encoding and decoding"""
        test_numbers = [1, 62, 100000000000, 999999999999]
        
        for num in test_numbers:
            encoded = Base62Encoder.encode(num)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == num, f"Failed for number {num}"
    
    def test_encode_length_padding(self):
        """Test that encoded strings are padded to 7 characters for large numbers"""
        test_numbers = [100000000000, 100000000001, 999999999999]
        
        for num in test_numbers:
            encoded = Base62Encoder.encode(num)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == num
            assert len(encoded) == 7, f"Encoded {num} as {encoded} with length {len(encoded)}"
    
    def test_encode_zero(self):
        """Test encoding zero"""
        encoded = Base62Encoder.encode(0)
        assert encoded == "0"  # Zero should encode to single '0', not padded
        assert Base62Encoder.decode(encoded) == 0
    
    def test_encode_small_numbers(self):
        """Test encoding small numbers (no padding for small values)"""
        for i in range(1, 100):
            encoded = Base62Encoder.encode(i)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == i
            # Small numbers don't get padded to 7 characters
            assert len(encoded) >= 1
    
    def test_encode_large_numbers(self):
        """Test encoding large numbers within range"""
        large_numbers = [
            100000000000,  # Starting counter value
            200000000000,
            500000000000,
            999999999999
        ]
        
        for num in large_numbers:
            encoded = Base62Encoder.encode(num)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == num
            assert len(encoded) == 7  # Large numbers get padded
    
    def test_alphabet_coverage(self):
        """Test that all alphabet characters can be used"""
        alphabet = Base62Encoder.ALPHABET
        assert len(alphabet) == 62
        assert alphabet == "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        # Test a number that uses various characters
        test_num = 12345678901234
        encoded = Base62Encoder.encode(test_num)
        decoded = Base62Encoder.decode(encoded)
        assert decoded == test_num
    
    def test_deterministic_encoding(self):
        """Test that encoding is deterministic"""
        test_num = 100000000000
        encoded1 = Base62Encoder.encode(test_num)
        encoded2 = Base62Encoder.encode(test_num)
        assert encoded1 == encoded2

class TestURLValidator:
    def test_valid_urls(self):
        """Test valid URL validation"""
        valid_urls = [
            "https://www.google.com",
            "http://example.com",
            "https://subdomain.example.com/path?query=value",
            "https://example.com:8080/path",
            "https://www.example.com/path/to/resource",
            "https://example.com/path?param1=value1&param2=value2",
            "https://www.example-site.com",
            "https://example.co.uk",
            "https://api.example.com/v1/resource"
        ]
        
        for url in valid_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL {url} should be valid but got error: {message}"
    
    def test_invalid_urls(self):
        """Test invalid URL validation"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Wrong scheme
            "",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "http://",  # Incomplete URL
            "https://",  # Incomplete URL
            "www.example.com",  # Missing scheme
            "example.com",  # Missing scheme
            "http:/example.com",  # Malformed
            "https:///example.com"  # Malformed
        ]
        
        for url in invalid_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert not is_valid, f"URL {url} should be invalid but was accepted"
    
    def test_blocked_domains(self):
        """Test blocked domain validation"""
        blocked_urls = [
            "http://localhost/test",
            "https://localhost:3000/api",
            "https://127.0.0.1/test",
            "http://127.0.0.1:8080/path",
            "http://0.0.0.0/test",
            "https://0.0.0.0:5000/api"
        ]
        
        for url in blocked_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert not is_valid, f"URL {url} should be blocked but was accepted"
            # The actual error message might be "Invalid URL format" or "Domain is not allowed"
            assert "invalid" in message.lower() or "not allowed" in message.lower()
    
    def test_custom_code_validation_valid(self):
        """Test valid custom code validation"""
        valid_codes = [
            "abc123", 
            "my-url", 
            "test_code",
            "ABC",
            "123",
            "a1b2c3",
            "short",
            "portfolio",
            "github-link",
            "my_project",
            "Test_Code_123"
        ]
        
        for code in valid_codes:
            is_valid, message = URLValidator.is_valid_custom_code(code)
            assert is_valid, f"Code '{code}' should be valid but got error: {message}"
    
    def test_custom_code_validation_invalid(self):
        """Test invalid custom code validation"""
        invalid_codes = [
            "ab",                    # Too short (< 3 chars)
            "a" * 20,               # Too long (> 16 chars)
            "invalid@code",         # Invalid character (@)
            "",                     # Empty
            "code with spaces",     # Spaces not allowed
            "code!",                # Exclamation mark
            "code#hash",            # Hash symbol
            "code%percent",         # Percent symbol
            "code.dot",             # Dot not allowed
            "code+plus",            # Plus not allowed
            "code=equals",          # Equals not allowed
        ]
        
        for code in invalid_codes:
            is_valid, message = URLValidator.is_valid_custom_code(code)
            assert not is_valid, f"Code '{code}' should be invalid but was accepted"
    
    def test_custom_code_edge_cases(self):
        """Test edge cases for custom code validation"""
        # Test minimum length (3 characters)
        assert URLValidator.is_valid_custom_code("abc")[0] == True
        assert URLValidator.is_valid_custom_code("ab")[0] == False
        
        # Test maximum length (16 characters)
        assert URLValidator.is_valid_custom_code("a" * 16)[0] == True
        assert URLValidator.is_valid_custom_code("a" * 17)[0] == False
        
        # Test allowed special characters
        assert URLValidator.is_valid_custom_code("test-code")[0] == True
        assert URLValidator.is_valid_custom_code("test_code")[0] == True
        
        # Test mixed case
        assert URLValidator.is_valid_custom_code("TestCode")[0] == True
        assert URLValidator.is_valid_custom_code("TEST_code_123")[0] == True
    
    def test_url_scheme_validation(self):
        """Test URL scheme validation"""
        # Test allowed schemes
        allowed_schemes = [
            "http://example.com",
            "https://example.com"
        ]
        
        for url in allowed_schemes:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL with allowed scheme {url} should be valid"
        
        # Test disallowed schemes
        disallowed_schemes = [
            "ftp://example.com",
            "file://example.com",
        ]
        
        for url in disallowed_schemes:
            is_valid, message = URLValidator.is_valid_url(url)
            assert not is_valid, f"URL with disallowed scheme {url} should be invalid"

class TestCacheManager:
    def test_cache_manager_without_redis(self):
        """Test cache manager when Redis is not available"""
        cache = CacheManager(None, ttl=3600)
        
        # Should handle gracefully when Redis is None
        assert cache.get_url("test") is None
        cache.set_url("test", "https://example.com")  # Should not raise error
        cache.delete_url("test")  # Should not raise error
    
    def test_cache_manager_with_mock_redis(self):
        """Test cache manager with mocked Redis"""
        mock_redis = Mock()
        mock_redis.get.return_value = b"https://example.com"
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        
        cache = CacheManager(mock_redis, ttl=3600)
        
        # Test get_url
        result = cache.get_url("test123")
        assert result == "https://example.com"
        mock_redis.get.assert_called_with("url:test123")
        
        # Test set_url
        cache.set_url("test123", "https://example.com")
        mock_redis.setex.assert_called_with("url:test123", 3600, "https://example.com")
        
        # Test delete_url
        cache.delete_url("test123")
        mock_redis.delete.assert_called_with("url:test123")
    
    def test_cache_manager_redis_failure(self):
        """Test cache manager when Redis operations fail"""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.setex.side_effect = Exception("Redis connection failed")
        mock_redis.delete.side_effect = Exception("Redis connection failed")
        
        cache = CacheManager(mock_redis, ttl=3600)
        
        # Should handle Redis failures gracefully
        assert cache.get_url("test") is None
        cache.set_url("test", "https://example.com")  # Should not raise
        cache.delete_url("test")  # Should not raise
    
    def test_cache_manager_ttl_configuration(self):
        """Test cache manager TTL configuration"""
        mock_redis = Mock()
        
        # Test default TTL
        cache = CacheManager(mock_redis)
        cache.set_url("test", "https://example.com")
        mock_redis.setex.assert_called_with("url:test", 3600, "https://example.com")
        
        # Test custom TTL
        cache = CacheManager(mock_redis, ttl=7200)
        cache.set_url("test", "https://example.com")
        mock_redis.setex.assert_called_with("url:test", 7200, "https://example.com")
    
    def test_cache_key_formatting(self):
        """Test that cache keys are formatted correctly"""
        mock_redis = Mock()
        cache = CacheManager(mock_redis)
        
        # Test URL cache key format
        cache.get_url("abc123")
        mock_redis.get.assert_called_with("url:abc123")

class TestURLValidatorEdgeCases:
    def test_url_with_query_parameters(self):
        """Test URLs with various query parameters"""
        urls_with_params = [
            "https://example.com?param=value",
            "https://example.com?param1=value1&param2=value2",
            "https://example.com?search=hello%20world",
            "https://example.com?id=123&token=abc&redirect=https%3A%2F%2Fother.com"
        ]
        
        for url in urls_with_params:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL with query params {url} should be valid: {message}"
    
    def test_url_with_fragments(self):
        """Test URLs with fragments"""
        urls_with_fragments = [
            "https://example.com#section1",
            "https://example.com/page#top",
            "https://example.com/docs#api-reference"
        ]
        
        for url in urls_with_fragments:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL with fragment {url} should be valid: {message}"
    
    def test_url_with_ports(self):
        """Test URLs with different ports"""
        urls_with_ports = [
            "https://example.com:443/path",
            "http://example.com:80/path",
            "https://api.example.com:8443/v1",
            "http://dev.example.com:3000/api"
        ]
        
        for url in urls_with_ports:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"URL with port {url} should be valid: {message}"
    
    def test_url_length_limits(self):
        """Test very long URLs"""
        base_url = "https://example.com/"
        
        # Test reasonable length URL
        normal_url = base_url + "a" * 100
        is_valid, message = URLValidator.is_valid_url(normal_url)
        assert is_valid, f"Normal length URL should be valid: {message}"
        
        # Test very long URL (2000+ characters)
        very_long_url = base_url + "a" * 2000
        is_valid, message = URLValidator.is_valid_url(very_long_url)
        # This should still be valid from URL format perspective
        assert is_valid, f"Very long URL should be valid from format perspective: {message}"

class TestBase62EncoderEdgeCases:
    def test_encode_decode_boundary_values(self):
        """Test encoding/decoding at boundary values"""
        boundary_values = [
            1,                    # Minimum non-zero value
            61,                   # Maximum single character value
            62,                   # First two-character value
            62**2 - 1,           # Maximum two-character value
            62**2,               # First three-character value
            100000000000,        # Starting counter value
        ]
        
        for value in boundary_values:
            encoded = Base62Encoder.encode(value)
            decoded = Base62Encoder.decode(encoded)
            assert decoded == value, f"Boundary value {value} failed encode/decode"
            
            # Only large numbers (>= 100000000000) get padded to 7 characters
            if value >= 100000000000:
                assert len(encoded) == 7, f"Large number {value} should be 7 chars, got {len(encoded)}"
    
    def test_encode_preserves_order(self):
        """Test that encoding preserves numerical order for similar values"""
        values = [100000000000, 100000000001, 100000000002, 100000000010, 100000000100]
        encoded_values = [Base62Encoder.encode(v) for v in values]
        
        # When compared as strings, encoded values should maintain order
        # for values that are close together
        for i in range(len(encoded_values) - 1):
            assert encoded_values[i] < encoded_values[i + 1], \
                f"Order not preserved: {values[i]} -> {encoded_values[i]}, {values[i+1]} -> {encoded_values[i+1]}"
    
    def test_encode_character_distribution(self):
        """Test that encoding uses characters from alphabet"""
        # Test a range of values to ensure alphabet characters can appear
        test_values = [i for i in range(1, 1000, 50)]  # Sample across range
        all_chars = set()
        
        for value in test_values:
            encoded = Base62Encoder.encode(value)
            all_chars.update(encoded)
        
        # Should use a portion of the alphabet
        assert len(all_chars) > 10, f"Only used {len(all_chars)} characters from alphabet"
    
    def test_decode_invalid_characters(self):
        """Test decoding with invalid characters raises appropriate errors"""
        invalid_strings = [
            "abc123@",  # Contains invalid character
            "abc 123",  # Contains space
            "abc#123",  # Contains special character
        ]
        
        for invalid_string in invalid_strings:
            try:
                # Should raise ValueError or KeyError for invalid input
                Base62Encoder.decode(invalid_string)
                assert False, f"Should have raised error for invalid string: {invalid_string}"
            except (ValueError, KeyError):
                # Expected behavior for invalid input
                pass

class TestCacheManagerIntegration:
    def test_cache_workflow(self):
        """Test complete cache workflow"""
        mock_redis = Mock()
        
        # Setup mock responses
        mock_redis.get.return_value = None  # Cache miss first
        mock_redis.setex.return_value = True
        
        cache = CacheManager(mock_redis, ttl=3600)
        
        # Simulate cache miss -> set -> hit workflow
        short_code = "abc123"
        original_url = "https://example.com"
        
        # First get (cache miss)
        result = cache.get_url(short_code)
        assert result is None
        
        # Set in cache
        cache.set_url(short_code, original_url)
        mock_redis.setex.assert_called_with(f"url:{short_code}", 3600, original_url)
        
        # Simulate cache hit
        mock_redis.get.return_value = original_url.encode('utf-8')
        result = cache.get_url(short_code)
        assert result == original_url

class TestValidationIntegration:
    def test_url_validation_with_real_domains(self):
        """Test URL validation with real-world domain patterns"""
        real_world_urls = [
            "https://github.com/user/repo",
            "https://stackoverflow.com/questions/123456",
            "https://docs.python.org/3/library/urllib.parse.html",
            "https://www.googleapis.com/oauth2/v1/userinfo",
            "https://api.stripe.com/v1/charges",
            "https://cdn.jsdelivr.net/npm/package@version/file.js",
            "https://fonts.googleapis.com/css2?family=Roboto",
        ]
        
        for url in real_world_urls:
            is_valid, message = URLValidator.is_valid_url(url)
            assert is_valid, f"Real-world URL {url} should be valid: {message}"
    
    def test_custom_code_realistic_patterns(self):
        """Test custom codes with realistic user patterns"""
        realistic_codes = [
            "github",
            "portfolio",
            "resume-2024",
            "my_project",
            "demo-app",
            "v1-api",
            "user123",
            "temp_link",
            "short",
            "redirect_me"
        ]
        
        for code in realistic_codes:
            is_valid, message = URLValidator.is_valid_custom_code(code)
            assert is_valid, f"Realistic code '{code}' should be valid: {message}"
    
    def test_validation_error_messages(self):
        """Test that validation provides helpful error messages"""
        # Test URL validation error messages
        is_valid, message = URLValidator.is_valid_url("not-a-url")
        assert not is_valid
        assert "invalid" in message.lower() or "format" in message.lower()
        
        is_valid, message = URLValidator.is_valid_url("ftp://example.com")
        assert not is_valid
        assert "http" in message.lower() or "scheme" in message.lower()
        
        # Test custom code validation error messages
        is_valid, message = URLValidator.is_valid_custom_code("ab")
        assert not is_valid
        assert "3" in message and "16" in message  # Should mention length requirements
        
        is_valid, message = URLValidator.is_valid_custom_code("code@invalid")
        assert not is_valid
        assert any(word in message.lower() for word in ["character", "letter", "number", "hyphen", "underscore"])