from flask import Blueprint, request, jsonify, redirect, render_template_string
from app.services import URLShortenerService, UserService
from app import limiter
from datetime import datetime

main = Blueprint('main', __name__)

# Simple HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .container { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px; 
        }
        h2 { 
            color: #444; 
            border-bottom: 2px solid #007bff; 
            padding-bottom: 10px; 
        }
        input[type="text"], input[type="email"] { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            font-size: 16px; 
            box-sizing: border-box; 
        }
        button { 
            background: #007bff; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px; 
            width: 100%; 
            margin-top: 10px; 
        }
        button:hover { 
            background: #0056b3; 
        }
        .result { 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 4px; 
            border-left: 4px solid; 
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            border-color: #28a745; 
        }
        .error { 
            background: #f8d7da; 
            color: #721c24; 
            border-color: #dc3545; 
        }
        code { 
            background: #e9ecef; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-family: monospace; 
            word-break: break-all; 
        }
        .api-section { 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 10px 0; 
        }
        .endpoint { 
            margin: 15px 0; 
            padding: 10px; 
            background: white; 
            border-radius: 4px; 
        }
        .endpoint h4 { 
            color: #007bff; 
            margin: 0 0 10px 0; 
        }
        a { 
            color: #007bff; 
            text-decoration: none; 
        }
        a:hover { 
            text-decoration: underline; 
        }
    </style>
</head>
<body>
    <h1>URL Shortener</h1>
    
    <div class="container">
        <h2>Shorten URL</h2>
        <form id="shortenForm">
            <input type="text" id="originalUrl" placeholder="Enter long URL (e.g., https://example.com)" required>
            <input type="text" id="customCode" placeholder="Custom code (optional, 3-16 characters)">
            <input type="text" id="apiKey" placeholder="API key (optional)">
            <button type="submit">Shorten URL</button>
        </form>
        <div id="shortenResult"></div>
    </div>
    
    <div class="container">
        <h2>Get API Key</h2>
        <form id="apiForm">
            <input type="email" id="email" placeholder="Email (optional)">
            <button type="submit">Generate API Key</button>
        </form>
        <div id="apiResult"></div>
    </div>
    
    <div class="container">
        <h2>API Documentation</h2>
        
        <div class="endpoint">
            <h4>POST /api/shorten</h4>
            <p><strong>Create a short URL</strong></p>
            <p>Request body:</p>
            <code>{"url": "https://example.com", "custom_code": "optional", "api_key": "optional", "expires_in_days": 365}</code>
        </div>
        
        <div class="endpoint">
            <h4>GET /{short_code}</h4>
            <p><strong>Redirect to original URL</strong></p>
            <p>Returns HTTP 302 redirect to the original URL</p>
        </div>
        
        <div class="endpoint">
            <h4>GET /api/stats/{short_code}</h4>
            <p><strong>Get URL statistics</strong></p>
            <p>Query parameter: <code>?api_key=your_key</code></p>
            <p>Returns click count, daily statistics, and recent clicks</p>
        </div>
        
        <div class="endpoint">
            <h4>POST /api/user/create</h4>
            <p><strong>Create user and get API key</strong></p>
            <p>Request body: <code>{"email": "optional@example.com"}</code></p>
        </div>
        
        <div class="endpoint">
            <h4>GET /api/user/info</h4>
            <p><strong>Get user information</strong></p>
            <p>Requires API key in header: <code>X-API-Key: your-key</code></p>
        </div>
        
        <div class="endpoint">
            <h4>GET /health</h4>
            <p><strong>Health check endpoint</strong></p>
            <p>Returns service status and version information</p>
        </div>
    </div>

    <script>
        // URL Shortening Form
        document.getElementById('shortenForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('originalUrl').value;
            const customCode = document.getElementById('customCode').value;
            const apiKey = document.getElementById('apiKey').value;
            
            if (!url) {
                showResult('shortenResult', 'Please enter a URL', false);
                return;
            }
            
            const payload = { url };
            if (customCode) payload.custom_code = customCode;
            if (apiKey) payload.api_key = apiKey;
            
            try {
                const response = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult('shortenResult', `
                        <strong>Success!</strong><br><br>
                        <strong>Short URL:</strong> <a href="${data.short_url}" target="_blank">${data.short_url}</a><br>
                        <strong>Short Code:</strong> ${data.short_code}<br>
                        <strong>Original URL:</strong> ${data.original_url}<br>
                        <strong>Created:</strong> ${new Date(data.created_at).toLocaleString()}
                        ${data.expires_at ? `<br><strong>Expires:</strong> ${new Date(data.expires_at).toLocaleString()}` : ''}
                    `, true);
                    
                    // Clear form
                    document.getElementById('originalUrl').value = '';
                    document.getElementById('customCode').value = '';
                } else {
                    showResult('shortenResult', `Error: ${data.error}`, false);
                }
            } catch (error) {
                showResult('shortenResult', `Error: ${error.message}`, false);
            }
        });
        
        // API Key Creation Form
        document.getElementById('apiForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const payload = email ? { email } : {};
            
            try {
                const response = await fetch('/api/user/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult('apiResult', `
                        <strong>API Key Created Successfully!</strong><br><br>
                        <strong>API Key:</strong> <code>${data.api_key}</code><br>
                        <strong>Email:</strong> ${data.email || 'Not provided'}<br>
                        <strong>Created:</strong> ${new Date(data.created_at).toLocaleString()}<br><br>
                        <small style="color: #dc3545;">⚠️ Save this API key securely - you won't see it again!</small>
                    `, true);
                    
                    // Clear form
                    document.getElementById('email').value = '';
                } else {
                    showResult('apiResult', `Error: ${data.error}`, false);
                }
            } catch (error) {
                showResult('apiResult', `Error: ${error.message}`, false);
            }
        });
        
        function showResult(elementId, content, isSuccess = true) {
            const resultDiv = document.getElementById(elementId);
            resultDiv.className = `result ${isSuccess ? 'success' : 'error'}`;
            resultDiv.innerHTML = content;
        }
        
        // URL validation on input
        document.getElementById('originalUrl').addEventListener('input', function(e) {
            const url = e.target.value;
            if (url && !url.match(/^https?:\/\/.+/)) {
                e.target.style.borderColor = '#dc3545';
            } else {
                e.target.style.borderColor = '#ddd';
            }
        });
        
        // Custom code validation
        document.getElementById('customCode').addEventListener('input', function(e) {
            const code = e.target.value;
            if (code && (code.length < 3 || code.length > 16 || !/^[a-zA-Z0-9_-]+$/.test(code))) {
                e.target.style.borderColor = '#dc3545';
            } else {
                e.target.style.borderColor = '#ddd';
            }
        });
    </script>
</body>
</html>
"""

@main.route('/')
def index():
    """Home page with web interface"""
    return render_template_string(HTML_TEMPLATE)

@main.route('/<short_code>')
def redirect_url(short_code):
    """Redirect short URL to original URL"""
    service = URLShortenerService()
    
    # Collect analytics data
    request_data = {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'referrer': request.headers.get('Referer', '')
    }
    
    result, status_code = service.get_original_url(short_code, track_analytics=True, request_data=request_data)
    
    if status_code == 200:
        return redirect(result['original_url'], code=302)
    else:
        return jsonify(result), status_code

# API Routes
@main.route('/api/shorten', methods=['POST'])
@limiter.limit("10 per minute")
def create_short_url():
    """Create a shortened URL"""
    service = URLShortenerService()
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    result, status_code = service.create_short_url(
        original_url=data['url'],
        api_key=data.get('api_key'),
        custom_code=data.get('custom_code'),
        expires_in_days=data.get('expires_in_days')
    )
    
    return jsonify(result), status_code

@main.route('/api/stats/<short_code>')
def get_url_stats(short_code):
    """Get URL statistics"""
    service = URLShortenerService()
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    result, status_code = service.get_url_stats(short_code, api_key)
    return jsonify(result), status_code

@main.route('/api/user/create', methods=['POST'])
@limiter.limit("5 per hour")
def create_user():
    """Create a new user"""
    data = request.get_json() or {}
    email = data.get('email')
    
    result, status_code = UserService.create_user(email)
    return jsonify(result), status_code

@main.route('/api/user/info')
def get_user_info():
    """Get user information"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    result, status_code = UserService.get_user_info(api_key)
    return jsonify(result), status_code

@main.route('/api/user/urls')
def get_user_urls():
    """Get all URLs created by user"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    service = URLShortenerService()
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    result, status_code = service.get_user_urls(api_key, limit, offset)
    return jsonify(result), status_code

@main.route('/api/url/<short_code>', methods=['DELETE'])
def delete_url(short_code):
    """Delete a URL"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    service = URLShortenerService()
    result, status_code = service.delete_url(short_code, api_key)
    return jsonify(result), status_code

@main.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'features': [
            'URL shortening',
            'Custom aliases',
            'Analytics tracking',
            'Rate limiting',
            'Redis caching',
            'PostgreSQL storage'
        ]
    }), 200

# Error Handlers
@main.errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': '60 seconds'
    }), 429

@main.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@main.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@main.errorhandler(400)
def bad_request(e):
    """Handle bad request errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request data'
    }), 400