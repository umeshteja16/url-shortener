#!/usr/bin/env python3
"""
Local development setup for URL Shortener
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if required environment variables are set
required_vars = ['DATABASE_URL', 'SECRET_KEY']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please create a .env file or set these environment variables:")
    for var in missing_vars:
        print(f"  {var}=your_value_here")
    print("\nExample .env file:")
    print("DATABASE_URL=postgresql://postgres:password@localhost:5432/urlshortener")
    print("SECRET_KEY=your-secret-key-change-this")
    print("REDIS_URL=redis://localhost:6379/0")
    print("BASE_URL=http://localhost:5000")
    sys.exit(1)

def test_postgresql():
    """Test PostgreSQL connection using environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    try:
        import psycopg2
        # Parse DATABASE_URL
        from urllib.parse import urlparse
        result = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port or 5432,
            database=result.path[1:],  # Remove leading '/'
            user=result.username,
            password=result.password
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected: {version[:50]}...")
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            print("❌ Wrong password. Please check DATABASE_URL")
        elif "database" in str(e) and "does not exist" in str(e):
            print("❌ Database doesn't exist. Please create it first")
        elif "could not connect" in str(e):
            print("❌ PostgreSQL server is not running")
        else:
            print(f"❌ PostgreSQL connection error: {e}")
        return False
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_redis():
    """Test Redis connection using environment variables"""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("⚠️  REDIS_URL not set, Redis will be disabled")
        return False
    
    try:
        import redis
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        print("✅ Redis connected successfully")
        return True
    except ImportError:
        print("❌ Redis package not installed: pip install redis")
        return False
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("Application will work without cache")
        return False

def setup_database():
    """Initialize database and return test API key"""
    try:
        from app import create_app, db
        from app.models import User, Counter
        
        app = create_app()
        
        with app.app_context():
            print("🔧 Setting up database...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create initial counter
            counter = Counter.query.filter_by(name='url_counter').first()
            if not counter:
                counter = Counter(name='url_counter', value=100000000000)
                db.session.add(counter)
                db.session.commit()
                print("✅ URL counter initialized")
            
            # Create test user
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                test_user = User(email='test@example.com')
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created")
            
            api_key = test_user.api_key
            
        return app, api_key
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    # Only run setup once (not during Flask reloader restart)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("URL Shortener - Local Development")
        print("=" * 50)
        
        # Test connections
        postgres_ok = test_postgresql()
        if not postgres_ok:
            print("\n💡 PostgreSQL Setup:")
            print("1. Install PostgreSQL")
            print("2. Create database using your DATABASE_URL")
            print("3. Start PostgreSQL service")
            print("4. Check your .env file settings")
            return
        
        redis_ok = test_redis()
        if not redis_ok:
            # Disable Redis in environment if connection failed
            os.environ['REDIS_URL'] = ''
        
        # Setup database and app
        app, api_key = setup_database()
        if not app:
            return
        
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        print("\n" + "=" * 50)
        print("🚀 URL Shortener Ready!")
        print("=" * 50)
        print(f"🌐 Web Interface: {base_url}")
        print(f"🔑 Test API Key: {api_key}")
        print(f"🐘 Database: Connected")
        print(f"🔴 Redis: {'ENABLED' if redis_ok else 'DISABLED'}")
        print("=" * 50)
        print("Press Ctrl+C to stop the server\n")
    else:
        # This is the reloader process, just create the app
        from app import create_app
        app = create_app()
    
    # Start Flask server
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        port = int(base_url.split(':')[-1]) if ':' in base_url else 5000
        app.run(host='127.0.0.1', port=port, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")

if __name__ == '__main__':
    main()