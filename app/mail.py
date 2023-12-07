# smtplib Module importieren
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MEINE_ADRESSE = 'simon.heinrich.weiss@web.de'
PASSWORT = ''





messageTemplate= "Hallo {KONTAKT_NAME},/n Dies ist eine Testmail./n Viele Grüße"


def prepare_mail(s, namen, emails):
    
    # Sende eine Email für jeden Kontakt
    for name, email in zip(namen, emails):
        msg = MIMEMultipart()       # Erstelle Nachricht

        # Vorname in die Nachricht einfügen
        message = messageTemplate.format(KONTAKT_NAME=name)

        # Parameters der Nachricht vorbereiten
        msg['From']=MEINE_ADRESSE
        msg['To']=email
        msg['Subject']="Ich lerne Python 3"

        # Nachricht hinzufügen
        msg.attach(MIMEText(message, 'plain'))

        # Nachricht über den eingerichteten SMTP-Server abschicken
        s.send_message(msg)
        
        del msg

def send_mail():
    s = smtplib.SMTP(host='smtp.web.de', port=587)
    s.starttls()
    #s.login(MEINE_ADRESSE, PASSWORT)
    namen = {"Simon"}
    emails = {"simon.heinrich.weiss@web.de"}

    prepare_mail(s, namen, emails)
        
    s.quit()

