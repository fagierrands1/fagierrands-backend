#!/usr/bin/env python
"""
Quick SMTP test script to verify Brevo connection
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Brevo SMTP settings
SMTP_HOST = 'smtp-relay.brevo.com'
SMTP_PORT = 587
SMTP_USER = '938fe3002@smtp-brevo.com'
SMTP_PASSWORD = 'xsmtpsib-d95db4e9eef4f54c8ee6061c4299a168e03eb984bc97a386e372c6846ae86ed6-CUEzvYQXrN4m5gZ9'

def test_smtp_connection():
    try:
        print("🔄 Testing SMTP connection to Brevo...")
        
        # Create SMTP connection
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()  # Enable TLS
        
        print("🔐 Attempting login...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ Login successful!")
        
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = 'noreply@fagierrands.com'
        msg['To'] = 'devops@fagitone.com'
        msg['Subject'] = 'Test Email from Fagi Errands'
        
        body = """
        This is a test email to verify SMTP is working.
        
        If you receive this, the SMTP configuration is correct!
        
        Test OTP: 123456
        """
        msg.attach(MIMEText(body, 'plain'))
        
        print("📧 Sending test email...")
        server.send_message(msg)
        print("✅ Email sent successfully!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False

if __name__ == "__main__":
    test_smtp_connection()