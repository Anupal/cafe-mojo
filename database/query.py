import math
from database.models import User, Group, Transaction, Item, TransactionItem, db_connection


def add_user(user_name, password):
    session = db_connection.get_session()
    existing_user = session.query(User).filter_by(user_name=user_name).first()
    if existing_user:
        print("Username already exists!")
        return None
    new_user = User(user_name=user_name, password=password)
    session.add(new_user)
    session.commit()
    print(f"User {user_name} added with ID {new_user.user_id}.")
    return new_user


def add_group(owner_id, name):
    session = db_connection.get_session()
    # First, create the new group without members
    new_group = Group(name=name, owner_id=owner_id)

    # Before adding the new group to the session, find the owner by ID
    owner = session.query(User).filter_by(user_id=owner_id).first()
    if not owner:
        print("Owner not found.")
        return None

    # Add the owner to the group's members
    new_group.members.append(owner)

    # Add the new group to the session and commit
    session.add(new_group)
    session.commit()

    print(f"Group {name} added with ID {new_group.group_id}, owner ID {owner_id} added as a member.")
    return new_group


def authenticate_user(user_name, password):
    session = db_connection.get_session()
    user = session.query(User).filter_by(user_name=user_name, password=password).first()
    if user:
        print("Authentication successful!")
        return user
    else:
        print("Invalid username or password!")
        return None


def add_item(name, price):
    session = db_connection.get_session()
    new_item = Item(name=name, price=price)
    session.add(new_item)
    session.commit()
    print(f"Item {name} added with ID {new_item.item_id}.")
    return new_item


def add_transaction(user_id, group_id, store, points_redeemed, items):
    session = db_connection.get_session()
    # Start a transaction to ensure atomicity
    try:
        total = 0
        for item_data in items:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            item = get_item(item_id)
            if not item:
                raise Exception("Item not found")

            total += item.price * quantity

        # Add the transaction
        transaction = add_transaction_entry(user_id, group_id, store, total, points_redeemed)
        if not transaction:
            raise Exception("Failed to add transaction")

        # Iterate over each item in the transaction and add it
        transaction_items = []
        for item_data in items:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            item = get_item(item_id)

            if not item:
                raise Exception("Item not found")
            item_total = item.price * quantity
            transaction_items.append(
                add_transaction_item(transaction.transaction_id, item_id, quantity, item_total).to_dict()
            )
        session.commit()
        return transaction.to_dict(), transaction_items

    except Exception as e:
        print(f"Failed to add transaction due to {e}")
        session.rollback()
        return None, None


def add_transaction_item(transaction_id, item_id, quantity, item_total):
    session = db_connection.get_session()
    new_transaction_item = TransactionItem(transaction_id=transaction_id, item_id=item_id, quantity=quantity, item_total=item_total)
    session.add(new_transaction_item)
    print(f"Transaction item added to transaction {transaction_id} with item ID {item_id}.")
    return new_transaction_item


def add_transaction_entry(user_id, group_id, store, total, points_redeemed):
    session = db_connection.get_session()
    # Check if the group has enough points
    group = session.query(Group).filter_by(group_id=group_id).one()
    if group.points < points_redeemed:
        print("Not enough points in the group to redeem.")
        return None

    # Deduct points from group
    group.points -= points_redeemed

    # Calculate the total after redeeming points
    # Assuming each point is worth 1 unit of currency
    effective_total = total - points_redeemed

    # Calculate points awarded (assuming 1 point awarded for every 10 units of currency spent, and no points
    # awarded if points are redeemed)
    if points_redeemed == 0:
        points_awarded = math.ceil(effective_total / 10)
        group.points += points_awarded
    else:
        points_awarded = 0

    # Create and add the transaction
    new_transaction = Transaction(
        user_id=user_id,
        group_id=group_id,
        store=store,
        total=effective_total,
        points_redeemed=points_redeemed,
        points_awarded=points_awarded
    )
    session.add(new_transaction)

    print(f"Transaction added for user {user_id} in group {group_id}. Points redeemed: {points_redeemed}. New group points: {group.points}")
        
    return new_transaction


def get_user_details(user_id):
    session = db_connection.get_session(read_only=True)
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        print("User not found!")
        return None
    return user


def get_user_details_by_username(user_name):
    session = db_connection.get_session(read_only=True)
    user = session.query(User).filter_by(user_name=user_name).first()
    if not user:
        print("User not found!")
        return None
    return user


def get_group_details(group_id):
    session = db_connection.get_session(read_only=True)
    group = session.query(Group).filter_by(group_id=group_id).first()
    if not group:
        print("Group not found!")
        return None
    # Load members lazily
    members = [member.user_id for member in group.members]
    group_details = {
        "group_id": group.group_id,
        "name": group.name,
        "owner_id": group.owner_id,
        "points": group.points,
        "members": members
    }
    return group_details


def add_member_to_group(user_id, group_id):
    session = db_connection.get_session()
    group = session.query(Group).filter_by(group_id=group_id).first()
    if not group:
        print("Group not found!")
        return False
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        print("User not found!")
        return False
    if user in group.members:
        print("User already in group!")
        return False
    if len(group.members) >= 4:  # Assuming a maximum of 4 members per group
        print("Group is full!")
        return False
    group.members.append(user)
    session.commit()
    print(f"User {user_id} added to group {group_id}.")
    return True


def get_item(item_id):
    session = db_connection.get_session(read_only=True)
    return session.query(Item).filter_by(item_id=item_id).first()


def get_items():
    session = db_connection.get_session(read_only=True)
    items = session.query(Item).all()
    return items


def get_user_transactions(user_id):
    session = db_connection.get_session(read_only=True)
    transactions = session.query(Transaction).filter_by(user_id=user_id).all()
    return transactions


def get_group_transactions(group_id):
    session = db_connection.get_session(read_only=True)
    transactions = session.query(Transaction).filter_by(group_id=group_id).all()
    return transactions
