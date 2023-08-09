import smtplib

gmail_user = 'hackathontest.rtx@gmail.com'
gmail_password = 'Raytheon123!'

sent_from = gmail_user
to = ['shane.stevens@rtx.com']
subject = 'Test Email From Heroku'
body = 'This is a test email sent from Heroku'

try:
    server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server_ssl.ehlo()   # optional
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

    print ('Email sent!')
except:
    print('Something went wrong...')
