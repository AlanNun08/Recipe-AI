
#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded .env file from: {env_file}")
else:
    print(f"⚠️ No .env file found at: {env_file}")

# Test environment variables
print("\n🔑 Environment Variables Status:")
print("=" * 50)

openai_key = os.environ.get('OPENAI_API_KEY')
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')

print(f"OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
if openai_key:
    print(f"  - Starts with: {openai_key[:10]}...")
    print(f"  - Length: {len(openai_key)} characters")

print(f"MONGO_URL: {'✅ Set' if mongo_url else '❌ Missing'}")
if mongo_url:
    print(f"  - Starts with: {mongo_url[:20]}...")

print(f"DB_NAME: {'✅ Set' if db_name else '❌ Missing'}")
if db_name:
    print(f"  - Value: {db_name}")

# Test OpenAI client initialization
print("\n🤖 OpenAI Client Test:")
print("=" * 30)

try:
    from openai import OpenAI
    if openai_key:
        client = OpenAI(api_key=openai_key)
        print("✅ OpenAI client initialized successfully")
    else:
        print("❌ Cannot initialize OpenAI client - no API key")
except Exception as e:
    print(f"❌ OpenAI client initialization failed: {e}")

print("\n🏁 Test Complete!")