import smtplib

try:
    server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server_ssl.ehlo()   # optional
    # ...send emails
print("sucesss")
except:
    print('Something went wrong...')
