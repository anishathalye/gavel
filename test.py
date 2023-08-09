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
    try:
        server.login(gmail_user, gmail_password)
        print ('Logged In to Gmail')
        try:
            server.sendmail(sent_from, to, email_text)
            print ('Email sent!')
        except Exception as error:
            print('Could not send mail', error)
            server.close()            
    except Exception as error:
        print('Could not login into to gmail ', error)    
except:
    print('Could not connect to smtp.gmail.com')


