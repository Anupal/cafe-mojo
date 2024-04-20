"""
This script is designed to simulate a set of operations involving user registration, group management, and transaction processing to test the functionality and robustness of an API handling concurrent requests.

Instructions for running this script:
1. Make sure the API server (e.g., Flask application) that you intend to test is up and running at the specified BASE_URL.
2. The script should be located under a specific directory structured for testing within your project. It's recommended to place this script in a directory such as 'project_directory/scripts' for organization.
3. To execute the script, navigate to the directory where the script is located and run it from the command line:
   python script_double_spending_test.py


Script Workflow:
- Registers two test users.
- Logs in both users to retrieve JWT tokens.
- Creates a group and adds both users to it.
- Simulates adding initial points to the group.
- Conducts concurrent transactions using threading to simulate real-world usage and test the system's handling of concurrency.
- Checks and prints the final state of the group's points to verify the outcomes of the transactions.

Location and Structure:
- Ensure this script is located in a dedicated test directory within your project structure, such as 'project_directory/tests'.
- This structure helps maintain clarity and organization, especially in larger projects where multiple types of tests might be needed.

Purpose:
- This script is used primarily for testing and verifying the correct functionality of user registration, group creation, transaction handling, and concurrency management within the API. It aims to ensure that the system performs as expected under simulated real-world conditions.
"""


import threading
import requests

API_BASE_URL = "http://localhost:5000"  # 根据实际情况调整


def register_user(username, password):
    url = f"{API_BASE_URL}/user/signup"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    return response.json(), response.status_code


def login_user(username, password):
    url = f"{API_BASE_URL}/user/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None


def create_group(jwt, group_name):
    url = f"{API_BASE_URL}/group/add"
    headers = {'Authorization': f'Bearer {jwt}'}
    data = {"name": group_name}
    response = requests.post(url, headers=headers, json=data)
    return response.json(), response.status_code


def add_group_member(jwt, group_id, user_name):
    url = f"{API_BASE_URL}/group/add-member"
    headers = {'Authorization': f'Bearer {jwt}'}
    data = {"group_id": group_id, "user_name": user_name}
    response = requests.post(url, headers=headers, json=data)
    return response.json(), response.status_code


def make_transaction(jwt, group_id, store, item):
    url = f"{API_BASE_URL}/transaction/add"
    headers = {'Authorization': f'Bearer {jwt}'}
    data = {
        "group_id": group_id,
        "store": store,
        "points_redeemed": 2,
        "items": item
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json(), response.status_code


def add_initial_points(jwt, group_id, initial_points):
    url = f"{API_BASE_URL}/group/add_points"  # 确保这是正确的API端点
    headers = {'Authorization': f'Bearer {jwt}'}
    data = {"group_id": group_id, "points_to_add": initial_points}
    response = requests.post(url, headers=headers, json=data)
    return response.json(), response.status_code


def simulate_transaction(jwt1, jwt2, group_id):
    items_user1 = [{"item_id": 1, "quantity": 2}, {"item_id": 2, "quantity": 1}]
    items_user2 = [{"item_id": 3, "quantity": 1}, {"item_id": 4, "quantity": 3}]

    thread1 = threading.Thread(target=make_transaction, args=(jwt1, group_id, "Dublin 6", items_user1))
    thread2 = threading.Thread(target=make_transaction, args=(jwt2, group_id, "Dublin 6", items_user2))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()


def check_group_points(jwt, group_id):
    url = f"{API_BASE_URL}/group/{group_id}"
    headers = {'Authorization': f'Bearer {jwt}'}
    response = requests.get(url, headers=headers)
    return response.json(), response.status_code


def main():
    user1 = {"username": "testuser1", "password": "password1"}
    user2 = {"username": "testuser2", "password": "password2"}
    group_name = "TestGroup"

    print("Registering users...")
    register_user(user1['username'], user1['password'])
    register_user(user2['username'], user2['password'])

    print("Logging in users...")
    jwt1 = login_user(user1['username'], user1['password'])
    jwt2 = login_user(user2['username'], user2['password'])

    print("Creating group...")
    group_info, status = create_group(jwt1, group_name)
    group_id = group_info['group_id']
    if status == 201:
        print("Adding second user to group...")
        add_group_member(jwt1, group_id, user2['username'])

        print("Adding 10 points to group...")
        add_initial_points(jwt1, group_id, 10)

    simulate_transaction(jwt1, jwt2, group_id)
    result, status = check_group_points(jwt1, group_id)
    print(f"Group Points Status: {status}, Data: {result}")


if __name__ == '__main__':
    main()