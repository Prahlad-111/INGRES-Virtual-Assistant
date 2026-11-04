from email_service import send_otp_email

receiver_email = "your_email@example.com"
test_otp = "123456"

try:
    send_otp_email(receiver_email, test_otp)
    print("SUCCESS: OTP email sent through Brevo!")

except Exception as error:
    print("FAILED:", error)