import smtplib
import os


gg_py_pass = os.environ.get('GOOGLE_PYTHON_TEST_PASS')
gg_mail = os.environ.get('GOOGLE_MAIL')
print(gg_mail)

sender = gg_mail
receiver = os.environ.get('ZIMBRA_MAIL')
print(receiver)


with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()

    smtp.login(gg_mail, gg_py_pass)
    print("good login")


    subject = "test mail"
    body = "coucou"

    msg = f'Suject: {subject}\n\n{body}'

    smtp.sendmail(sender, receiver, msg)
    print("envoyé")