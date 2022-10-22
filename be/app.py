from flask import Flask,request,Response,json
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime,timedelta
import hashlib
import jwt
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import upload
import cloudinary.api
from cloudinary.utils import cloudinary_url

#loads model
from models.account import Account,AccountDTO 
from models.book import Book
from models.block import Block
from models.blockchain import Block_Chain
from models.history import History




app = Flask(__name__)
cors = CORS(app,resources={r"/api/*": {"origin": "*"}})


client = MongoClient("localhost:27017")
db = client.DATN_data
cloudinary.config(cloud_name = 'dwweabf16', api_key='723518173222341', 
api_secret='KMNHUvnxM7qGRMyNSVVJdC1lQS8')

token = ''
isLogin = False

@app.route('/api/')
def index():
    return "thinh vip pro"
#-----------------------------------------account--------------------------------------------------------------------------
@app.route('/api/register',methods =['POST'])
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
        account = {'_id':userID,'fname':fname.upper(),'username':username,'password':hash_password,'email':email,'address':'','phone':'','timecreated':timecreated}
        response = db.account.insert_one(account)
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
@app.route('/api/login', methods = ['POST'])
def login():
    global token
    global isLogin
    username = request.form['username']
    password = request.form['password']
    user =  db.account.find_one({"username":username})
    # print(user)
    if hashlib.sha256(password.encode('utf8')).hexdigest() == (user['password']):
        isLogin = True
        # print(hashlib.sha256(password.encode('utf8')).hexdigest())
        token = generate_token(username)
        # print(token)
        data_response = json.dumps({"response_data":"Login successfully","token":token})
        status = 200
    else:
        data_response = "Wrong password"
        status = 401
    return Response(
        response=data_response,
        status=status,
        mimetype = "application/json",
    )
@app.route('/api/getinfo/<string:username>',methods =['GET'])
def getinfo(username):
    if  isLogin:
        for item in db.account.find({'username': username}):
            acc = AccountDTO(item['fname'],item['email'],item['address'],item['phone'],item['timecreated'])
            address,balance = getwalletbyusername(username)
            return Response(
                response = json.dumps({"response":"get account successfully ","data":acc.visible(),"address-wallet":address,"balance":balance}),
                status = 200,
                mimetype = "application/json",
            )
    else:
        return Response(
            response = "Please login",
            status = 400,
            mimetype = "application/json",
        )

@app.route('/api/profile/get-work/<string:username>', methods=['GET'])
def get_work(username):
    response = ''
    status = 401
    listwork= []
    if isLogin:
        for i in db.history_user.find({'username': username}):
            # histories = History(i['_id'], i['username'],i['blockID'],i['hash'],i['methods'],i['timestamp'],getaddressbyusername(i['fromusr']),i['value'],getaddressbyusername(i['to']))
            listwork.append(i)
        response = json.dumps({"response":"get account successfully ","data":listwork})
        status = 200
    else:
            response = "Please login"
            status = 400
    return Response(
        response = response,
        status = status,
        mimetype="application/json",
    )
def getaddressbyusername(username):
    if username == "admin":
        return "admin"
    else:
        for i in db.wallet.find({'username': username}):
            return i['address']
def getwalletbyusername(username):
    if username == "admin":
        return "admin",0
    else:
        for i in db.wallet.find({'username': username}):
            return i['address'], i['balance']

#---------------------------------------------block chain----------------------------------------------------------------
def add_block(username,type,value,bookName,fromusr,to):
    timestamp = datetime.now()
    if type == "create":
        data = " "+str(username)+" "+str(type)+" wallet at "+str(timestamp)
    elif type =="give":
        data = " "+str(username)+" "+str(type)+" "+str(value)+" "+str(bookName)+" to"+str(to)
    elif type == "receive":
        data = " "+str(username)+" "+str(type)+" "+str(value)+" "+str(bookName) + "from "+str(fromusr)
    else:
        data = " "+str(username)+" "+str(type)+" "+str(value)+" "+str(bookName)
    listID =[]
    currentID = 0
    for block in db.block.find():
        listID.append(block['_id'])
    if len(listID) >1:
        currentID = max(listID)
    block = Block(currentID + 1,timestamp,data)
    #get last block
    for item in db.block.find({'_id': currentID}):
        block.pre_hash = item['hash']
    block.hash = block.mine_block(Block_Chain.dificulty)
    blc = {'_id':block.blockID,'prehash':block.pre_hash,'data':block.data,'timestamp':block.timestamp,'hash':block.hash}
    db.block.insert_one(blc)
    history = {'_id':(datetime.now().microsecond + datetime(1970, 1, 1).microsecond),'username':username,'blockID':block.blockID,'hash':block.hash,'methods':type,'timestamp':block.timestamp,'fromusr':fromusr,'value':value,'to':to}
    db.history_user.insert_one(history)
    return Response(
        response = json.dumps({"Block":block.blockID,
        "hash":  block.hash,
        "data transfer": block.data,
        "Pre_hash": block.pre_hash,
        "time transfer":block.timestamp,}),
        status = 200,
        mimetype='application/json',
    )

#------------------------------------------------ wallet-----------------------------------------------------------------------
def create_wallet(username):
    walletid = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    address = hashlib.md5(username.encode('utf8')).hexdigest()
    balance = 0
    wallet = {'_id':walletid,'address':address,'username':username,'balance':balance,'timeCreated':datetime.now()}
    res = db.wallet.insert_one(wallet)
    add_block(username,"create",0,0,'admin',username)
    return res
def add_balance(username,balance):
    db.wallet.update_one({'username':username},{"$set":{'balance':balance}})

#-----------------------------------------------books------------------------------------------------------------------
@app.route('/api/add-book',methods=['POST'])
def add_book():
    if isLogin:
        username = decode_auth_token(token)
        bookid = request.form['id']
        namebook = request.form['name']
        typebook = convertType(request.form['type'])
        detail = request.form['detail']
        countrybook = convertCountry(request.form['country'])
        nxb = request.form['nxb']
        datexb = request.form['date']
        sl = request.form['sl']
        timestamp = datetime.now()
        isExisted = False
        add_block(username,"add_book",sl,namebook,bookid,username)
        add_book_amount(namebook,sl,bookid)
        book = Book(bookid,namebook,typebook,detail,countrybook,nxb,datexb,sl,username,timestamp)
        books = {'_id':bookid,'name':namebook,'type':typebook,'detail':detail,'country':countrybook,'nxb':nxb,'datexb':datexb,'sl':sl,'username':username,'timestamp':timestamp}
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
    else:
        return Response(
                response = "Please login",
                status= 400,
                mimetype='application/json',
                )
def convertType(type):
    rs = ''
    if type == 'cate-action':
        rs = 'menu.categories-action'
    elif type == 'cate-art':
        rs = 'menu.categories-art'
    elif type == 'cate-business':
        rs = 'menu.categories-business'
    elif type == 'cate-computer':
        rs = 'menu.categories-computer'
    elif type == 'cate-history':
        rs = 'menu.categories-history'
    elif type == 'cate-entertainment':
        rs = 'menu.categories-entertainment'
    elif type == 'cate-sport':
        rs = 'menu.categories-sport'
    elif type == 'cate-travel':
        rs = 'menu.categories-travel'
    elif type == 'cate-teen':
        rs = 'menu.categories-teen'
    elif type == 'cate-other':
        rs = 'menu.categories-other'
    return rs
def convertCountry(country):
    rs = ''
    if country == 'country-vn':
        rs = 'menu.lan-vi'
    elif country == 'country-france':
        rs ='menu.country-france'
    elif country == 'country-usa':
        rs = 'menu.country-usa'
    return rs
def add_book_amount(bookname, amount,IDBook):
    id = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    name = hashlib.md5(bookname.lower().encode('utf8')).hexdigest()
    isExisted = False
    currentAmount = 0
    if db.book_amount.find({'bookname':name}):
        isExisted = True
    else:
        isExisted = False
    if not isExisted:
        bookamount={"_id":id,'bookname':name,'amount':amount,'idBook':IDBook}
        db.book_amount.insert_one(bookamount)
    else:
        for i in db.book_amount.find({'bookname':name}):
            currentAmount +=int(i['amount'])
        db.book_amount.update_one({'bookname':name},{"$set":{'amount':currentAmount}})

def get_book_address_amount(bookID):
    for i in db.book_amount.find({'idBook':bookID}):
        return i['bookname'],i['amount']

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
@app.route('/api/book/add-image', methods=['POST'])
def addimages():
    upload_result = None
    id = (datetime.now().microsecond + datetime(1970, 1, 1).microsecond)
    idBook = request.form['id']
    fileImages = request.files['fileIMG']
    filename = secure_filename(fileImages.filename)
    if fileImages:
        upload_result = cloudinary.uploader.upload(fileImages)
        # print(upload_result)
    images = {'_id':id,'idBook':idBook,'filename':filename,'url':upload_result["secure_url"]}
    db.Images_book.insert_one(images)
    return Response(
        response = upload_result,
        status = 200,
        mimetype= "application/json",
    )
def check_vaild_book(bookid):
    if db.book.find_one({'_id':bookid}):
        return True
    else: return False
@app.route('/api/book/profile/<string:id>',methods=['GET'])
def getInfobook(id):
    book = Book()
    if db.book.find({'_id':id}):
        for i in db.book.find({'_id':id}):
            book.id = id
            book.name = i['name']
            book.type = i['type']
            book.detail = i['detail']
            book.country = i['country']
            book.nxb = i['nxb']
            book.datexb = i['datexb']
            book.sl = i['sl']
            book.timestamp = i['timestamp']
            book.username =i['username']
        imageURL = getImageFromID(id)
        response = json.dumps({'data':book.visible(),"url":imageURL})
        status = 200
    else:
        response = " Not Found"
        status = 400
    return Response(
        response=response,
        status=status,
        mimetype='application/json'
    )
def getImageFromID(bookid):
    for i in db.Images_book.find({'idBook':bookid}):
        return i['url']

#---------------------------------------------------token------------------------------------------------------
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


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['DEBUG'] = True
    app.testing = True
    app.run(host='0.0.0.0', port=443, debug=True)