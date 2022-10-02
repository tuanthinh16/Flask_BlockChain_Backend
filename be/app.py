from crypt import methods
from mimetypes import init
from flask import Flask,request,Response,json
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime,timedelta
import hashlib
import jwt

#loads model
from models.account import Account,AccountDTO 
from models.book import Book




app = Flask(__name__)
cors = CORS(app,resources={r"/api/*": {"origin": "*"}})


client = MongoClient("localhost:27017")
db = client.DATN_data

token = ''
isLogin = False

@app.route('/api/')
def index():
    return "thinh vip pro"
#------------------------account-------------------------------
@app.route('/api/register',methods =['Post'])
def register():
    userID = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    fname = request.form['fname']
    username = request.form['username']
    password = request.form['password']
    hash_password = hashlib.sha256(password.encode('utf8')).hexdigest()
    email = request.form['email']
    isExisted = False
    timecreated = datetime.now()
    for user in db.user.find():
        if username == user['username']:
            isExisted = True
        else: isExisted = False
    if not isExisted:
        acc = Account(fname,username,hash_password,email,'','',timecreated)
        account = {'_id':userID,'fname':fname,'username':username,'password':hash_password,'email':email,'address':'','phone':'','timecreated':timecreated}
        response = db.user.insert_one(account)
        create_wallet(username)
        return Response(
            response = json.dumps({"response":"create account successfully ","data":acc.visible()}),
            status = 200,
            mimetype = "application/json",
        )
    else:
        return Response(
            response = "Username has been availd, please chose another username and try again. ",
            status = 401,
            mimetype = "application/json",
        )
app.route('/api/login', methods = ['POST'])
def login():
    global token
    global isLogin
    username = request.form['username']
    password = request.form['password']
    user =  db.user.find_one({"username":username})
    print(user)
    if hashlib.sha256(password.encode('utf8')).hexdigest() == (user['password']):
        isLogin = True
        print(hashlib.sha256(password.encode('utf8')).hexdigest())
        token = generate_token(username)
        data_response = json.dumps({"response_data":"Login successfully","token":token})
        status = 200
    else:
        data_response = "Wrong password"
        status = 401,
        
        
    return Response(
        response=data_response,
        status=status,
        mimetype = "application/json",
    )

#---------------------------------------- wallet----------------------------------------
def create_wallet(username):
    walletid = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    address = hashlib.sha256(username.encode('utf8')).hexdigest()
    balance = 0
    wallet = {'_id':walletid,'address':address,'username':username,'balance':balance,'timeCreated':datetime.now()}
    res = db.wallet.insert_one(wallet)
    return res
def add_balance(username,balance):
    db.wallet.update_one({'username':username},{"$set":{'balance':balance}})

#---------------------------books--------------------------
@app.route('/api/add-book',methods=['POST'])
def add_book():
    bookid = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    namebook = request.form['name']
    typebook = request.form['type']
    countrybook = request.form['country']
    nxb = request.form['nxb']
    datexb = request.form['date']
    sl = request.form['sl']
    username = request.form['username']
    timestamp = datetime.now()
    isExisted = False
    book = Book(bookid,namebook,typebook,countrybook,nxb,datexb,sl,username,timestamp)
    books = {'_id':bookid,'name':namebook,'type':typebook,'country':countrybook,'nxb':nxb,'datexb':datexb,'sl':sl,'username':username,'timestamp':timestamp}
    for i in db.book.find():
        if bookid == i['_id']:
            isExisted = True
        else: isExisted = False
    if not isExisted:
        db.book.insert_one(books)
        return Response(
            response = json.dumps({'data': " add book successfully"}),
            status= 200,
            mimetype='application/json',
            )
    else:
        return Response(
            response = json.dumps({'data': " add book NOT successfully. Book is vaild"}),
            status= 401,
            mimetype='application/json',
            )
@app.route('/api/book/sell-book/<string:bookid>',methods =['POST'])
def sell_book(bookid):
    if isLogin:
        booksellID = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
        amount = request.form['amount']
        username = decode_auth_token(token)
        price = request.form['price']
        timestamp = datetime.now()
        isExisted = False
        for i in db.bookSell.find():
            if booksellID == i['booksellID']:
                isExisted = True
            else: isExisted = False
        bookSell = {'_id':booksellID, 'amount':amount, 'price':price, 'timestamp':timestamp,'bookid':bookid,'username':username}
        if not isExisted:
            if check_vaild_book(bookid):
                db.bookSell.insert_one(bookSell)
                response = json.dump({'data':' Add book to market successfully'})
                status = 200
            else:
                response = json.dump({'data':' Book has not been added to market successfully'})
                status = 400
    else:
        response = "Must be Login first"
        status =401
    return Response(
        response= response,
        status=status,
        mimetype='application/json',
    )

def check_vaild_book(bookid):
    if db.book.find_one({'_id':bookid}):
        return True
    else: return False






#------------------------------------token---------------------------------
def generate_token(username):
    SECRET_KEY="""\xf9'\xe4p(\xa9\x12\x1a!\x94\x8d\x1c\x99l\xc7\xb7e\xc7c\x86\x02MJ\xa0"""
    try:
        payload = {
            'exp': datetime.now() + timedelta(days=0, seconds=5),
            'iat': datetime.now(),
            'sub': username
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return e
def decode_auth_token(auth_token):
    SECRET_KEY="""\xf9'\xe4p(\xa9\x12\x1a!\x94\x8d\x1c\x99l\xc7\xb7e\xc7c\x86\x02MJ\xa0"""
    try:
        payload = jwt.decode(auth_token, options={"verify_signature": False})
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
