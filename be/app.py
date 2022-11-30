from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import jwt
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import upload
import cloudinary.api
from cloudinary.utils import cloudinary_url

# loads model
from models.account import Account, AccountDTO
from models.book import Book
from models.block import Block
from models.blockchain import Block_Chain
from models.history import History


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origin": "*"}})


client = MongoClient("localhost:27017")
db = client.Data
cloudinary.config(
    cloud_name="dwweabf16",
    api_key="723518173222341",
    api_secret="KMNHUvnxM7qGRMyNSVVJdC1lQS8",
)

token = ""
isLogin = False
book_delete = []


@app.route("/api/")
def index():
    return "thinh vip pro"


# -----------------------------------------account--------------------------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    userID = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    fname = request.form["fname"]
    username = request.form["username"]
    password = request.form["password"]
    hash_password = hashlib.sha256(password.encode("utf8")).hexdigest()
    email = request.form["email"]
    isExisted = False
    timecreated = datetime.now()
    for user in db.user.find():
        if username == user["username"]:
            isExisted = True
        else:
            isExisted = False
    if not isExisted:
        acc = Account(fname, username, hash_password, email, "", "", timecreated)
        account = {
            "_id": userID,
            "fname": fname.upper(),
            "username": username,
            "password": hash_password,
            "email": email,
            "address": "",
            "phone": "",
            "timecreated": timecreated,
        }
        response = db.account.insert_one(account)
        create_wallet(username)
        return Response(
            response=json.dumps(
                {"response": "create account successfully ", "data": acc.visible()}
            ),
            status=200,
            mimetype="application/json",
        )
    else:
        return Response(
            response="Username has been availd, please chose another username and try again. ",
            status=401,
            mimetype="application/json",
        )


@app.route("/api/login", methods=["POST"])
def login():
    global token
    global isLogin
    username = request.form["username"]
    password = request.form["password"]
    user = db.account.find_one({"username": username})
    # print(user)
    if hashlib.sha256(password.encode("utf8")).hexdigest() == (user["password"]):
        isLogin = True
        # print(hashlib.sha256(password.encode('utf8')).hexdigest())
        token = generate_token(username)
        # print(token)
        data_response = json.dumps(
            {"response_data": "Login successfully", "token": str(token)}
        )
        status = 200
    else:
        data_response = "Wrong password"
        status = 401
    return Response(
        response=data_response,
        status=status,
        mimetype="application/json",
    )


@app.route("/api/logout", methods=["POST"])
def logout():
    global isLogin
    global token
    token = ""
    isLogin = False
    return Response(
        response="Logout Successfull", status=200, mimetype="application/json"
    )


@app.route("/api/getinfo/<string:username>", methods=["GET"])
def getinfo(username):
    if isLogin:
        for item in db.account.find({"username": username}):
            acc = AccountDTO(
                item["fname"],
                item["email"],
                item["address"],
                item["phone"],
                item["timecreated"],
            )
            address, balance = getwalletbyusername(username)
            return Response(
                response=json.dumps(
                    {
                        "response": "get account successfully ",
                        "data": acc.visible(),
                        "address-wallet": address,
                        "balance": balance,
                    }
                ),
                status=200,
                mimetype="application/json",
            )
    else:
        return Response(
            response="Please login",
            status=400,
            mimetype="application/json",
        )


@app.route("/api/profile/get-work/<string:username>", methods=["GET"])
def get_work(username):
    response = ""
    status = 401
    listwork = []
    if isLogin:
        for i in db.history_user.find({"username": username}):
            # histories = History(i['_id'], i['username'],i['blockID'],i['hash'],i['methods'],i['timestamp'],getaddressbyusername(i['fromusr']),i['value'],getaddressbyusername(i['to']))
            listwork.append(i)
        response = json.dumps(
            {"response": "get account successfully ", "data": listwork}
        )
        status = 200
    else:
        response = "Please login"
        status = 400
    return Response(
        response=response,
        status=status,
        mimetype="application/json",
    )


def getaddressbyusername(username):
    if username == "admin":
        return "admin"
    else:
        for i in db.wallet.find({"username": username}):
            return i["address"]


def getwalletbyusername(username):
    if username == "admin":
        return "admin", 0
    else:
        for i in db.wallet.find({"username": username}):
            return i["address"], i["balance"]


@app.route("/api/account/edit", methods=["POST"])
def onEdit():
    res = ""
    st = 404
    if isLogin:
        username = decode_auth_token(token)
        phone = request.form["phone"]
        address = request.form["dc"]
        email = request.form["email"]
        db.account.update_one(
            {"username": username},
            {"$set": {"address": address, "phone": phone, "email": email}},
        )
        res = "Successfull"
        st = 200
    else:
        res = " Must be login"
        st = 401
    return Response(response=res, status=st, mimetype="application/json")


# ---------------------------------------------block chain----------------------------------------------------------------
def add_block(username, type, value, bookName, fromusr, to, role):
    timestamp = datetime.now()
    if role == 0:  # user
        if type == "create":
            data = (
                " " + str(username) + " " + str(type) + " wallet at " + str(timestamp)
            )
        elif type == "give":
            data = (
                " "
                + str(username)
                + " "
                + str(type)
                + " "
                + str(value)
                + " "
                + str(bookName)
                + " to"
                + str(to)
            )
        elif type == "received":
            data = "recived " + str(value) + " from " + str(username)
        elif type == "deposit":
            data = "deposit " + str("+" + value)
        elif type == "withdraw":
            data = "withdraw " + str("-" + value)
        elif type == "buy":
            data = (
                "buy "
                + str(bookName)
                + "with  "
                + str("-" + str(value))
                + "from: "
                + str(fromusr)
            )
        elif type == "sell":
            data = "sell " + str(bookName) + "with : " + str(value)
        elif type == "sold":
            data = "sold " + str(bookName) + "with : " + str("+" + str(value))
        else:
            data = (
                " "
                + str(username)
                + " "
                + str(type)
                + " "
                + str(value)
                + " "
                + str(bookName)
            )
    else:  # book
        data = (
            " "
            + str(bookName)
            + " "
            + str(type)
            + " "
            + str(value)
            + " by "
            + str(username)
        )
    listID = []
    currentID = 0
    for block in db.block.find():
        listID.append(block["_id"])
    if len(listID) > 1:
        currentID = max(listID)
    block = Block(currentID + 1, timestamp, data)
    # get last block
    for item in db.block.find({"_id": currentID}):
        block.pre_hash = item["hash"]
    block.hash = block.mine_block(Block_Chain.dificulty)
    blc = {
        "_id": block.blockID,
        "prehash": block.pre_hash,
        "data": block.data,
        "timestamp": block.timestamp,
        "hash": block.hash,
    }
    db.block.insert_one(blc)
    if role == 0:
        history = {
            "_id": (datetime.now().microsecond + datetime(1970, 1, 1).microsecond),
            "username": username,
            "blockID": block.blockID,
            "hash": block.hash,
            "methods": type,
            "timestamp": block.timestamp,
            "fromusr": fromusr,
            "value": value,
            "to": to,
        }
        db.history_user.insert_one(history)
    else:  # book
        history = {
            "_id": (datetime.now().microsecond + datetime(1970, 1, 1).microsecond),
            "username": username,
            "blockID": block.blockID,
            "hash": block.hash,
            "methods": type,
            "timestamp": block.timestamp,
            "address": bookName,
            "value": value,
            "to": to,
        }
        db.book_history.insert_one(history)
    return Response(
        response=json.dumps(
            {
                "Block": block.blockID,
                "hash": block.hash,
                "data transfer": block.data,
                "Pre_hash": block.pre_hash,
                "time transfer": block.timestamp,
            }
        ),
        status=200,
        mimetype="application/json",
    )


@app.route("/api/block/getall", methods=["POST"])
def getblockall():
    listBlocks = []
    if isLogin:
        for i in db.block.find():
            listBlocks.append(i)
    return Response(
        response=json.dumps(listBlocks), status=200, mimetype="application/json"
    )


@app.route("/api/block/gettotal", methods=["POST"])
def gettotal_block():
    count = 0
    if isLogin:
        for i in db.block.find():
            count += 1
    return Response(response=str(count), status=200, mimetype="application/json")


# ------------------------------------------------ wallet-----------------------------------------------------------------------
@app.route("/api/wallet/gettotal", methods=["POST"])
def gettotal_wallet():
    count = 0
    if isLogin:
        for i in db.wallet.find():
            count += 1
    return Response(response=str(count), status=200, mimetype="application/json")


def create_wallet(username):
    walletid = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    address = hashlib.md5(username.encode("utf8")).hexdigest()
    balance = 0
    wallet = {
        "_id": walletid,
        "address": address,
        "username": username,
        "balance": balance,
        "timeCreated": datetime.now(),
    }
    res = db.wallet.insert_one(wallet)
    add_block(username, "create", 0, 0, "admin", username, 0)
    return res


def add_balance(username, balance):
    db.wallet.update_one({"username": username}, {"$set": {"balance": balance}})


def get_balance(username):
    for i in db.wallet.find({"username": username}):
        return int(i["balance"])


def update_wallet(username, amount):
    res = db.wallet.update_one({"username": username}, {"$set": {"balance": amount}})
    print("update wallet" + str(res))
    return res


@app.route("/api/wallet/<string:username>", methods=["POST"])
def getWalletInfo(username):
    response = ""
    status = 400
    if isLogin:
        for i in db.wallet.find({"username": username}):
            response = json.dumps(
                {
                    "id": i["_id"],
                    "address": i["address"],
                    "balance": i["balance"],
                    "time": i["timeCreated"],
                }
            )
            status = 200
    else:
        response = "Must be login"
        status = 401
    return Response(response=response, status=status, mimetype="application/json")


@app.route("/api/wallet/deposit", methods=["POST"])
def deposit():
    depositID = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    value = request.form["value"]
    email = request.form["email"]
    if isLogin:
        username = decode_auth_token(token)
        db.wallet.update_one(
            {"username": username},
            {"$set": {"balance": int(value) + int(get_balance(username))}},
        )
        add_block(username, "deposit", ("+" + value), "", "admin", username, 0)
        deposits = {
            "_id": depositID,
            "value": value,
            "username": username,
            "email": email,
        }
        db.deposit.insert_one(deposits)
        return Response(
            response="Add Sucessfully", status=200, mimetype="application/json"
        )
    else:
        return Response(
            response="Must be login", status=401, mimetype="application/json"
        )


@app.route("/api/wallet/withdraw", methods=["POST"])
def withdraw():
    address = request.form["address"]
    amount = request.form["amount"]
    if isLogin:
        username = decode_auth_token(token)
        db.wallet.update_one(
            {"username": username},
            {"$set": {"balance": int(get_balance(username) - int(amount))}},
        )
        add_block(username, "withdraw", ("+" + amount), "", username, address, 0)
        return Response(
            response="Withdraw Sucessfully", status=200, mimetype="application/json"
        )
    else:
        return Response(
            response="Must be login", status=401, mimetype="application/json"
        )


@app.route("/api/wallet/transfer/<string:username>", methods=["POST"])
def getTransfer(username):
    list = []
    if isLogin:
        for i in db.history_user.find({"username": username}):
            if (
                i["methods"] == "deposit"
                or i["methods"] == "withdraw"
                or i["methods"] == "buy"
                or i["methods"] == "sell"
                or i["methods"] == "send"
                or i["methods"] == "recived"
                or i["methods"] == "ship"
            ):
                list.append(i)
    else:
        print("Must be Login")
    return Response(
        response=json.dumps({"data": list}), status=200, mimetype="application/json"
    )


@app.route("/api/wallet/send", methods=["POST"])
def send():
    response_data = ""
    status_code = 404
    if isLogin:
        username = decode_auth_token(token)
        address = request.form["address"]
        amount = request.form["amount"]
        for i in db.wallet.find({"username": username}):
            newbalance = int(i["balance"]) - int(amount)
            update_wallet(username, newbalance)
            add_block(username, "send", ("-" + amount), "", username, address, 0)
        for i in db.wallet.find({"address": address}):
            newbal = int(i["balance"]) + int(amount)
            update_wallet(i["username"], newbal)
            add_block(
                i["username"], "recived", ("+" + amount), "", username, i["username"], 0
            )
        response_data = "Ok"
        status_code = 200
    else:
        response_data = "Must be login"
        status_code = 401
    return Response(
        response=response_data, status=status_code, mimetype="application/json"
    )


# -----------------------------------------------books------------------------------------------------------------------
@app.route("/api/add-book", methods=["POST"])
def add_book():
    if isLogin:
        username = decode_auth_token(token)
        bookid = request.form["id"]
        namebook = request.form["name"]
        typebook = convertType(request.form["type"])
        detail = request.form["detail"]
        countrybook = convertCountry(request.form["country"])
        nxb = request.form["nxb"]
        datexb = request.form["date"]
        pdf = request.form["pdf"]
        address = hashlib.md5(str(namebook).encode("utf-8")).hexdigest()
        sl = request.form["sl"]
        timestamp = datetime.now()
        isExisted = False
        add_block(username, "add", sl, address, "", "", 1)
        add_block(username, "add_book", sl, namebook, bookid, username, 0)
        add_book_amount(namebook, sl, bookid)
        book = Book(
            bookid,
            namebook,
            typebook,
            detail,
            countrybook,
            nxb,
            datexb,
            sl,
            username,
            timestamp,
        )
        books = {
            "_id": bookid,
            "name": namebook,
            "type": typebook,
            "detail": detail,
            "country": countrybook,
            "address": address,
            "nxb": nxb,
            "datexb": datexb,
            "sl": sl,
            "pdf": pdf,
            "username": username,
            "timestamp": timestamp,
        }
        for i in db.book.find():
            if bookid == i["_id"]:
                isExisted = True
            else:
                isExisted = False
        if not isExisted:
            db.book.insert_one(books)
            return Response(
                response=json.dumps({"data": " add book successfully"}),
                status=200,
                mimetype="application/json",
            )
        else:
            return Response(
                response=json.dumps(
                    {"data": " add book NOT successfully. Book is vaild"}
                ),
                status=401,
                mimetype="application/json",
            )
    else:
        return Response(
            response="Please login",
            status=400,
            mimetype="application/json",
        )


def convertType(type):
    rs = ""
    if type == "cate-business":
        rs = "Kinh Doanh"
    elif type == "cate-computer":
        rs = "Máy Tính & Công Nghệ"
    else:
        rs = "Khác"
    return rs


def convertCountry(country):
    rs = ""
    if country == "country-vn":
        rs = "Việt Nam"
    elif country == "country-france":
        rs = "Pháp"
    elif country == "country-usa":
        rs = "Mỹ"
    elif country == "country-other":
        rs = "Khác"
    return rs


def add_book_amount(bookname, amount, IDBook):
    id = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    name = hashlib.md5(bookname.lower().encode("utf8")).hexdigest()
    isExisted = False
    currentAmount = 0
    if db.book_amount.find({"bookname": name}):
        isExisted = True
    else:
        isExisted = False
    if not isExisted:
        bookamount = {"_id": id, "bookname": name, "amount": amount, "idBook": IDBook}
        db.book_amount.insert_one(bookamount)
    else:
        for i in db.book_amount.find({"bookname": name}):
            currentAmount += int(i["amount"])
        db.book_amount.update_one(
            {"bookname": name}, {"$set": {"amount": currentAmount}}
        )


def get_book_address_amount(bookID):
    for i in db.book_amount.find({"idBook": bookID}):
        return i["bookname"], i["amount"]


def get_info_book_by_id(id):
    for i in db.book.find({"_id": id}):
        return i["name"], i["nxb"], i["country"], i["detail"]


def get_url_by_id(id):
    for i in db.Images_book.find({"idBook": id}):
        return i["url"]


def update_sl_book(bookid, amount):
    for i in db.book.find({"_id": bookid}):
        if int(amount) <= int(i["sl"]):
            slnew = int(i["sl"]) - int(amount)
            res = db.book.update_one({"_id": bookid}, {"$set": {"sl": slnew}})
    return res


@app.route("/api/book/comment/get-byid/<string:id>", methods=["POST"])
def get_comment(id):
    listcmt = []
    if isLogin:
        for i in db.comment.find({"bookid": id}):
            listcmt.append(i)
    return Response(
        response=json.dumps(listcmt), status=200, mimetype="  application/json"
    )


@app.route("/api/book/comment/add", methods=["POST"])
def add_cmt():
    if isLogin:
        username = decode_auth_token(token)
        detail = request.form["detail"]
        bookid = request.form["bookid"]
        cmtID = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
        cmt = {
            "_id": cmtID,
            "username": username,
            "bookid": bookid,
            "detail": detail,
            "time": datetime.now(),
            "point": 0,
        }
        db.comment.insert_one(cmt)
    return Response(response="Successfull", status=200, mimetype="application/json")


@app.route("/api/book/comment/delete/<int:id>", methods=["POST"])
def onDelete(id):
    if isLogin:
        res = db.comment.delete_one({"_id": id})
    return Response(
        response=json.dumps({"data": str(res)}), status=200, mimetype="application/json"
    )


def get_point(id):
    if db.comment.find({"_id": id}):
        for i in db.comment.find({"_id": id}):
            return i["point"]
    else:
        return 0


@app.route("/api/book/comment/like/<int:id>", methods=["POST"])
def onLike(id):
    newpoint = int(get_point(id)) + 1
    res = db.comment.update_one({"_id": id}, {"$set": {"point": newpoint}})
    return Response(
        response=json.dumps({"data": str(res)}), status=200, mimetype="application/json"
    )


@app.route("/api/book/comment/get-point/<int:id>", methods=["POST"])
def getpoint(id):
    return json.dumps(get_point(id))


@app.route("/api/book/get-booksell-by-id/<int:id>", methods=["POST"])
def getbooksell_byid(id):
    response = ""
    status = 405
    if isLogin:
        for i in db.bookSell.find({"_id": id}):
            response = json.dumps(i)
            status = 200
    else:
        response = "Must be login"
        status = 401
    return Response(response=response, status=status, mimetype="application/json")


@app.route("/api/get-booksell-bookid/<string:id>", methods=["POST"])
def getbooksell_bybookid(id):
    response = ""
    status = 405
    if isLogin:
        for i in db.bookSell.find({"bookid": id}):
            response = i
    return Response(
        response=json.dumps(response), status=200, mimetype="application/json"
    )


@app.route("/api/book/get-url-by-id/<string:id>", methods=["GET"])
def getUrl(id):
    for i in db.Images_book.find({"idBook": id}):
        return str(i["url"])


def checkbooksell(id):
    for i in db.bookSell.find({"bookid": id}):
        return i["url"], 1
    else:
        return "", 0


@app.route("/api/book/getall", methods=["POST"])
def getall_book():
    listBook = []
    if isLogin:
        for i in db.book.find():
            listBook.append(i)
    return Response(
        response=json.dumps(listBook), status=200, mimetype="application/json"
    )


def geturl(id):
    for i in db.Images_book.find({"idBook": id}):
        return i["url"]


@app.route("/api/book/type/<string:value>", methods=["POST"])  # type
def FillterType(value):
    type = convertType(value)
    list = []
    response = ""
    status = 404
    if isLogin:
        for i in db.book.find({"type": type}):
            url = str(geturl(i["_id"]))
            i["timestamp"] = url
            list.append(i)

            # urllist =[{'url':url}]
            # list.extend(urllist)
            # print(list)
        response = json.dumps(list)
        status = 200
    else:
        response = "Must be login"
        status = 401
    return Response(response=response, status=status, mimetype="application/json")


@app.route("/api/book/country/<string:value>", methods=["POST"])  # country
def FillterCountry(value):
    country = convertCountry(value)
    list = []
    response = ""
    status = 404
    if isLogin:
        for i in db.book.find({"country": country}):
            url = str(geturl(i["_id"]))
            i["timestamp"] = url
            list.append(i)

            # urllist =[{'url':url}]
            # list.extend(urllist)
            print(list)
        response = json.dumps(list)
        status = 200
    else:
        response = "Must be login"
        status = 401
    return Response(response=response, status=status, mimetype="application/json")


def update_username(bookid, username, amount):
    # print(amount)
    res = ""
    list = []
    newid = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    _id = int(datetime.now().microsecond + datetime(1970, 2, 1).microsecond) * 2
    for i in db.book.find({"_id": bookid}):
        list.append(i)
    if len(list) > 0:
        print("con sacsh")

        for item in db.book.find({"_id": bookid}):
            for i in db.Images_book.find({"idBook": bookid}):
                print("them anh")
                newimages = {
                    "_id": str(_id),
                    "idBook": str(newid),
                    "filename": i["filename"],
                    "url": i["url"],
                }
                db.Images_book.insert_one(newimages)
            print(item)
            print("them sach voi " + username)
            newbook = {
                "_id": str(newid),
                "name": item["name"],
                "type": item["type"],
                "detail": item["detail"],
                "country": item["country"],
                "address": item["address"],
                "nxb": item["nxb"],
                "datexb": item["datexb"],
                "sl": amount,
                "username": username,
                "pdf": item["pdf"],
                "timestamp": datetime.now(),
            }
            res = db.book.insert_one(newbook)
    else:
        print("het sach")
        for item in db.outBook.find({"_id": bookid}):
            print("tim thay voi id " + str(bookid))
            for i in db.Images_book.find({"idBook": bookid}):
                newimages = {
                    "_id": str(_id),
                    "idBook": str(newid),
                    "filename": i["filename"],
                    "url": i["url"],
                }
                db.Images_book.insert_one(newimages)
            newbook = {
                "_id": str(newid),
                "name": item["name"],
                "type": item["type"],
                "detail": item["detail"],
                "country": item["country"],
                "nxb": item["nxb"],
                "datexb": item["datexb"],
                "sl": amount,
                "username": username,
                "pdf": item["pdf"],
                "timestamp": datetime.now(),
            }
            res = db.book.insert_one(newbook)
    return res


@app.route("/api/book/get-history/<string:address>", methods=["GET"])
def get_history(address):
    list = []
    for i in db.book_history.find({"address": address}):
        list.append(i)
    return Response(response=json.dumps(list), status=200, mimetype="application/json")


@app.route("/api/book/buy", methods=["POST"])  # buy book
def onBuy():
    response_data = ""
    id = request.form["id"]
    amount = request.form["amount"]
    status_code = 202
    if isLogin:
        username = decode_auth_token(token)
        balance = get_balance(username)
        for i in db.bookSell.find({"_id": int(id)}):
            # print(int(i['price']) < balance*24345)
            tienphaitra1quen = int(i["price"]) / int(i["amount"])
            youpay = tienphaitra1quen * int(amount)
            balanceVND = balance * 24345
            print(int(youpay) < balanceVND)
            if int(youpay) < balanceVND:
                new_balance = round((balanceVND - int(youpay)) / 24345)
                update_wallet(username, new_balance)
                seller_balance = get_balance(i["username"])
                update_wallet(
                    i["username"], (seller_balance + round(int(youpay) / 24245))
                )
                print(i["bookid"])
                update_username(i["bookid"], username, amount)
                add_block(
                    username,
                    "buy",
                    "-" + str(youpay),
                    str(i["bookid"]),
                    str(i["username"]),
                    username,
                    0,
                )
                if int(amount) == int(i["amount"]):
                    db.bookSell.delete_one({"_id": int(id)})
                else:
                    new_amount = int(i["amount"]) - int(amount)
                    db.bookSell.update_one(
                        {"_id": int(id)},
                        {
                            "$set": {
                                "amount": new_amount,
                                "price": (new_amount * tienphaitra1quen),
                            }
                        },
                    )
                add_block(
                    username=username,
                    type="buy",
                    value=amount,
                    bookName=str(getaddress_book(i["bookid"])),
                    role=1,
                    fromusr="",
                    to="",
                )
                add_block(
                    i["username"],
                    "sold",
                    ("+" + str(round(int(youpay) / 23345))),
                    str(i["bookid"]),
                    username,
                    str(i["username"]),
                    0,
                )
                response_data = "OK"
                status_code = 200
            else:
                response_data = "balance not enough to buy"
                status_code = 201

    else:
        response_data = "Must be login"
        status_code = 401
    return Response(
        response=response_data, status=status_code, mimetype="application/json"
    )


def getaddress_book(bookid):
    if db.book.find({"_id": bookid}):
        for i in db.book.find({"_id": bookid}):
            return i["address"]
    else:
        return "Not found"


@app.route("/api/book/get-work/<string:id>", methods=["POST"])
def get_work_book(id):
    list = []
    res = ""
    code = 202
    if isLogin:
        address = getaddress_book(id)
        for i in db.book_history.find({"address": address}):
            list.append(i)
        res = json.dumps(list)
        code = 200
    else:
        res = "Must be login"
        code = 401
    return Response(response=res, status=code, mimetype="application/json")


@app.route("/api/book/sell-book/<string:bookid>", methods=["POST"])
def sell_book(bookid):
    global book_delete
    if isLogin:
        booksellID = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
        amount = request.form["amount"]
        username = decode_auth_token(token)
        price = request.form["price"]
        name, nxb, country, detail = get_info_book_by_id(bookid)
        url = get_url_by_id(bookid)
        timestamp = datetime.now()
        isExisted = False
        address = getaddress_book(bookid)
        print(amount)
        # res = db.book.update_one({'_id':bookid},{'$set':{'sl':slnew}})
        # print(res)
        bookSell = {
            "_id": booksellID,
            "name": name,
            "nxb": nxb,
            "country": country,
            "url": url,
            "detail": detail,
            "amount": amount,
            "price": price,
            "timestamp": timestamp,
            "bookid": bookid,
            "address": address,
            "username": username,
        }
        if not isExisted:
            if check_vaild_book(bookid):
                db.bookSell.insert_one(bookSell)
                update_sl_book(bookid, amount)
                add_block(
                    username=username,
                    type="sell",
                    value=amount,
                    bookName=str(getaddress_book(bookid)),
                    role=1,
                    fromusr="",
                    to="",
                )
                for i in db.book.find({"_id": bookid}):
                    if int(i["sl"]) == 0:
                        db.book.delete_one({"_id": bookid})
                        db.outBook.insert_one(i)
                add_block(
                    username,
                    "sell",
                    amount,
                    (name + " have id: " + bookid),
                    bookid,
                    "Market",
                    0,
                )
                response = " Add book to market successfully"
                status = 200
            else:
                response = " Book has not been added to market successfully"
                status = 400
    else:
        response = "Must be Login first"
        status = 401
    return Response(
        response=response,
        status=status,
        mimetype="application/json",
    )


@app.route("/api/book/get-book-sell", methods=["POST", "GET"])
def getBookSell():
    list = []
    response = ""
    status = 404
    if isLogin:
        for i in db.bookSell.find():
            list.append(i)
        response = json.dumps(list)
        status = 200
    else:
        response = "Must be login"
        status = 401
    return Response(response=response, status=status, mimetype="application/json")


@app.route("/api/book/add-image", methods=["POST"])
def addimages():
    upload_result = None
    id = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    idBook = request.form["id"]
    fileImages = request.files["fileIMG"]
    filename = secure_filename(fileImages.filename)
    if fileImages:
        upload_result = cloudinary.uploader.upload(fileImages)
        print(upload_result)
    images = {
        "_id": id,
        "idBook": idBook,
        "filename": filename,
        "url": upload_result["secure_url"],
    }
    db.Images_book.insert_one(images)
    return Response(
        response=upload_result,
        status=200,
        mimetype="application/json",
    )


def check_vaild_book(bookid):
    if db.book.find_one({"_id": bookid}):
        return True
    else:
        return False


@app.route("/api/book/shipForm/<string:idbook>", methods=["POST"])
def shipForm(idbook):
    id = datetime.now().microsecond + datetime(1970, 1, 1).microsecond
    name = request.form["name"]
    sdt = request.form["sdt"]
    address = request.form["address"]
    amount = request.form["amount"]
    timecreated = datetime.now()
    shipForm = {
        "_id": id,
        "bookid": idbook,
        "name": name,
        "address": address,
        "sdt": sdt,
        "amount": amount,
        "timecreated": timecreated,
    }
    add_block(
        decode_auth_token(token), "ship", amount, getaddress_book(idbook), "", "", 1
    )
    currentamount = 0
    current = 0
    for i in db.wallet.find({"username": decode_auth_token(token)}):
        currentamount = i["balance"]
    update_wallet(decode_auth_token(token), int(currentamount) - 5)
    add_block(
        decode_auth_token(token), "ship", "-5", getaddress_book(idbook), "", "", 0
    )
    for i in db.book.find({"_id": idbook}):
        current = i["sl"]
    if current >= amount:
        db.book.update_one(
            {"_id": idbook}, {"$set": {"sl": int(current) - int(amount)}}
        )
    else:
        return "not enough amount"
    db.shipForm.insert_one(shipForm)
    return Response(response="Add Sucessfully", status=200, mimetype="application/json")


@app.route("/api/book/profile/<string:id>", methods=["GET"])
def getInfobook(id):
    book = Book()
    if db.book.find({"_id": id}):
        for i in db.book.find({"_id": id}):
            book.id = id
            book.name = i["name"]
            book.type = i["type"]
            book.detail = i["detail"]
            book.country = i["country"]
            book.nxb = i["nxb"]
            book.datexb = i["datexb"]
            book.sl = i["sl"]
            book.timestamp = i["timestamp"]
            book.username = i["username"]
            book.pdf = i["pdf"]
        imageURL = getImageFromID(id)
        response = json.dumps({"data": book.visible(), "url": imageURL})
        status = 200
    else:
        response = " Not Found"
        status = 400
    return Response(response=response, status=status, mimetype="application/json")


def getImageFromID(bookid):
    for i in db.Images_book.find({"idBook": bookid}):
        return i["url"]


@app.route("/api/book/get-id/<string:username>", methods=["GET"])
def getListIDBook(username):
    listbook = []
    response = ""
    if isLogin:
        if db.book.find({"username": username}):
            for i in db.book.find({"username": username}):
                listbook.append(i)
            response = json.dumps(listbook)

        else:
            response = "Not Found"
        return Response(response=response, status=200, mimetype="application/json")

    else:
        return Response(
            response="must be login", status=401, mimetype="application/json"
        )


@app.route("/api/book/gettotal", methods=["POST"])
def gettota_book():
    count = 0
    if isLogin:
        for i in db.book.find():
            count += 1
    return Response(response=str(count), status=200, mimetype="application/json")


@app.route("/api/search/<string:value>", methods=["GET"])
def onSearch(value):
    listaccount = []
    listbook = []
    response_data = ""
    status_code = 404
    if isLogin:
        for i in db.account.find({"username": {"$regex": value}}):
            i["timecreated"] = getaddressbyusername(i["username"])
            listaccount.append(i)
        for i in db.book.find({"name": {"$regex": value}}):
            listbook.append(i)
        for i in db.book.find({"country": {"$regex": value}}):
            listbook.append(i)
        for i in db.book.find({"type": {"$regex": value}}):

            listbook.append(i)
        if len(listbook):
            response_data = json.dumps({"book": listbook, "account": listaccount})
            status_code = 200
        if len(listaccount):
            response_data = json.dumps({"account": listaccount, "book": listbook})
            status_code = 200
    else:
        response_data = "must be login"
        status_code = 401
    return Response(
        response=response_data, status=status_code, mimetype="application/json"
    )


# ---------------------------------------------------token------------------------------------------------------
def generate_token(username):
    SECRET_KEY = (
        """\xf9'\xe4p(\xa9\x12\x1a!\x94\x8d\x1c\x99l\xc7\xb7e\xc7c\x86\x02MJ\xa0"""
    )
    try:
        payload = {
            "exp": datetime.now() + timedelta(days=0, seconds=5),
            "iat": datetime.now(),
            "sub": username,
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    SECRET_KEY = (
        """\xf9'\xe4p(\xa9\x12\x1a!\x94\x8d\x1c\x99l\xc7\xb7e\xc7c\x86\x02MJ\xa0"""
    )
    try:
        payload = jwt.decode(auth_token, options={"verify_signature": False})
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return "Signature expired. Please log in again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please log in again."


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["DEBUG"] = True
    app.testing = True
    app.run(host="0.0.0.0", port=8000, debug=True)
