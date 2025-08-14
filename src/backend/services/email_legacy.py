import os
import random
import string
import requests
import json
from datetime import datetime, timedelta
from typing import Optional
import logging
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Load from environment variables
        self.api_key = os.environ.get('MAILJET_API_KEY')
        self.secret_key = os.environ.get('MAILJET_SECRET_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL')
        self.test_mode = False  # Always use live mode
        self.last_verification_code = None  # Store for testing
        
        # Check if all required environment variables are set
        if not all([self.api_key, self.secret_key, self.sender_email]):
            logger.error("Missing required Mailjet environment variables")
            self.initialized = False
        else:
            self.initialized = True
            logger.info(f"EmailService initialized with environment variables - Live mode: True, Sender: {self.sender_email}")
    
    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    async def send_verification_email(self, to_email: str, first_name: str, verification_code: str) -> bool:
        """Send verification email with 6-digit code using Mailjet API"""
        # Store for testing
        self.last_verification_code = verification_code
        
        # Force live mode for testing
        self.test_mode = False
        
        if self.test_mode:
            logger.info(f"TEST MODE: Would send verification code {verification_code} to {to_email}")
            print(f"🧪 TEST EMAIL: Verification code {verification_code} for {to_email}")
            return True
        
        try:
            # Prepare the email data in Mailjet v3.1 format
            data = {
                "Messages": [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": "AI Chef App"
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": "Verify Your AI Chef Account - Code Inside",
                        "TextPart": f"""
Hi {first_name},

Welcome to AI Chef! Please verify your email address to complete your registration.

Your verification code is: {verification_code}

This code will expire in 5 minutes.

If you didn't create this account, please ignore this email.

Best regards,
AI Chef Team
                        """,
                        "HTMLPart": f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #10b981; margin-bottom: 10px;">👨‍🍳 AI Chef</h1>
        <h2 style="color: #374151; margin-top: 0;">Verify Your Account</h2>
    </div>
    
    <div style="background-color: white; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <p style="color: #374151; font-size: 16px; margin-bottom: 20px;">Hi {first_name},</p>
        
        <p style="color: #374151; font-size: 16px; margin-bottom: 20px;">
            Welcome to AI Chef! Please verify your email address to complete your registration and start generating amazing recipes.
        </p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div style="background: linear-gradient(135deg, #10b981, #3b82f6); color: white; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 8px; letter-spacing: 8px; font-family: monospace; display: inline-block;">
                {verification_code}
            </div>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 20px;">
            ⏰ This code will expire in 5 minutes.
        </p>
        
        <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
            <h3 style="color: #374151; margin-bottom: 10px;">🎯 What's Next?</h3>
            <p style="color: #6b7280; font-size: 14px; margin: 0;">
                After verification, you'll be able to:<br/>
                🤖 Generate AI-powered recipes<br/>
                🛒 Get instant Walmart grocery delivery<br/>
                🍃 Access healthy & budget-friendly options
            </p>
        </div>
    </div>
    
    <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
        <p style="color: #6b7280; font-size: 12px; text-align: center;">
            If you didn't create this account, please ignore this email.
        </p>
        <p style="color: #6b7280; font-size: 12px; text-align: center;">
            Best regards,<br/>
            <strong>AI Chef Team</strong>
        </p>
    </div>
</body>
</html>
                        """
                    }
                ]
            }
            
            # Make the API call using requests
            auth = (self.api_key, self.secret_key)
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Sending verification email to {to_email} with code {verification_code}")
            logger.info(f"Using Mailjet credentials - API Key: {self.api_key}, Secret Key: {self.secret_key}, Sender: {self.sender_email}")
            
            response = requests.post(
                'https://api.mailjet.com/v3.1/send',
                auth=auth,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Email sent successfully to {to_email}. Mailjet response: {result}")
                print(f"📧 LIVE EMAIL SENT: Verification code {verification_code} sent to {to_email}")
                return True
            else:
                logger.error(f"❌ Failed to send email. Status: {response.status_code}, Response: {response.text}")
                print(f"❌ Email failed: Status {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending verification email: {str(e)}")
            print(f"❌ Email error: {str(e)}")
            return False

    async def send_password_reset_email(self, to_email: str, first_name: str, reset_code: str) -> bool:
        """Send password reset email with 6-digit code"""
        # Store for testing
        self.last_verification_code = reset_code
        
        # Force live mode for testing
        self.test_mode = False
        
        if self.test_mode:
            logger.info(f"TEST MODE: Would send password reset code {reset_code} to {to_email}")
            print(f"🧪 TEST EMAIL: Password reset code {reset_code} for {to_email}")
            return True
        
        try:
            # Prepare the email data in Mailjet v3.1 format
            data = {
                "Messages": [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": "AI Chef App"
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": "Reset Your AI Chef Password",
                        "TextPart": f"""
Hi {first_name},

We received a request to reset your AI Chef account password.

Your password reset code is: {reset_code}

This code will expire in 10 minutes.

If you didn't request this password reset, please ignore this email.

Best regards,
AI Chef Team
                        """,
                        "HTMLPart": f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #10b981; margin-bottom: 10px;">👨‍🍳 AI Chef</h1>
        <h2 style="color: #374151; margin-top: 0;">Reset Your Password</h2>
    </div>
    
    <div style="background-color: white; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <p style="color: #374151; font-size: 16px; margin-bottom: 20px;">Hi {first_name},</p>
        
        <p style="color: #374151; font-size: 16px; margin-bottom: 20px;">
            We received a request to reset your AI Chef account password. Use the code below to reset your password:
        </p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div style="background: linear-gradient(135deg, #ef4444, #f97316); color: white; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 8px; letter-spacing: 8px; font-family: monospace; display: inline-block;">
                {reset_code}
            </div>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 20px;">
            ⏰ This code will expire in 10 minutes.
        </p>
        
        <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444;">
            <h3 style="color: #dc2626; margin-bottom: 10px;">🔒 Security Notice</h3>
            <p style="color: #7f1d1d; font-size: 14px; margin: 0;">
                If you didn't request this password reset, please ignore this email.<br/>
                Your account remains secure.
            </p>
        </div>
    </div>
    
    <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
        <p style="color: #6b7280; font-size: 12px; text-align: center;">
            This password reset request was made from your AI Chef account.
        </p>
        <p style="color: #6b7280; font-size: 12px; text-align: center;">
            Best regards,<br/>
            <strong>AI Chef Team</strong>
        </p>
    </div>
</body>
</html>
                        """
                    }
                ]
            }
            
            # Make the API call using requests
            auth = (self.api_key, self.secret_key)
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Sending password reset email to {to_email} with code {reset_code}")
            
            response = requests.post(
                'https://api.mailjet.com/v3.1/send',
                auth=auth,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Password reset email sent successfully to {to_email}")
                print(f"📧 LIVE EMAIL SENT: Password reset code {reset_code} sent to {to_email}")
                return True
            else:
                logger.error(f"❌ Failed to send password reset email. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending password reset email: {str(e)}")
            return False

# Create global email service instance
email_service = EmailService()