import hashlib
password = 'admin create index block'
# p = password.lower()
# print(p)
print(hashlib.sha256(password.encode('utf8')).hexdigest())
# print(type(int("1")))