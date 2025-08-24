class User:
    def __init__(self, first_name, last_name, email, mobile, password,
                 email_verified=False, mobile_verified=False):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.mobile = mobile
        self.password = password  # Stored as hashed password.
        self.email_verified = email_verified
        self.mobile_verified = mobile_verified

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "mobile": self.mobile,
            "password": self.password,
            "email_verified": self.email_verified,
            "mobile_verified": self.mobile_verified
        }
