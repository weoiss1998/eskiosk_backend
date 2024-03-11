# smtplib Module importieren
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST=str(os.getenv('SMTP_HOST')).strip()
SMTP_PORT=int(os.getenv('SMTP_PORT'))
SMTP_USERNAME=str(os.getenv('SMTP_USERNAME')).strip()
SMTP_PASSWORD=str(os.getenv('SMTP_PASSWORD')).strip()
EMAIL_FROM_NAME=str(os.getenv('EMAIL_FROM_NAME')).strip()
EMAIL_FROM_ADDRESS=str(os.getenv('EMAIL_FROM_ADDRESS')).strip()

MEINE_ADRESSE = 'simon.heinrich.weiss@web.de'
PASSWORT = ''





messageTemplate = "Hello {CONTACT_NAME},\nThis is a test email.\nBest regards"
codeTemplate = "Hello {CONTACT_NAME},\nThis is your verification code: {CODE}.\nBest regards"
resetCodeTemplate = "Hello {CONTACT_NAME},\nThis is your password reset code: {CODE}.\nBest regards"
buyTemplate = "Hello {CONTACT_NAME},\nYou have purchased {PRODUCT_NAME} with a total sum of {TOTAL_SUM}€.\nBest regards"
adminActivationTemplate = "Hello {CONTACT_NAME},\nA new user has registered with the name {NAME} and would like to be activated.\nBest regards"
accountingTemplate = "Hello {CONTACT_NAME},\nYou have a balance of {BALANCE}€.\n You can find attached the actual invoice. \nBest regards"
productLowStockTemplate = "Hello {CONTACT_NAME},\nThe product {PRODUCT_NAME} is low in stock. \nBest regards"


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

def auth_code_mail(s, email, code, name):
    msg = MIMEMultipart()       # Erstelle Nachricht

    message = codeTemplate.format(CONTACT_NAME=name, CODE=code)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Verification code"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def reset_code_mail(s, email, code, name):
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = resetCodeTemplate.format(CONTACT_NAME=name, CODE=code)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Reset code"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def buy_mail(s, email, name, product_name, total_sum): 
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = buyTemplate.format(CONTACT_NAME=name, PRODUCT_NAME=product_name, TOTAL_SUM=total_sum)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Purchase confirmation"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg


def admin_activation_mail(s, email, name, new_user_name):
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = adminActivationTemplate.format(CONTACT_NAME=name, NAME=new_user_name)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="New user registration"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def accounting_mail(s, email, name, balance, invoice, invoice_name): #TODO: Add invoice attachment
    msg = MIMEMultipart()       

    message = accountingTemplate.format(CONTACT_NAME=name, BALANCE=balance)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="New Invoice from ESKiosk"

    msg.attach(MIMEText(message, 'plain'))


    # Read the file and encode it into base64 format
    mime_application = MIMEApplication(invoice,_subtype="pdf")

    # Add header as pdf attachment
    mime_application.add_header('Content-Disposition', 'attachment', filename=str(invoice_name))
    msg.attach(mime_application)

    s.send_message(msg)
    
    del msg

def product_low_stock_mail(s, email, name, product_name):
    msg = MIMEMultipart()       # Erstelle Nachricht

    # Vorname in die Nachricht einfü
    message = productLowStockTemplate.format(CONTACT_NAME=name, PRODUCT_NAME=product_name)

    msg['From']=EMAIL_FROM_ADDRESS
    msg['To']=email
    msg['Subject']="Product low in stock"

    # Nachricht hinzufügen 
    msg.attach(MIMEText(message, 'plain'))

    # Nachricht über den eingerichteten SMTP-Server abschicken
    s.send_message(msg)
    
    del msg

def send_auth_code(email, code, name):
    print(SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD)
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    auth_code_mail(s, email, code, name)
    s.quit()

def send_reset_code(email, code, name):
    print(SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD)
    s = smtplib.SMTP(host=SMTP_HOST, port=int(SMTP_PORT))
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    reset_code_mail(s, email, code, name)
    s.quit()

def send_mail_test():
    s = smtplib.SMTP(host='smtp.web.de', port=587)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    namen = {"Simon"}
    emails = {"simon.heinrich.weiss@web.de"}

    prepare_mail(s, namen, emails)
        
    s.quit()

def send_buy_mail(email, name, product_name, total_sum):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    buy_mail(s, email, name, product_name, total_sum)
    s.quit()

def send_admin_activation_mail(email, name, new_user_name):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    admin_activation_mail(s, email, name, new_user_name)
    s.quit()

def send_accounting_mail(email, name, balance, invoice, invoice_name):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    accounting_mail(s, email, name, balance, invoice, invoice_name)
    s.quit()

def send_product_low_stock_mail(email, name, product_name):
    s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    product_low_stock_mail(s, email, name, product_name)
    s.quit()
