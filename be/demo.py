import hashlib
password = 'Học Cho Ai Học Để Làm Gì'
p = password.lower()
print(p)
print(hashlib.md5(p.encode('utf8')).hexdigest())
print(type(int("1")))