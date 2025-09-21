#!/usr/bin/env python3
"""
Debug startup script to check all dependencies and create test user
"""
import os
import sys
import asyncio
from pathlib import Path

def check_environment():
    """Check environment variables"""
    print("🔍 Environment Variable Check:")
    
    required_vars = [
        ('MONGO_URL', 'mongodb://localhost:27017'),
        ('DB_NAME', 'buildyoursmartcart_production')
    ]
    
    optional_vars = [
        'OPENAI_API_KEY',
        'WALMART_CONSUMER_ID', 
        'WALMART_PRIVATE_KEY'
    ]
    
    for var_name, default in required_vars:
        value = os.environ.get(var_name, default)
        if value == default:
            print(f"   ⚠️ {var_name}: Using default '{default}'")
            os.environ[var_name] = default
        else:
            print(f"   ✅ {var_name}: Set")
    
    for var_name in optional_vars:
        value = os.environ.get(var_name)
        print(f"   {'✅' if value else '❌'} {var_name}: {'Set' if value else 'Not set'}")

def check_files():
    """Check required files exist"""
    print("\n📁 File Check:")
    
    required_files = [
        'backend/server.py',
        'frontend/src/App.js',
        'main.py'
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        exists = path.exists()
        print(f"   {'✅' if exists else '❌'} {file_path}: {'Found' if exists else 'Missing'}")
        
        if not exists and file_path == 'backend/server.py':
            print("      ❌ This is critical - backend won't work without server.py")

async def test_backend_import():
    """Test backend import"""
    print("\n🔄 Backend Import Test:")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        print("   🔄 Importing backend.server...")
        from backend.server import app as backend_app
        
        route_count = len(backend_app.routes)
        print(f"   ✅ Backend imported successfully with {route_count} routes")
        
        # Check for auth routes
        auth_routes = [r for r in backend_app.routes if hasattr(r, 'path') and 'auth' in r.path]
        print(f"   🔐 Found {len(auth_routes)} auth routes")
        
        for route in auth_routes:
            if hasattr(route, 'methods'):
                methods = list(route.methods)
                print(f"      {methods} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Backend import failed: {e}")
        print(f"   ❌ Error type: {type(e).__name__}")
        import traceback
        print(f"   ❌ Stack trace: {traceback.format_exc()}")
        return False

async def test_database():
    """Test database connection"""
    print("\n🗄️ Database Test:")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_production')
        
        print(f"   🔗 Connecting to: {mongo_url}")
        print(f"   📊 Database: {db_name}")
        
        client = AsyncIOMotorClient(mongo_url)
        await client.admin.command('ping')
        print("   ✅ Database connection successful")
        
        db = client[db_name]
        collections = await db.list_collection_names()
        print(f"   📊 Collections: {collections}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

async def main():
    """Main debug function"""
    print("🚀 BuildYourSmartCart Debug Startup\n")
    
    check_environment()
    check_files()
    
    backend_ok = await test_backend_import()
    database_ok = await test_database()
    
    print(f"\n📊 Summary:")
    print(f"   Backend Import: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"   Database: {'✅ OK' if database_ok else '❌ FAILED'}")
    
    if backend_ok and database_ok:
        print("\n🧪 Creating test user...")
        try:
            from create_test_user import create_test_user
            await create_test_user()
            print("✅ Test user created/verified")
        except Exception as e:
            print(f"❌ Test user creation failed: {e}")
    
    if backend_ok and database_ok:
        print("\n🎉 All systems ready! You can now:")
        print("   1. Run: python main.py")
        print("   2. Go to: http://localhost:8080")
        print("   3. Login with: fresh@test.com / password123")
    else:
        print("\n❌ Some systems failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
