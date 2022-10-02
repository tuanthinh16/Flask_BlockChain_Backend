


class Account:
    def __init__(self,fullName='',username='',password='',email='',address='',phone='',timeCreated=''):
        self.fullName = fullName
        self.email = email
        self.username = username
        self.password = password
        self.address = address
        self.phone = phone
        self.timeCreated = timeCreated
    def visible(self):
        return{
            'FullName': self.fullName,
            'Email': self.email,
            'Username': self.username,
            'Password': self.password,
            'Address': self.address,
            'Phone': self.phone,
            'TimeCreated': self.timeCreated,
        }
class AccountDTO:
    def __init__(self,FullName,email,address,phone,timeCreated):
        self.FullName = FullName
        self.email = email
        self.address = address
        self.phone = phone
        self.timeCreated = timeCreated
    def visible(self):
        return{
            'FullName': self.fullName,
            'Email': self.email,
            'Username': self.username,
            'Address': self.address,
            'Phone': self.phone,
            'TimeCreated': self.timeCreated,
        }