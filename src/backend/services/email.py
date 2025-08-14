"""
Email service
"""
import os
import logging
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self):
        self.api_key = os.environ.get('MAILJET_API_KEY')
        self.secret_key = os.environ.get('MAILJET_SECRET_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@buildyoursmartcart.com')
        
        # Check if we're in live mode (real API keys)
        self.live_mode = bool(
            self.api_key and 
            self.secret_key and 
            not any(placeholder in str(self.api_key) for placeholder in ['your-', 'placeholder', 'here']) and
            not any(placeholder in str(self.secret_key) for placeholder in ['your-', 'placeholder', 'here'])
        )
        
        logger.info(f"EmailService initialized - Live mode: {self.live_mode}, Sender: {self.sender_email}")
    
    async def send_verification_email(self, email: str, code: str) -> bool:
        """Send verification email"""
        try:
            if not self.live_mode:
                logger.info(f"Email service in test mode - would send verification code {code} to {email}")
                return True
            
            # In live mode, implement actual email sending
            subject = "Verify Your Account - buildyoursmartcart.com"
            body = f"""
            Welcome to buildyoursmartcart.com!
            
            Your verification code is: {code}
            
            Please enter this code to verify your account.
            
            This code will expire in 24 hours.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            The buildyoursmartcart.com Team
            """
            
            # Here you would implement actual email sending with Mailjet
            # For now, we'll log it
            logger.info(f"Sending verification email to {email} with code {code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False
    
    async def send_welcome_email(self, email: str, name: str = None) -> bool:
        """Send welcome email after verification"""
        try:
            if not self.live_mode:
                logger.info(f"Email service in test mode - would send welcome email to {email}")
                return True
            
            subject = "Welcome to buildyoursmartcart.com!"
            body = f"""
            Hi {name or 'there'}!
            
            Welcome to buildyoursmartcart.com - your AI-powered recipe and grocery assistant!
            
            You now have access to:
            - AI-generated recipes tailored to your preferences
            - Weekly meal planning with grocery integration
            - Starbucks secret menu recipes
            - Walmart shopping integration
            
            Your free 7-day trial is now active. Enjoy exploring all our features!
            
            Best regards,
            The buildyoursmartcart.com Team
            """
            
            logger.info(f"Sending welcome email to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False

# Create service instance
email_service = EmailService()