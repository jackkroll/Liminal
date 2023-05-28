import smtplib
phoneCarrierDedirect = {
    "verizon" : "@vtext.com",
    "at&t": "@txt.att.net",
    "t-mobile": "@tmomail.net",
    "sprint" : "@messaging.sprintpcs.com",
    "cricket wireless": "@sms.cricketwireless.net",
    "consumer cellular": "@mailmymobile.net"
}

def send_email(recipient, subject, message):
    try:
        smtp_port = 587
        server_url = "smtp-relay.sendinblue.com"
        login = "amazingsupdawg@gmail.com"
        password = "ommitted"
        # Connect to the SMTP server
        server = smtplib.SMTP(server_url, smtp_port)
        server.starttls()
        server.login(login, password)

        # Create the email message
        email_message = f"Subject: {subject}\n\n{message}"

        # Send the email
        server.sendmail(login, recipient, email_message)
        print("Email sent successfully!")

        # Disconnect from the server
        server.quit()
    except Exception as e:
        print(f"An error occurred while sending the email: {str(e)}")


# Get user input

recipient = "2489819464@vtext.com"
subject = "Liminal System Message"
message = 'Your print, "Example.gcode" ,has finished'

# Send the email
send_email(recipient, subject, message)


