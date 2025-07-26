#!/usr/bin/env python3
"""
Test email sending functionality with Mailjet
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

async def test_email_sending():
    """Test actual email sending"""
    try:
        from email_service import email_service
        
        print("🧪 Testing Email Service...")
        print(f"Email service initialized: {email_service.initialized}")
        print(f"API Key: {email_service.api_key[:8]}..." if email_service.api_key else "None")
        print(f"Sender Email: {email_service.sender_email}")
        
        # Test verification email
        print("\n📧 Testing verification email...")
        test_code = email_service.generate_verification_code()
        print(f"Generated code: {test_code}")
        
        # Send verification email
        result = await email_service.send_verification_email(
            to_email="testuser@example.com",
            first_name="Test",
            verification_code=test_code
        )
        
        print(f"Verification email result: {'✅ Success' if result else '❌ Failed'}")
        
        # Test password reset email
        print("\n🔐 Testing password reset email...")
        reset_code = email_service.generate_verification_code()
        print(f"Generated reset code: {reset_code}")
        
        # Send reset email
        result = await email_service.send_password_reset_email(
            to_email="testuser@example.com",
            first_name="Test",
            reset_code=reset_code
        )
        
        print(f"Password reset email result: {'✅ Success' if result else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Error testing email service: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_email_sending())