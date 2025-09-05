"""
SMS notification adapter for EduAnalytics.

Provides SMS sending capabilities through various providers (Twilio, AWS SNS, etc.).
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime
import json
import base64

from app.core.config import settings
from app.middleware.observability import get_business_metrics

logger = logging.getLogger(__name__)


class TwilioSMSAdapter:
    """Twilio SMS adapter."""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        self.timeout = getattr(settings, 'SMS_TIMEOUT', 30)
        self.business_metrics = get_business_metrics()
        
        if not self.enabled:
            logger.warning("Twilio SMS adapter disabled: credentials not configured")
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS via Twilio.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message text
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.error("Cannot send SMS: Twilio not configured")
            return False
        
        start_time = datetime.now()
        success = False
        
        try:
            # Prepare authentication
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'From': self.from_number,
                'To': to_number,
                'Body': message
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/Messages.json",
                    headers=headers,
                    data=data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    message_sid = result.get('sid')
                    logger.info(f"SMS sent successfully via Twilio: {message_sid}")
                    success = True
                else:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get('message', 'Unknown error')
                    logger.error(f"Twilio SMS error: {response.status_code} - {error_message}")
        
        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {str(e)}")
        
        finally:
            # Track metrics
            if self.business_metrics:
                self.business_metrics.track_notification_sent(
                    channel="sms_twilio",
                    success=success,
                    notification_type="sms"
                )
        
        return success


class AWSSNSSMSAdapter:
    """AWS SNS SMS adapter."""
    
    def __init__(self):
        self.region = getattr(settings, 'AWS_REGION', 'us-east-1')
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.enabled = bool(self.access_key and self.secret_key)
        self.business_metrics = get_business_metrics()
        
        if not self.enabled:
            logger.warning("AWS SNS SMS adapter disabled: credentials not configured")
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS via AWS SNS.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message text
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.error("Cannot send SMS: AWS SNS not configured")
            return False
        
        start_time = datetime.now()
        success = False
        
        try:
            # Note: This is a simplified implementation
            # In production, use boto3 or proper AWS SDK
            import boto3
            
            sns_client = boto3.client(
                'sns',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            
            response = sns_client.publish(
                PhoneNumber=to_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'EduAnalytics'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                message_id = response.get('MessageId')
                logger.info(f"SMS sent successfully via AWS SNS: {message_id}")
                success = True
            else:
                logger.error(f"AWS SNS SMS error: {response}")
        
        except Exception as e:
            logger.error(f"Failed to send SMS via AWS SNS: {str(e)}")
        
        finally:
            # Track metrics
            if self.business_metrics:
                self.business_metrics.track_notification_sent(
                    channel="sms_aws",
                    success=success,
                    notification_type="sms"
                )
        
        return success


class SMSService:
    """Unified SMS service that supports multiple providers."""
    
    def __init__(self):
        self.provider = getattr(settings, 'SMS_PROVIDER', 'twilio').lower()
        self.max_message_length = getattr(settings, 'SMS_MAX_LENGTH', 160)
        
        # Initialize adapters
        self.twilio_adapter = TwilioSMSAdapter()
        self.aws_adapter = AWSSNSSMSAdapter()
        
        # Select primary adapter
        if self.provider == 'twilio' and self.twilio_adapter.enabled:
            self.primary_adapter = self.twilio_adapter
        elif self.provider == 'aws' and self.aws_adapter.enabled:
            self.primary_adapter = self.aws_adapter
        else:
            self.primary_adapter = None
            logger.warning(f"SMS provider '{self.provider}' not available or not configured")
    
    def _truncate_message(self, message: str) -> str:
        """Truncate message to fit SMS length limits."""
        if len(message) <= self.max_message_length:
            return message
        
        # Truncate and add ellipsis
        truncated = message[:self.max_message_length - 3] + "..."
        return truncated
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number to E.164 format."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if missing (assuming US +1 as default)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif not digits_only.startswith('+'):
            return f"+{digits_only}"
        
        return phone_number
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS through the configured provider.
        
        Args:
            to_number: Recipient phone number
            message: SMS message text
            
        Returns:
            bool: True if sent successfully
        """
        if not self.primary_adapter:
            logger.error("No SMS adapter available")
            return False
        
        # Format phone number and truncate message
        formatted_number = self._format_phone_number(to_number)
        truncated_message = self._truncate_message(message)
        
        logger.info(f"Sending SMS to {formatted_number} via {self.provider}")
        
        try:
            return await self.primary_adapter.send_sms(formatted_number, truncated_message)
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    async def send_assignment_due_soon(
        self,
        phone_number: str,
        assignment_title: str,
        course_name: str,
        due_date: str
    ) -> bool:
        """Send assignment due soon SMS notification."""
        message = f"EduAnalytics: Assignment '{assignment_title}' in {course_name} is due {due_date}. Don't forget to submit!"
        return await self.send_sms(phone_number, message)
    
    async def send_grade_posted(
        self,
        phone_number: str,
        assignment_title: str,
        grade: str,
        course_name: str
    ) -> bool:
        """Send grade posted SMS notification."""
        message = f"EduAnalytics: Grade posted for '{assignment_title}' in {course_name}: {grade}. Check your dashboard for details."
        return await self.send_sms(phone_number, message)
    
    async def send_urgent_reminder(
        self,
        phone_number: str,
        reminder_text: str
    ) -> bool:
        """Send urgent reminder SMS."""
        message = f"EduAnalytics URGENT: {reminder_text}"
        return await self.send_sms(phone_number, message)
    
    async def send_verification_code(
        self,
        phone_number: str,
        verification_code: str
    ) -> bool:
        """Send phone number verification code."""
        message = f"EduAnalytics verification code: {verification_code}. This code expires in 10 minutes."
        return await self.send_sms(phone_number, message)
    
    def is_enabled(self) -> bool:
        """Check if SMS service is enabled and configured."""
        return self.primary_adapter is not None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all SMS providers."""
        return {
            "primary_provider": self.provider,
            "providers": {
                "twilio": {
                    "enabled": self.twilio_adapter.enabled,
                    "configured": bool(self.twilio_adapter.account_sid)
                },
                "aws": {
                    "enabled": self.aws_adapter.enabled,
                    "configured": bool(self.aws_adapter.access_key)
                }
            },
            "service_enabled": self.is_enabled()
        }


# Global SMS service instance
sms_service = SMSService()
