#!/usr/bin/env python3
"""
Backend Environment Check
Check what environment variables the backend is actually loading
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

# Load environment like the backend does
from dotenv import load_dotenv

ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

print("🔍 Backend Environment Variables")
print("=" * 50)
print(f"MONGO_URL: {os.environ.get('MONGO_URL')}")
print(f"DB_NAME: {os.environ.get('DB_NAME', 'test_database')}")
print(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', 'Not set')[:20]}...")
print(f"STRIPE_API_KEY: {os.environ.get('STRIPE_API_KEY', 'Not set')[:20]}...")

# Check if there are any other environment files
print("\nEnvironment files found:")
for env_file in ['/app/.env', '/app/backend/.env', '/app/frontend/.env']:
    if os.path.exists(env_file):
        print(f"✅ {env_file}")
        with open(env_file, 'r') as f:
            lines = f.readlines()[:5]  # First 5 lines
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    print(f"   {line.strip()}")
    else:
        print(f"❌ {env_file}")

# Check if there are system environment variables that might override
print("\nSystem environment variables (that might override .env):")
for key in os.environ:
    if any(keyword in key.upper() for keyword in ['MONGO', 'DB_', 'OPENAI', 'STRIPE']):
        value = os.environ[key]
        if len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")