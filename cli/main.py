import os
import sys
import click
from api_client import APIClient

user_logged_in = False
transaction_service_url = None
user_info_service_url = None
apiClient = None


@click.group()
def cli():
    """Cafe CLI Tool"""
    pass


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def connection_config():
    """Configure URLs for backends"""
    global transaction_service_url, user_info_service_url, apiClient

    service_connection_tested = False
    first_try = True
    while not service_connection_tested:
        clear_screen()
        if first_try:
            click.echo("Welcome to Cafe CLI Tool!")
            first_try = False
        else:
            click.echo("Something went wrong when trying to connect to your services, please try again!")

        transaction_service_url = click.prompt("Please enter your transaction service URL", type=str)
        user_info_service_url = click.prompt("Please enter your user info service URL", type=str)

        apiClient = APIClient(transaction_service_url, user_info_service_url)
        service_connection_tested = apiClient.are_services_healthy()


@click.command()
def main_menu():
    """Display the main meun."""
    global user_logged_in
    while not user_logged_in:
        clear_screen()
        click.echo("Main Menu:")
        click.echo("1: Register a new user")
        click.echo("2: User login")
        click.echo("3: Exit")

        choice = click.prompt("Please enter your choice", type=int)

        if choice == 1:
            register()
        elif choice == 2:
            login()
        elif choice == 3:
            click.echo("Exiting the program.")
            sys.exit(0)
        else:
            click.echo("Invalid choice, Please try again.")


def register():
    """Register a new user."""
    clear_screen()
    click.echo("Register Page:")
    username = click.prompt('Please enter a username')
    password = click.prompt('Please enter a password', hide_input=True)
    response = apiClient.signup(username, password)
    if response.status_code == 201:
        click.echo("User successfully registered.")
    elif response.status_code == 400:
        error_msg = response.json().get('msg', 'Registration failed due to an unknown error.')
        click.echo(f"Registration failed. Reason: {error_msg}")
    else:
        click.echo("Registration failed with an unexpected error.")


def login():
    """Log in as an existing user."""
    clear_screen()
    click.echo("Login Page:")

    while True:
        username = click.prompt('Please enter your username')
        password = click.prompt('Please enter your password', hide_input=True)
        response = apiClient.login(username, password)

        if response.status_code == 200:
            global user_logged_in
            user_logged_in = True
            click.echo("Login successful.")
            user_menu()
            break
        else:
            click.echo("Login failed. Reason: " + response.json().get('msg', 'Bad username or password.'))
            retry = click.prompt('Do you want to try again? (y/n)', default='y')
            if retry.lower() != 'y':
                break


def user_menu():
    """Show the user menu after login."""
    global user_logged_in
    while user_logged_in:
        clear_screen()
        click.echo("User Menu:")
        click.echo("1: View points and membership information")
        click.echo("2: Create a group")
        click.echo("3: Join a group")
        click.echo("4: View group information")
        click.echo("5: Add item")
        click.echo("6: View item list")
        click.echo("7: Create a transaction")
        click.echo("8: Logout")

        choice = click.prompt("Please enter your choice", type=int)

        if choice == 1:
            view_points_and_memberships()
        elif choice == 2:
            create_group()
        elif choice == 3:
            add_user_to_group()
        elif choice == 4:
            view_group_info()
        elif choice == 5:
            add_item()
        elif choice == 6:
            view_item_list()
        elif choice == 7:
            create_transaction()
        elif choice == 8:
            logout()
            user_logged_in = False
        else:
            click.echo("Invalid choice, please try again.")


def view_points_and_memberships():
    clear_screen()
    click.echo("Viewing points and membership information...")
    response = apiClient.get_user_memberships()
    if response.status_code == 200:
        memberships = response.json()
        click.echo("Your group single region memberships: ")
        for group in memberships["single_region"]:
            click.echo(f"Group ID: {group['group_id']}, Name: {group['name']}, Owner ID: {group['owner_id']}")
        click.echo("Your group multi region memberships: ")
        for group in memberships["multi_region"]:
            click.echo(f"Group ID: {group['group_id']}, Name: {group['name']}, Owner ID: {group['owner_id']}")
    elif response.status_code == 401:
        error_msg = response.json().get('msg', 'Unauthorized access. Please log in again.')
        click.echo(error_msg)
    else:
        error_msg = response.json().get('msg', 'An error occurred. Please try again later.')
        click.echo(error_msg)

    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def create_group():
    while True:
        clear_screen()
        click.echo("Create a new group:")
        group_name = click.prompt("Please enter the group name: ")
        response = apiClient.create_group(group_name)

        if response.status_code == 201:
            click.echo("Group successfully created.")
            group_info = response.json()
            click.echo(f"Group ID: {group_info.get('group_id')}, Name: {group_name}")
            break
        else:
            error_msg = response.json().get('msg', 'Failed to create group.')
            click.echo(error_msg)
            retry = click.prompt("Do you want to try again? (y/n)", default='n')
            if retry.lower() != 'y':
                break
    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def add_user_to_group():
    """Allow the current user to add another user to the group"""
    clear_screen()
    click.echo("Add user to existing group:")
    group_id = click.prompt("Enter the group ID", type=int)
    user_name = click.prompt("Enter the username of the user you want to add to the group")

    response = apiClient.add_member_to_group(group_id=group_id, user_name=user_name)

    if response.status_code == 201:
        click.echo("User successfully added to the group.")
    elif response.status_code == 404:
        click.echo("User or group not found.")
    elif response.status_code == 500:
        click.echo("Failed to add the user to the group. The group may be full, or the user is already a member.")
    else:
        error_msg = response.json().get('msg', 'An error occurred.')
        click.echo(error_msg)

    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def view_group_info():
    clear_screen()
    group_id = click.prompt("Please enter the group ID", type=int)
    response = apiClient.get_group_details(group_id)

    if response.status_code == 200:
        group_details = response.json()
        click.echo(f"Group ID: {group_details['group_id']}")
        click.echo(f"Name: {group_details['name']}")
        click.echo(f"Owner ID: {group_details['owner_id']}")
        click.echo(f"Points: {group_details['points']}")
        click.echo("Members:")
        for member_id in group_details['members']:
            click.echo(f"- User ID: {member_id}")
    else:
        error_msg = response.json().get('msg', 'Failed to retrieve group details.')
        click.echo(error_msg)

    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def create_transaction():
    """Create a new transaction"""
    clear_screen()
    click.echo("Creating a new transaction...")
    group_id = click.prompt("Please enter your group ID", type=int)
    store = click.prompt("Enter the store name")
    # points_redeemed = click.prompt("Enter points to redeem (enter 0 if not using points)", type=int)

    click.echo("Available items:")
    available_items = fetch_and_display_items()
    if not available_items:
        click.echo("No available items to purchase.")
        return

    selected_items = []
    while True:
        item_id = click.prompt("Enter item ID (or press 'q' to finish)", default='q')
        if item_id == 'q':
            break
        item_id = int(item_id)
        quantity = click.prompt(f"Enter quantity for item {item_id}", type=int)

        item = next((item for item in available_items if item['item_id'] == item_id), None)
        if item is None:
            click.echo("Item not found, please try again.")
            continue

        selected_items.append({"item_id": item_id, "quantity": quantity, "price": item['price']})

    total_price = sum(item['price'] * item['quantity'] for item in selected_items)
    click.echo(f"Total price before points redemption: {total_price}")

    response = apiClient.get_group_details(group_id)
    if response.status_code == 200:
        group_details = response.json()
        group_points = group_details['points']
        click.echo(f"Your group has {group_points} points available.")
    else:
        click.echo("Failed to fetch group details. Please try again later.")
        return

    while True:
        points_redeemed = click.prompt("Enter points to redeem (enter 0 if not using points)", type=int, default=0)
        if points_redeemed <= group_points:
            break
        click.echo("Cannot redeem more points than the group has. Please try again.")

    response = apiClient.create_transaction(group_id, store, points_redeemed, selected_items)

    if response.status_code == 201:
        click.echo("Transaction created successfully!")
        transaction_details = response.json()
        click.echo(f"Transaction ID: {transaction_details.get('transaction').get('transaction_id')}")
        click.echo("Items:")
        for item in transaction_details.get('transaction_items', []):
            click.echo(
                f"- Item ID: {item.get('item_id')}, "
                f"Quantity: {item.get('quantity')}, "
                f"Item Total: {item.get('item_total')}"
            )
    else:
        error_message = response.json().get('msg', 'An error occurred while creating the transaction.')
        click.echo(f"Error: {error_message}")

    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def fetch_and_display_items():
    response = apiClient.get_items()

    if response.status_code == 200:
        items = response.json()
        if items:
            for item in items:
                click.echo(f"Item ID: {item['item_id']}, Name: {item['name']}, Price: {item['price']}")
            return items
        else:
            click.echo("No items available.")
    else:
        error_message = response.json().get('msg', 'An error occurred while fetching the item list.')
        click.echo(f"Error: {error_message}")
    return None


def view_item_list():
    clear_screen()
    click.echo("Fetching the item list...")
    fetch_and_display_items()

    click.echo("\nPress any key to return to the user menu...")
    input()
    user_menu()


def add_item():
    while True:
        clear_screen()
        click.echo("Adding a new item to the inventory...")
        name = click.prompt("Please enter the item name ('q' to quit)")
        if name.lower() == 'q':
            return

        price = click.prompt("Please enter the item price", type=float)

        click.echo(f"Name: {name}, Price: {price}")
        confirm = click.confirm("Are you sure you want to add this item?")
        if confirm:
            response = apiClient.add_item(name, price)

            if response.status_code == 201:
                click.echo("Item added successfully!")
                item_details = response.json()
                click.echo(f"Item ID: {item_details.get('item_id')}")
            else:
                error_message = response.json().get('msg', 'An error occurred while adding the item.')
                click.echo(f"Error: {error_message}")

            continue_adding = click.confirm("Do you want to add another item?")
            if not continue_adding:
                return
        else:
            click.echo("Item addition canceled.")
            continue_adding = click.confirm("Do you want to add another item?")
            if not continue_adding:
                return


def logout():
    """Logout the current user."""
    global user_logged_in
    apiClient.set_access_token(None)
    user_logged_in = False
    click.echo("You have been logged out.")


if __name__ == '__main__':
    connection_config()
    main_menu()
