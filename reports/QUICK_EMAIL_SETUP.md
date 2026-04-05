# 🚀 Quick Email Setup - Send Real Emails to Users

## **Option 1: Brevo SMTP (Recommended - 300 free emails/day)**

### **Step 1: Get Brevo Credentials**
1. Go to: https://www.brevo.com/
2. Sign up for free account
3. Go to "SMTP & API" → "SMTP" 
4. Create SMTP Key named "Fagi Errands"
5. Copy the SMTP key (starts with `xsmtpsib-`)

### **Step 2: Update Settings**
Edit `fagierrandsbackup/settings.py` lines 291-292:

```python
# Replace these lines:
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'YOUR_BREVO_LOGIN_EMAIL@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'xsmtpsib-YOUR_SMTP_KEY_HERE')

# With your actual credentials:
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'your-actual-email@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'xsmtpsib-your-actual-smtp-key')
```

---

## **Option 2: Gmail SMTP (Alternative)**

### **Step 1: Enable Gmail App Password**
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate App Password for "Mail"
4. Copy the 16-character password

### **Step 2: Update Settings**
Edit `fagierrandsbackup/settings.py`:

```python
# Uncomment and update these lines:
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'your-gmail@gmail.com'  
EMAIL_HOST_PASSWORD = 'your-16-char-app-password'
```

---

## **Step 3: Test Real Email Sending**

1. **Restart Django server:**
   ```bash
   python manage.py runserver 8006
   ```

2. **Test with your real email:**
   ```bash
   curl -X POST http://localhost:8006/api/accounts/smtp/send-otp/ \
     -H "Content-Type: application/json" \
     -d '{"email": "your-real-email@gmail.com"}'
   ```

3. **Check your inbox!** 📧

---

## **What You'll Get**

✅ **Beautiful HTML emails** with professional formatting  
✅ **6-digit OTP codes** in highlighted boxes  
✅ **Works with ANY email domain** (Gmail, Outlook, Yahoo, etc.)  
✅ **No Supabase domain restrictions**  
✅ **Free tier: 300 emails/day (Brevo) or unlimited (Gmail)**  

---

## **Troubleshooting**

### **Error: Authentication failed**
- Double-check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- For Gmail: Make sure you're using App Password, not regular password
- For Brevo: Make sure SMTP key starts with `xsmtpsib-`

### **Error: Connection timeout**
- Check firewall settings
- Try different EMAIL_PORT (25, 465, or 587)

### **Emails going to spam**
- This is normal for new SMTP setups
- Check spam/junk folder
- Users should mark as "Not Spam"

---

## **Ready to Send Real Emails! 🎉**

After setup, your users will receive beautiful verification emails in their actual inboxes!