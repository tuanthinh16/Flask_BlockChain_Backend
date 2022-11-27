import hashlib

from app import getaddress_book
password = 'admin create index block'
# p = password.lower()
# print(p)
print(hashlib.sha256(password.encode('utf8')).hexdigest())
# print(type(int("1")))
print(round((222370)/233))


getaddress_book('1669533542')