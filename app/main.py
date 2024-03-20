import time
from fastapi import Depends, FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Annotated
from . import crud, models, schemas, mail, backup, database
from .database import SessionLocal, engine
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import random
from datetime import date, datetime
import qrcode
import io
import os
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, PackageLoader
from weasyprint import HTML
from pydantic import Field
from dotenv import load_dotenv
import pytz
from uuid import uuid4
from fastapi_utils.tasks import repeat_every
from fastapi.testclient import TestClient

load_dotenv()

TOKEN_EXPIRY_MINUTES=int(os.getenv("TOKEN_EXPIRY_MINUTES"))
AUTH_CODE_EXPIRY_MINUTES=int(os.getenv("AUTH_CODE_EXPIRY_MINUTES"))



# load templates folder to environment (security measure)
env = Environment(loader=PackageLoader('app', 'templates'))


origins = [
    "http://localhost",
    "http://localhost:8080"
]

TESTING = os.environ.get("TESTING", 0)

SECRET_KEY = os.environ.get("SECRET_KEY", "1234567890")

temp_cred_list = list()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="/templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AuthCode(BaseModel):
    user: schemas.UserCreate
    auth_code: int
    timestamp: int
    change: str = None

client = TestClient(app)

@app.on_event("startup")
@repeat_every(seconds=86390, wait_first=True)
def periodic():
    if TESTING == "0":
        today = datetime.today()
        if today.day==1:
            test_response=client.get("/getSettings/?user_id=-1&token="+SECRET_KEY)
            data = test_response.json()
            if data["auto_invoice"]==True:
                url ="/closePeriod/?admin_id=-1&token="+SECRET_KEY
                response = client.post(url,)
                data = response.json()

def checkAuthCode(check_user: schemas.VerifyMail, db: Session = Depends(get_db), new_pw: str = None):
    for entry in temp_cred_list:
        if entry.user.email==check_user.email:
            if entry.auth_code==int(check_user.auth_code):
                curr_dt = datetime.now()
                timestamp = int(round(curr_dt.timestamp()))
                if timestamp-entry.timestamp<AUTH_CODE_EXPIRY_MINUTES*60:
                    if entry.change=="yes":
                        if new_pw==None:
                            print("No new password given!")
                            return False
                        temp_mail = entry.user.email
                        temp_cred_list.remove(entry)
                        return crud.update_password(db=db, user_email=temp_mail, password=new_pw)
                    else:
                        temp = entry.user
                        temp_cred_list.remove(entry)
                        return crud.create_user(db=db, user=temp)
                else:
                    temp_cred_list.remove(entry)
                    return False
    return False

def checkExpiry():
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    for entry in temp_cred_list:
        if TESTING == "1":
            if entry.timestamp != 1234567890:
                temp_cred_list.remove(entry)
        else:
            if timestamp-entry.timestamp>TOKEN_EXPIRY_MINUTES*60:
                temp_cred_list.remove(entry)

def create_FastApi_Invoice(user_name: str,user_email: str, items: list, admin_name: str, admin_email: str, admin_link:str, total: float):
    today = datetime.today().strftime("%B %-d, %Y")
    user_name_without_spaces = user_name.replace(" ", "")
    invoice_date= datetime.today().strftime("%Y%m%d")
    invoice_number = user_name_without_spaces+invoice_date
    this_folder = os.path.dirname(os.path.abspath(__file__))
    qr_path=""
    if total>0.0:
        index_template = env.get_template('invoice.html')   
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        if admin_link[-1]!="/":
            admin_link = admin_link + "/"
        total_string = str(total)
        total_string = total_string.replace(".", ",")
        admin_link_with_balance = admin_link+total_string 
        qr.add_data(admin_link_with_balance)
        qr.make(fit=True)
        qr_path= 'file://' + os.path.join(this_folder, 'templates', 'qr.png' )
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("app/templates/qr.png")
    else:
        index_template = env.get_template('credit_invoice.html')
    picture_path= 'file://' + os.path.join(this_folder, 'templates', 'es_logo_gross.jpg' ) 
    total_string = "{:.2f}".format(total)
    output_from_parsed_template = index_template.render(date= today, picture=picture_path,  user_name=user_name, admin_name=admin_name, admin_email=admin_email, items= items, total= total_string, invoice_number= invoice_number, qr_code=qr_path)
    html = HTML(string=output_from_parsed_template)  
    rendered_pdf = html.write_pdf()
    path = "app/invoices/"+user_name+today+".pdf"
    with open(path, 'wb') as f:
        f.write(rendered_pdf)
        f.close()
    # write the parsed template
    if total>0.0:
        os.remove("app/templates/qr.png")

    if TESTING == "0" and total !=0.00:
        mail.send_accounting_mail(email=user_email, name=user_name, balance=total_string, invoice=rendered_pdf, invoice_name=user_name+today+".pdf")
    return True

def checkIfAdmin(db, user_id, token):
    user = crud.get_user(db, user_id)
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    if TESTING == "1":
        if user.token!=token or user.is_admin==False or user.token_timestamp==None or user.token_timestamp!=1234567890:
            raise HTTPException(status_code=401, detail="Not authorized")
    else:
        if user.token!=token or user.is_admin==False or user.token_timestamp==None or user.token_timestamp+TOKEN_EXPIRY_MINUTES*60<int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp())):
            raise HTTPException(status_code=401, detail="Not authorized")
        crud.update_user_time_stamp(db, user_id, int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp())))
    return True

def checkIfAuthentificated(db, user_id, token):
    user = crud.get_user(db, user_id)
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    if TESTING == "1":
        if user.token!=token or user.token_timestamp==None or user.token_timestamp!=1234567890:
            raise HTTPException(status_code=401, detail="Not authorized")
    else:
        if user.token!=token or user.token_timestamp==None or user.token_timestamp+TOKEN_EXPIRY_MINUTES*60<int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp())):
            raise HTTPException(status_code=401, detail="Not authorized")
        crud.update_user_time_stamp(db, user_id, int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp())))
    return True

@app.get("/test")
def test(db: Session = Depends(get_db)):
    return crud.get_user_by_email(db, email="admin")

@app.get("/backup/")
def backup_db(action: str):
    backup.backupDB(action=action, date="2024-03-01", dest_db="fastapi_traefik", verbose=True) 
    return True

@app.get("/createBackup/",responses = {
        200: {
            "content": {"application/octet-stream": {}}
        }
    },)
def create_backup(user_id: int, token: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    compressedFile = backup.backupDB(action="backup", date=datetime.now(), dest_db="fastapi_traefik", verbose=True, nameOfBackup="") 
    return FileResponse(path=compressedFile,media_type='application/octet-stream', filename='backup.dump.gz')

@app.post("/restoreBackup/")
def restore_backup(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/gzip":
        raise HTTPException(400, detail="Invalid document type")
    try:
        file_path = f"./backups/{file.filename}" 
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            backup.backupDB(action="restoreNew", date=datetime.now(), dest_db="fastapi_traefik", verbose=True, nameOfBackup=file.filename)
        return {"message": "File saved successfully"}
    except Exception as e:
        return {"message": e.args}

@app.post("/create/", response_model=schemas.UserCreate)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    checkExpiry()
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    generatedCode = 0

    if TESTING == "1":
        generatedCode = 123456
        print(generatedCode)
    else:
        generatedCode = random.randint(100000, 999999)
        print(generatedCode)
        mail.send_auth_code(user.email, generatedCode, user.name) #TODO: activate
    entry = AuthCode(user=user, auth_code=generatedCode, timestamp=timestamp, change="no")
    temp_cred_list.append(entry)   


    #print(generatedCode)

    item = schemas.Confirm(message="success",token="0")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/resetPassword/", response_model=schemas.User)
def resetPassword(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email does not exist")
    checkExpiry()
    curr_dt = datetime.now()
    timestamp = int(round(curr_dt.timestamp()))
    generatedCode = random.randint(100000, 999999)
    if TESTING == "1":
        generatedCode = 123456
    if TESTING == "0":
        mail.send_reset_code(user.email, generatedCode, db_user.name)
    entry = AuthCode(user=user, auth_code=generatedCode, timestamp=timestamp, change="yes")
    temp_cred_list.append(entry)
    print(generatedCode)
    item = schemas.Confirm(message="success",token="0")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/verify/", response_model=schemas.VerifyMail)
def verify_user(user: schemas.VerifyMail, db: Session = Depends(get_db)):
    db_user = checkAuthCode(user, db)
    checkExpiry()
    if db_user==False:
        raise HTTPException(status_code=400, detail="Auth Code wrong or expired!")
    db_user_test = crud.get_user_by_email(db, email=db_user.email)
    if db_user_test is None:
        raise HTTPException(status_code=404, detail="User not found")
    admin_user = crud.get_admin_users(db)
    if TESTING == "0":
        for admins in admin_user:
            if admins.email!="admin":
                mail.send_admin_activation_mail(admins.email, admins.name, db_user.name)

    item = schemas.Confirm(message="success",token="1")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.patch("/updatePassword/", response_model=schemas.CheckNewPassword)
def updatePassword(user: schemas.CheckNewPassword, db: Session = Depends(get_db)):
    dummy_user=schemas.VerifyMail(email=user.email, auth_code=user.auth_code)
    db_user = checkAuthCode(dummy_user, db, user.new_pw)
    checkExpiry()
    if db_user==False:
        raise HTTPException(status_code=400, detail="Auth Code wrong or expired!")
    item = schemas.Confirm(message="success",token="1")
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/auth/", response_model=schemas.UserCheck)
def check_user(user: schemas.UserCheck, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if crud.checkPassword(user.hash_pw, db_user.hashed_password)==False:
        raise HTTPException(status_code=400, detail="Password wrong!")
    token= str(uuid4())
    timestamp=int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp()))
    if TESTING =="1":
        token=123456789
        timestamp=1234567890
    crud.update_user_token(db, db_user.id, token)
    crud.update_user_time_stamp(db, db_user.id, timestamp)
    item = schemas.Item(message="success",user_id=db_user.id, token=token, is_admin=db_user.is_admin)
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)

@app.post("/token/", response_model=schemas.Item)
def check_token(user_id: int, token: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.token!=token:
        raise HTTPException(status_code=400, detail="Token wrong!")
    if db_user.token_timestamp==None or db_user.token_timestamp+TOKEN_EXPIRY_MINUTES*60<int(round(datetime.now(pytz.timezone('Europe/Berlin')).timestamp())):
        raise HTTPException(status_code=401, detail="Token expired!")
    item = schemas.Item(message="success",user_id=db_user.id, token=token, is_admin=db_user.is_admin)
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)


@app.post("/check-account/", response_model=schemas.User)
def get_user_by_mail(user: schemas.UserBase, db: Session = Depends(get_db)):
    check_for_admin_user = crud.get_user_by_email(db, email="admin")
    if check_for_admin_user is None:
        user = schemas.UserCreateAdmin(email="admin", hash_pw="admin", name="admin", is_admin=True, is_active=True)
        crud.create_admin_user(db=db, user=user)
    check_global_settings = crud.get_global_state_settings(db)
    if check_global_settings is None:
        crud.create_global_state(db)
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
    

@app.get("/users/", response_model=list[schemas.User])
def read_users(user_id: int, token: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/products/", response_model=list[schemas.Product])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.get("/salesEntries/", response_model=list[schemas.SalesEntryWithProductName])
def read_sales_entries(user_id: int, token: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    sales_entries = crud.get_sales_entries(db, skip=skip, limit=limit)
    users = crud.get_users(db, skip=0, limit=1024)
    modifed_entries=list()
    for entry in sales_entries:
        user_name=""
        for user in users:
            if user.id==entry.user_id:
                user_name=user.name
                break
        modifed_entry=schemas.SalesEntryWithProductName(id=entry.id, user_id=entry.user_id, user_name=user_name, product_id=entry.product_id, product_name=crud.get_product(db, entry.product_id).name, price=entry.price, quantity=entry.quantity, paid=entry.paid, period=entry.period, timestamp=entry.timestamp)
        modifed_entries.append(modifed_entry)
    if modifed_entries==None:
        raise HTTPException(status_code=404, detail="User not found")
    return modifed_entries

@app.get("/salesEntriesID/", response_model=list[schemas.SalesEntryWithProductName])
def read_sales_entries_by_uid(user_id: int, token: str, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    sales_entries = crud.get_sales_entry_by_user_id(db, user_id=user_id)
    modifed_entries=list()
    for entry in sales_entries:
        modifed_entry=schemas.SalesEntryWithProductName(id=entry.id, user_id=entry.user_id,user_name="", product_id=entry.product_id, product_name=crud.get_product(db, entry.product_id).name, price=entry.price, quantity=entry.quantity, paid=entry.paid, period=entry.period, timestamp=entry.timestamp)
        modifed_entries.append(modifed_entry)
    if modifed_entries==None:
        raise HTTPException(status_code=404, detail="User not found")
    return modifed_entries

@app.post("/products/", response_model=schemas.Product)
def create_product(user_id: int, token: str, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.get_product_by_name(db, name=product.name)
    if db_product:
        raise HTTPException(status_code=400, detail="Product already exists")
    return crud.create_product(db=db, product=product)

@app.patch("/changePrice/", response_model=schemas.ProductUpdate)
def updatePrice(user_id: int, token: str, product_id: int, price: float, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.update_price(db, product_id=product_id, price=price)
    if price<0:
        raise HTTPException(status_code=400, detail="Price cannot be smaller than 0")
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/changeStock/", response_model=schemas.ProductUpdate)
def updateStock(user_id: int, token: str, product_id: int, quantity: int, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    if quantity<0:
       raise HTTPException(status_code=400, detail="Stock cannot be smaller than 0") 
    db_product = crud.update_stock(db, product_id=product_id, quantity=quantity)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/reducequantity/", response_model=schemas.ProductUpdate)
def reduceQuantity(user_id: int, token: str, product_id: int, quantity: int, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.get_product(db, product_id=product_id)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    if quantity>db_product.quantity:
        raise HTTPException(status_code=401, detail="Quantity to high!")
    db_product = crud.reduce_stock(db, product_id=product_id, quantity=quantity)
    return db_product

@app.patch("/changeName/", response_model=schemas.ProductUpdate )
def updateName(user_id: int, token: str, product_id: int, name: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.update_name(db, product_id=product_id, name=name)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return db_product

@app.patch("/changeActive/")
def updateActive(user_id: int, token: str, product_id: int, is_active: bool, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.update_active(db, product_id=product_id, is_active=is_active)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return True

@app.patch("/changeType/")
def updateType(user_id: int, token: str, product_id: int, type_of_product: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.update_type(db, product_id=product_id, type_of_product=type_of_product)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return True

@app.patch("/changeImage/")
def updateImage(user_id: int, token: str, product_id: int, image: schemas.BodyImage, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_product = crud.update_image(db, product_id=product_id, image=image.image)
    if db_product==None:
        raise HTTPException(status_code=400, detail="Product doesn't exists")
    return True

@app.patch("/changeUserStatus/", response_model=schemas.UserUpdate)
def updateUserStatus(user_id: int, token: str, change_id: int, is_active: bool, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user = crud.update_user_status(db, user_id=change_id, status=is_active)
    if db_user==None:
        raise HTTPException(status_code=400, detail="User doesn't exists")
    return db_user

@app.patch("/changeUserAdmin/", response_model=schemas.UserUpdate) 
def updateUserAdmin(user_id: int, token: str, change_id: int, is_admin: bool, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user = crud.update_user_admin(db, user_id=change_id, status=is_admin)
    if db_user==None:
        raise HTTPException(status_code=400, detail="User doesn't exists")
    return db_user

@app.post("/cart/products/")
def checkout_cart(user_id: int, token: str, q: Annotated[list[schemas.ProductBuyInfo] | None, Query()] = None, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    query_items = {"q": q}
    users =  crud.get_users(db, skip=0, limit=1024)
    admins = crud.get_admin_users(db)
    products =  crud.get_products(db, skip=0, limit=1024)
    old_prod_quantity = 0
    user_email = ""
    user_name = ""
    user_wants_email = False
    #Check for valid values
    for product in q:
        userFound=False
        productFound=False
        for user in users:
            if(user.id==product.user_id):
                userFound=True
                user_wants_email = user.mail_for_purchases
                tempPeriod = user.sales_period
                user_email = user.email
                user_name = user.name
                break
        if userFound==False:
            raise HTTPException(status_code=404, detail="User not found")
        for prodList in products:
            if(product.id==prodList.id):
                productFound=True
                if(product.quantity>prodList.quantity):
                   raise HTTPException(status_code=404, detail="Product Quantity to high!") 
                old_prod_quantity = prodList.quantity
                break
        if productFound==False:
            raise HTTPException(status_code=404, detail="Product not found")
    #Create entry and update stock  
    string_buylist = "" 
    total = 0.00 
    for product in q:
        if TESTING == "1":
            timestamp = "123"
        else:
            timestamp = str(datetime.now(pytz.timezone('Europe/Berlin')).strftime("%Y-%m-%d %H:%M:%S"))
        schema_entry=schemas.SalesEntryCreate(user_id=product.user_id, product_id=product.id, price=product.price, quantity=product.quantity, period=tempPeriod, timestamp=timestamp)
        crud.create_sales_entry(db, schema_entry)
        crud.reduce_stock(db, product_id=product.id, quantity=product.quantity)
        product_name = crud.get_product(db, product.id).name
        if user_wants_email==True:
            string_buylist+=str(product.quantity)+"x "+product_name+" for "+str(f"{product.price:.2f}")+" "
            total+=product.price*float(product.quantity)

        for admin in admins:
            if (old_prod_quantity-product.quantity)<=admin.set_warning_for_product and admin.set_warning_for_product!=-1 and old_prod_quantity>admin.set_warning_for_product and TESTING == "0":
                mail.send_product_low_stock_mail(admin.email, admin.name, product_name) 
    if user_wants_email==True and TESTING == "0":
        mail.send_buy_mail(user_email, user_name, string_buylist, str(f"{total:.2f}"))
    return query_items

@app.get("/userData/", response_model=list[schemas.UserData])
def get_user_data(user_id: int, token: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    users = crud.get_users(db, skip=0, limit=1024)
    sales_entries = crud.get_sales_entries(db, skip=0, limit=1024)
    user_data = list()
    for user in users:
        open_balances = crud.get_open_balances(db, user.id)
        last_turnover = open_balances
        actual_turnover = 0.0 
        period = int(user.sales_period)
        paid = False
        for entry in sales_entries:
            if entry.user_id==user.id:
                if int(entry.period)==period-1:
                    last_turnover+=entry.price*float(entry.quantity)
                    if entry.paid==True and open_balances==0.0:
                        paid=True
                    else:
                        paid=False
                if int(entry.period)==period:
                    actual_turnover+=entry.price*float(entry.quantity)
        if last_turnover<=0.0:
            paid=True
        user_data.append(schemas.UserData(id=user.id, email=user.email, is_active=user.is_active, is_admin=user.is_admin, sales_period=user.sales_period, name=user.name, last_turnover=last_turnover, paid=paid, actual_turnover=actual_turnover, open_balances=user.open_balances))
    return user_data

@app.patch("/changePayPalLink/")
def set_paypal_link(user_id: int, token: str, link: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    crud.set_paypal_link(db, link)
    return True

@app.post("/closePeriod/")
def close_period(admin_id: int, token: str, db: Session = Depends(get_db)) :
    if admin_id==-1 and token==SECRET_KEY:
        print("Period closed")
        admin = crud.get_user(db, 1)
    else:
        admin = crud.get_user(db, admin_id)
        checkIfAdmin(db, admin_id, token)    
    users = crud.get_users(db, skip=0, limit=1024)
    sales_entries = crud.get_sales_entries(db, skip=0, limit=1024)
    class Item():
        name: str
        price_per_unit: float
        quantity: int
        total_price: float

    for user in users:
        list_items = list()
        last_unpaid_turnover = crud.get_open_balances(db, user.id)
        period = int(user.sales_period)
        for entry in sales_entries:
            if entry.user_id==user.id:
                if int(entry.period)==period-1 and entry.paid==False:
                    last_unpaid_turnover+=entry.price*float(entry.quantity)
                    """entry.paid=True
                    crud.change_paid(db, entry.id, True)"""
                if entry.invoiced==False:
                    if len(list_items)==0:
                        temp = Item()
                        temp.name=crud.get_product(db, entry.product_id).name
                        temp.price_per_unit=entry.price
                        temp.quantity=entry.quantity
                        temp.total_price=entry.price*float(entry.quantity)
                        list_items.append(temp)
                    else:
                        for item in list_items:
                            temp_name = crud.get_product(db, entry.product_id).name
                            if item.name==temp_name and item.price_per_unit==entry.price:
                                item.quantity+=entry.quantity
                                item.total_price+=entry.price*float(entry.quantity)
                            else:
                                temp = Item()
                                temp.name=temp_name
                                temp.price_per_unit=entry.price
                                temp.quantity=entry.quantity
                                temp.total_price=entry.price*float(entry.quantity)
                                list_items.append(temp)
                    crud.change_invoiced(db, entry.id, True)
        
        total_turnover = sum([i.total_price for i in list_items])       
        if last_unpaid_turnover!=0.0:
            crud.update_open_balances(db, user.id, round(last_unpaid_turnover,2))
            temp = Item()
            temp.name="Open Balances"
            temp.price_per_unit=0.00
            temp.quantity=1
            temp.total_price=last_unpaid_turnover
            list_items.append(temp)
        user_balance = total_turnover+last_unpaid_turnover
        if user_balance<=0.0 and total_turnover!=0.0:
            for entry in sales_entries:
                if entry.user_id==user.id and entry.paid==False and entry.invoiced==True:
                    crud.change_paid(db, entry.id, True)
            crud.update_open_balances(db, user.id, round(user_balance,2))

        class StringItem():
            name: str
            price_per_unit: str
            quantity: str
            total_price: str
        if len(list_items)!=0:
            string_items = list()
            for item in list_items:
                temp = StringItem()
                temp.name=item.name
                temp.price_per_unit=str(f"{item.price_per_unit:.2f}")
                temp.quantity=str(item.quantity)
                temp.total_price=str(f"{item.total_price:.2f}")    
                string_items.append(temp) 
            json_items = jsonable_encoder(string_items)#to be changed
            paypal_link = crud.get_global_state_settings(db).paypal_link
            create_FastApi_Invoice(user.name, user.email, json_items, admin.name, admin.email, paypal_link, user_balance )
        crud.increase_sales_period(db, user.email)

@app.patch("/changePaid/")
def change_paid(user_id: int, token: str, change_id: int, paid: bool, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    sales_entries = crud.get_sales_entry_by_user_id(db, change_id)
    crud.update_open_balances(db, change_id, 0.0)
    for entry in sales_entries:
        if entry.invoiced==True:
            crud.change_paid(db, entry.id, paid)
    return True

@app.post("/sendMoney/")
def send_money(user_id: int, token:str, email:str, amount: float, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    user = crud.get_user(db, user_id)
    if user.email==email:
        raise HTTPException(status_code=400, detail="You cannot send money to yourself")
    empf = crud.get_user_by_email(db, email)
    if user==None or empf==None:
        raise HTTPException(status_code=404, detail="User not found")
    if amount<0.0:
        raise HTTPException(status_code=400, detail="Amount cannot be smaller than 0")
    old_amount= crud.get_open_balances(db, user_id)
    crud.update_open_balances(db, user_id, old_amount+amount)
    old_amount= crud.get_open_balances(db, empf.id)
    crud.update_open_balances(db, empf.id, old_amount-amount)
    if old_amount-amount<=0.0:
        sales_entries = crud.get_sales_entry_by_user_id(db, empf.id)
        for entry in sales_entries:
            if entry.paid==False and entry.invoiced==True:
                crud.change_paid(db, entry.id, True)
    return True

@app.post("/addOpenBalances/")
def add_open_balances(user_id: int, token: str, change_id:int, amount: float, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    user = crud.get_user(db, change_id)
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    old_amount= crud.get_open_balances(db, change_id)
    new_amount= old_amount-amount
    crud.update_open_balances(db, change_id, new_amount)
    if new_amount<=0.0:
        sales_entries = crud.get_sales_entry_by_user_id(db, change_id)
        for entry in sales_entries:
            if entry.paid==False and entry.invoiced==True:
                crud.change_paid(db, entry.id, True)
    return True

@app.get("/getSettings/")
def get_settings(user_id: int, token: str, db: Session = Depends(get_db)):
    if user_id==-1 and token==SECRET_KEY:
        db_user=crud.get_user(db, 1)
        print("check_for_admin_user")
    else:
        checkIfAuthentificated(db, user_id, token)
        db_user=crud.get_user(db, user_id)
    if db_user.is_admin==True:
        admin_settings = crud.get_global_state_settings(db)
        if admin_settings.paypal_link==None:
            admin_settings.paypal_link=""
        settings = schemas.AdminSettings(mail_for_purchases=db_user.mail_for_purchases, confirmation_prompt=db_user.confirmation_prompt, auto_invoice=admin_settings.auto_invoice, paypal_link=admin_settings.paypal_link, set_warning_for_product=db_user.set_warning_for_product)
    else:
        settings = schemas.UserSettings(mail_for_purchases=db_user.mail_for_purchases, confirmation_prompt=db_user.confirmation_prompt)
    return settings

@app.patch("/change_mail_for_purchases/")
def change_mail_for_purchases(user_id: int, token: str, mail_for_purchases: bool, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    crud.update_mail_for_purchases(db, user_id, mail_for_purchases)
    return True

@app.patch("/change_confirmation_prompt/")
def change_confirmation_prompt(user_id: int, token: str, confirmation_prompt: bool, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    crud.update_confirmation_prompt(db, user_id, confirmation_prompt)
    return True

@app.patch("/change_auto_invoice/")
def change_auto_invoice(user_id: int, token: str, auto_invoice: bool, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    crud.update_auto_invoice(db, auto_invoice)
    return True

@app.patch("/change_set_warning_for_product/")
def change_set_warning_for_product(user_id: int, token: str, set_warning_for_product: int, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    crud.update_set_warning_for_product(db, user_id, set_warning_for_product)
    return True

@app.patch("/updateNewPassword/")
def update_password(user: schemas.UserPasswordUpdate, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user.user_id, user.token)
    db_user= crud.get_user(db, user.user_id)
    crud.update_password(db, db_user.email, user.password)
    return True

@app.patch("/changePassword/")
def change_password_of_user(user_id: int, token: str, user: schemas.AdminPasswordChange, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user= crud.get_user(db, user.change_id)
    if db_user==None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.update_password(db, db_user.email, user.password)
    return True

@app.patch("/changeNameUser/")
def change_name_of_user(user_id: int, token: str, change_id: int, name: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user= crud.get_user(db, change_id)
    if db_user==None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.update_name_user(db, change_id, name)
    return True

@app.patch("/changeEmail/")
def change_email(user_id: int, token: str, change_id: int, email: str, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user= crud.get_user(db, change_id)
    if db_user==None:
        raise HTTPException(status_code=404, detail="User not found")
    if crud.get_user_by_email(db, email)!=None:
        raise HTTPException(status_code=400, detail="Email already registered")
    crud.update_email(db, change_id, email)
    return True

@app.patch("/logout/")
def logout(user_id: int, token: str, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    crud.update_user_token(db, user_id, "-1")
    return True

@app.get("/products/oneSort/")
def read_one_sort(sort: str, db: Session = Depends(get_db)):
    products = crud.get_one_sort(db, sort)
    return products

@app.post("/singleCheckOut/")
def single_checkout(user_id: int, token: str, product_id: int, db: Session = Depends(get_db)):
    checkIfAuthentificated(db, user_id, token)
    user =  crud.get_user(db, user_id)
    product =  crud.get_product(db, product_id)
    admins = crud.get_admin_users(db)
    old_prod_quantity = product.quantity
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    if product==None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.quantity<=0:
        raise HTTPException(status_code=404, detail="Product not available")
    tempPeriod = user.sales_period
    if TESTING == "1":
        timestamp = "123"
    else:
        timestamp = str(datetime.now(pytz.timezone('Europe/Berlin')).strftime("%Y-%m-%d %H:%M:%S"))
    schema_entry=schemas.SalesEntryCreate(user_id=user_id, product_id=product.id, price=product.price, quantity=1, period=tempPeriod, timestamp=timestamp)
    crud.create_sales_entry(db, schema_entry)
    crud.reduce_stock(db, product_id=product.id, quantity=1)
    for admin in admins:
        if (old_prod_quantity-1)<=admin.set_warning_for_product and admin.set_warning_for_product!=-1 and old_prod_quantity>admin.set_warning_for_product and TESTING == "0":
                mail.send_product_low_stock_mail(admin.email, admin.name, product.name) 
    if user.mail_for_purchases==True and TESTING == "0":
        mail.send_buy_mail(user.email, user.name, product.name, str(f"{product.price:.2f}"))
    return True

@app.get("/products/avaiable/")
def read_avaiable(db: Session = Depends(get_db)):
    products = crud.get_active_products(db)
    return products

@app.post("/new-user/")
def create_new_user(user_id: int, token: str,user: schemas.UserCreate, db: Session = Depends(get_db)):
    checkIfAdmin(db, user_id, token)
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/closePeriodForUser/")
def close_period(admin_id: int, token: str, change_id: int, db: Session = Depends(get_db)) :
    admin = crud.get_user(db, admin_id)
    checkIfAdmin(db, admin_id, token)
    user = crud.get_user(db, change_id)
    if user==None:
        raise HTTPException(status_code=404, detail="User not found")
    sales_entries = crud.get_sales_entries(db, skip=0, limit=1024)
    class Item():
        name: str
        price_per_unit: float
        quantity: int
        total_price: float

    list_items = list()
    last_unpaid_turnover = crud.get_open_balances(db, user.id)
    period = int(user.sales_period)
    for entry in sales_entries:
        if entry.user_id==user.id:
            if int(entry.period)==period-1 and entry.paid==False:
                last_unpaid_turnover+=entry.price*float(entry.quantity)
            if entry.invoiced==False:
                if len(list_items)==0:
                    temp = Item()
                    temp.name=crud.get_product(db, entry.product_id).name
                    temp.price_per_unit=entry.price
                    temp.quantity=entry.quantity
                    temp.total_price=entry.price*float(entry.quantity)
                    list_items.append(temp)
                else:
                    for item in list_items:
                        temp_name = crud.get_product(db, entry.product_id).name
                        if item.name==temp_name and item.price_per_unit==entry.price:
                            item.quantity+=entry.quantity
                            item.total_price+=entry.price*float(entry.quantity)
                        else:
                            temp = Item()
                            temp.name=temp_name
                            temp.price_per_unit=entry.price
                            temp.quantity=entry.quantity
                            temp.total_price=entry.price*float(entry.quantity)
                            list_items.append(temp)
                crud.change_invoiced(db, entry.id, True)
    
    total_turnover = sum([i.total_price for i in list_items])   
    if last_unpaid_turnover!=0.0: 
        crud.update_open_balances(db, user.id, round(last_unpaid_turnover,2))
        temp = Item()
        temp.name="Open Balances"
        temp.price_per_unit=0.00
        temp.quantity=1
        temp.total_price=last_unpaid_turnover
        list_items.append(temp)
    user_balance = total_turnover+last_unpaid_turnover
    if user_balance<=0.0 and total_turnover!=0.0:
        for entry in sales_entries:
            if entry.user_id==user.id and entry.paid==False and entry.invoiced==True:
                crud.change_paid(db, entry.id, True)
        crud.update_open_balances(db, user.id, round(user_balance,2))

    class StringItem():
            name: str
            price_per_unit: str
            quantity: str
            total_price: str
    if len(list_items)!=0:
        string_items = list()
        for item in list_items:
            temp = StringItem()
            temp.name=item.name
            temp.price_per_unit=str(f"{item.price_per_unit:.2f}")
            temp.quantity=str(item.quantity)
            temp.total_price=str(f"{item.total_price:.2f}")    
            string_items.append(temp) 
        json_items = jsonable_encoder(string_items)#to be changed
        paypal_link = crud.get_global_state_settings(db).paypal_link
        create_FastApi_Invoice(user.name, user.email, json_items, admin.name, admin.email, paypal_link, user_balance )
    crud.increase_sales_period(db, user.email)