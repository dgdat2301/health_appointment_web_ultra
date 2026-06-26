from csv_service import read_csv, append_csv

USER_FIELDS = ["user_id", "username", "password", "role", "email", "full_name", "phone", "address"]


class AuthService:
    def __init__(self, users_file):
        self.users_file = users_file

    def get_all_users(self):
        return read_csv(self.users_file)

    def get_next_user_id(self):
        users = self.get_all_users()
        ids = [int(u["user_id"]) for u in users if u.get("user_id", "").isdigit()]
        return max(ids) + 1 if ids else 1

    def find_by_username(self, username):
        username = username.lower().strip()

        for user in self.get_all_users():
            if user["username"].lower().strip() == username:
                return user

        return None

    def find_by_email(self, email):
        email = email.lower().strip()

        for user in self.get_all_users():
            if user["email"].lower().strip() == email:
                return user

        return None

    def login(self, username, password):
        user = self.find_by_username(username)

        if not user:
            return None

        if user["password"] != password:
            return None

        return user

    def register_patient(self, username, password, email, full_name, phone, address):
        if self.find_by_username(username):
            return False, "Tên đăng nhập đã tồn tại."

        if self.find_by_email(email):
            return False, "Email đã được sử dụng."

        new_user = {
            "user_id": self.get_next_user_id(),
            "username": username,
            "password": password,
            "role": "User",
            "email": email,
            "full_name": full_name,
            "phone": phone,
            "address": address
        }

        append_csv(self.users_file, USER_FIELDS, new_user)
        return True, "Đăng ký tài khoản thành công."
