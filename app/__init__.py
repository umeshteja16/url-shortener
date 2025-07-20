from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_limiter():
    """Create rate limiter with Redis or in-memory storage"""
    try:
        if os.getenv('REDIS_URL'):
            if os.getenv('PERFORMANCE_MODE', 'false').lower() == 'true':
                limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[]  # No default limits in performance mode
                )
        else:
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"]
            )
        return limiter
    except:
        return Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )

limiter = create_limiter()

def create_app():
    app = Flask(__name__)
    
    # Configure app directly from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', '')
    app.config['BASE_URL'] = os.getenv('BASE_URL', 'http://localhost:5000')
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    


    #These settings will:
    # POOL_SIZE: 20 concurrent database connections
    # MAX_OVERFLOW: 30 additional connections when needed
    # POOL_TIMEOUT: 30 seconds to wait for connection
    # POOL_RECYCLE: Recycle connections every 30 minutes
    # This should help push your performance closer to the 8,000 req/s target! 
    app.config['SQLALCHEMY_POOL_SIZE'] = 20
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 30
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800



    # Validate required configuration
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError("DATABASE_URL environment variable is required")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Initialize Redis
    try:
        if app.config['REDIS_URL']:
            redis_client = redis.from_url(app.config['REDIS_URL'])
            redis_client.ping()
            app.redis = redis_client
            # Only print in development, not during reloader
            if os.getenv('WERKZEUG_RUN_MAIN') != 'true':
                print("✅ Redis connected and caching enabled")
        else:
            app.redis = None
            if os.getenv('WERKZEUG_RUN_MAIN') != 'true':
                print("⚠️  Running without Redis cache")
    except Exception as e:
        app.redis = None
        if os.getenv('WERKZEUG_RUN_MAIN') != 'true':
            print(f"⚠️  Redis connection failed: {e}")
            print("Running without cache")
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app