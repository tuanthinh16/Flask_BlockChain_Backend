class Book:
    def __init__(self,id='',name='',type='',country='',nxb='',datexb='',sl=0,username='',timestamp=''):
        self.id = id
        self.name = name
        self.type = type
        self.country = country
        self.nxb = nxb
        self.datexb = datexb
        self.sl = sl
        self.username = username
        self.timestamp = timestamp
    def visible(self):
        return{
            'BookId': self.id,
            'Name': self.name,
            'Type': self.type,
            'Country': self.country,
            'Nhaxuatban': self.nxb,
            'Ngayxuatban': self.datexb,
            'Soluong': self.sl,
            'Username': self.username,
            'Thoigian': self.timestamp,
        }