# smtplib Module importieren
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST=os.getenv('SMTP_HOST')
SMTP_PORT=int(os.getenv('SMTP_PORT'))
SMTP_USERNAME=os.getenv('SMTP_USERNAME')
SMTP_PASSWORD=os.getenv('SMTP_PASSWORD')
EMAIL_FROM_NAME=os.getenv('EMAIL_FROM_NAME')
EMAIL_FROM_ADDRESS=os.getenv('EMAIL_FROM_ADDRESS')

MEINE_ADRESSE = 'simon.heinrich.weiss@web.de'
PASSWORT = ''





messageTemplate= "Hallo {KONTAKT_NAME},/n Dies ist eine Testmail./n Viele Grüße"
codeTemplate = "Hallo {KONTAKT_NAME},/n Dies ist dein Verifizierungscode: {CODE}./n Viele Grüße"
resetCodeTemplate = "Hallo {KONTAKT_NAME},/n Dies ist dein Code zum Zurücksetzen deines Passworts: {CODE}./n Viele Grüße"

def prepare_mail(s, namen, emails):
    
    # Sende eine Email für jeden Kontakt
    for name, email in zip(namen, emails):
        msg = MIMEMultipart()       # Erstelle Nachricht

        # Vorname in die Nachricht einfügen
        message = messageTemplate.format(KONTAKT_NAME=name)

        # Parameters der Nachricht vorbereiten
        msg['From']=EMAIL_FROM_ADDRESS
        msg['To']=email
        msg['Subject']="Ich lerne Python 3"

        # Nachricht hinzufügen
        msg.attach(MIMEText(message, 'plain'))

        # Nachricht über den eingerichteten SMTP-Server abschicken
        s.send_message(msg)
        
        del msg

def auth_code_mail(s, email, code):
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = codeTemplate.format(KONTAKT_NAME=email, CODE=code)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Verifizierungscode"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def reset_code_mail(s, email, code):
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = resetCodeTemplate.format(KONTAKT_NAME=email, CODE=code)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Resetcode"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def send_auth_code(email, code):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    auth_code_mail(s, email, code)
    s.quit()

def send_reset_code(email, code):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    reset_code_mail(s, email, code)
    s.quit()

def send_mail_test():
    s = smtplib.SMTP(host='smtp.web.de', port=587)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    namen = {"Simon"}
    emails = {"simon.heinrich.weiss@web.de"}

    prepare_mail(s, namen, emails)
        
    s.quit()

