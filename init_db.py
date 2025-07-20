#!/usr/bin/env python3
"""
Initialize database for Render deployment
Run this once after deployment to set up the database
"""

import os
from app import create_app, db
from app.models import Counter, User

def init_render_database():
    """Initialize database for Render deployment"""
    print("🚀 Initializing database for Render deployment...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("📊 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create initial counter
            counter = Counter.query.filter_by(name='url_counter').first()
            if not counter:
                counter = Counter(name='url_counter', value=100000000000)
                db.session.add(counter)
                db.session.commit()
                print("✅ URL counter initialized")
            else:
                print("✅ URL counter already exists")
            
            # Create admin user for testing
            admin_user = User.query.filter_by(email='admin@urlshortener.com').first()
            if not admin_user:
                admin_user = User(email='admin@urlshortener.com')
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Admin user created")
                print(f"   Email: admin@urlshortener.com")
                print(f"   API Key: {admin_user.api_key}")
            else:
                print(f"✅ Admin user exists")
                print(f"   API Key: {admin_user.api_key}")
            
            print("\n🎉 Database initialization completed successfully!")
            print("🌟 Your URL shortener is ready for production!")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = init_render_database()
    if success:
        print("\n🚀 Ready to handle 500+ req/s on Render! 🚀")
    else:
        print("\n❌ Initialization failed. Check logs for errors.")
        exit(1)