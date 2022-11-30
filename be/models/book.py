class Book:
    def __init__(
        self,
        id="",
        name="",
        type="",
        detail="",
        country="",
        nxb="",
        datexb="",
        sl=0,
        username="",
        timestamp="",
        pdf="",
    ):
        self.id = id
        self.name = name
        self.type = type
        self.detail = detail
        self.country = country
        self.nxb = nxb
        self.datexb = datexb
        self.sl = sl
        self.username = username
        self.timestamp = timestamp
        self.pdf = pdf

    def visible(self):
        return {
            "BookId": self.id,
            "Name": self.name,
            "Type": self.type,
            "Details": self.detail,
            "Country": self.country,
            "Nhaxuatban": self.nxb,
            "Ngayxuatban": self.datexb,
            "Soluong": self.sl,
            "Username": self.username,
            "Thoigian": self.timestamp,
            "pdf": self.pdf,
        }
