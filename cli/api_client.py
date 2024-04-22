import requests


class APIClient:
    def __init__(self, transaction_service_url="http://127.0.0.1:5000", user_info_service_url="http://127.0.0.1:5000"):
        self.transaction_service_url = transaction_service_url
        self.user_info_service_url = user_info_service_url

    access_token = None

    def set_access_token(self, token):
        self.access_token = token

    def signup(self, username, password):
        response = requests.post(f"{self.user_info_service_url}/user/signup",
                                 json={"username": username, "password": password})
        return response

    def login(self, username, password):
        response = requests.post(f"{self.user_info_service_url}/user/login",
                                 json={"username": username, "password": password})
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
        return response

    def get_authenticated_header(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def get_user_memberships(self):
        """Get the community information of the currently logged-in user"""
        headers = self.get_authenticated_header()
        response = requests.get(f"{self.user_info_service_url}/user/memberships", headers=headers)
        return response

    def create_group(self, group_name):
        """Create a new group"""
        headers = self.get_authenticated_header()
        data = {"name": group_name}
        response = requests.post(f"{self.user_info_service_url}/group/add", headers=headers, json=data)
        return response

    def add_member_to_group(self, group_id, user_name):
        """Add user to group"""
        headers = self.get_authenticated_header()
        data = {"group_id": group_id, "user_name": user_name}
        response = requests.post(f"{self.user_info_service_url}/group/add-member", headers=headers, json=data)
        return response

    def get_group_details(self, group_id):
        """Get the details of the specified group."""
        headers = self.get_authenticated_header()
        response = requests.get(f"{self.user_info_service_url}/group/{group_id}", headers=headers)
        return response

    def get_items(self):
        """Get a list of all items"""
        headers = self.get_authenticated_header()
        response = requests.get(f"{self.transaction_service_url}/item/all", headers=headers)
        return response

    def add_item(self, name, price):
        """Adds a new item to the inventory"""
        headers = self.get_authenticated_header()
        data = {
            "name": name,
            "price": price
        }
        response = requests.post(f"{self.transaction_service_url}/item/add", headers=headers, json=data)
        return response

    def create_transaction(self, group_id, store, points_redeemed, items):
        headers = self.get_authenticated_header()
        data = {
            "group_id": group_id,
            "store": store,
            "points_redeemed": points_redeemed,
            "items": items
        }
        response = requests.post(f"{self.transaction_service_url}/transaction/add", headers=headers, json=data)
        return response

    def are_services_healthy(self):
        try:
            response_transaction_service = requests.get(f"{self.transaction_service_url}/healthcheck")
            response_user_info_service = requests.get(f"{self.user_info_service_url}/healthcheck")
        except requests.exceptions.ConnectionError:
            return False
        return response_transaction_service.status_code == 200 and response_user_info_service.status_code == 200
