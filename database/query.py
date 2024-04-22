import logging
import math
import utils
from database.models import User, Group, Transaction, Item, TransactionItem, GroupMemberMR, DB_CONNECTION, \
    HOME_DB_CONNECTION

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def add_user(user_name, password):
    home_db_session = HOME_DB_CONNECTION.get_session()

    existing_user = home_db_session.query(User).filter_by(user_name=user_name).first()
    if existing_user:
        log.error("Username already exists!")
        return None
    new_user = User(user_name=user_name, password=password)
    home_db_session.add(new_user)
    home_db_session.commit()
    log.info(f"User {user_name} added with ID {new_user.user_id}.")
    return new_user


def add_group(owner_id, name, region, multi_region):
    db_session = DB_CONNECTION[region].get_session()

    # First, create the new group without members
    new_group = Group(name=name, owner_id=owner_id, multi_region=multi_region)

    # Before adding the new group to the session, find the owner by ID
    owner = db_session.query(User).filter_by(user_id=owner_id).first()
    if not owner:
        log.error("Owner not found.")
        return None

    if multi_region:
        db_session.add(new_group)
        db_session.commit()

        for region_i in DB_CONNECTION:
            db_session_r = DB_CONNECTION[region_i].get_session()
            mr_mapping = GroupMemberMR(
                group_id=new_group.group_id,
                user_id=owner.user_id,
                group_region_id=utils.REGIONS_INT[region],
                user_region_id=utils.REGIONS_INT[region]
            )
            db_session_r.add(mr_mapping)
            db_session_r.commit()
    else:
        # Add the owner to the group's members
        new_group.members.append(owner)
        # Add the new group to the session and commit
        db_session.add(new_group)
        db_session.commit()

    log.info(f"Group {name} added with ID {new_group.group_id}, owner ID {owner_id} added as a member.")
    return new_group


def authenticate_user(user_name, password, region):
    db_session = DB_CONNECTION[region].get_session()

    user = db_session.query(User).filter_by(user_name=user_name, password=password).first()
    if user:
        log.info("Authentication successful!")
        return user
    else:
        log.error("Invalid username or password!")
        return None


def add_item(name, price):
    home_db_session = HOME_DB_CONNECTION.get_session()

    new_item = Item(name=name, price=price)
    home_db_session.add(new_item)
    home_db_session.commit()
    log.info(f"Item {name} added with ID {new_item.item_id}.")
    return new_item


def add_transaction(user_id, group_id, store, points_redeemed, items):
    try:
        home_db_session = HOME_DB_CONNECTION.get_session()

        # check if both are part of multi region group
        mr_mapping = home_db_session.query(GroupMemberMR).filter_by(group_id=group_id, user_id=user_id).first()
        if mr_mapping:
            user_region = utils.REGIONS_INT_REV[mr_mapping.user_region_id]
            group_region = utils.REGIONS_INT_REV[mr_mapping.group_region_id]
        else:
            user_region = group_region = utils.REGION_ID

        total = 0
        for item_data in items:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            item = home_db_session.query(Item).filter_by(item_id=item_id).first()
            if not item:
                raise Exception("Item not found")

            total += item.price * quantity
        home_db_session.close()

        # redeem points
        points = modify_group_points(group_region, group_id, total, points_redeemed)
        if not points:
            raise Exception("Failed to modify group points.")
        points_awarded, points_redeemed = points

        # Add the transaction
        transaction_details = add_transaction_entry(user_region, user_id, group_id, store, total, points_awarded,
                                                    points_redeemed, items)
        if not transaction_details:
            raise Exception("Failed to add transaction")

        return transaction_details
    except Exception as e:
        log.error(f"Failed to add transaction due to {e}")
        return None, None


def modify_group_points(region, group_id, total, points_redeemed):
    db_session = DB_CONNECTION[region].get_session()
    try:
        group = db_session.query(Group).filter_by(group_id=group_id).with_for_update().one()

        # Check if the group has enough points
        if group.points < points_redeemed:
            log.error("Not enough points in the group to redeem.")
            return None

        group.points -= points_redeemed
        if points_redeemed == 0:
            points_awarded = math.ceil(total / 10)
            group.points += points_awarded
        else:
            points_awarded = 0
        db_session.commit()
        log.info(f"New group points: {group.points}")
        return points_awarded, points_redeemed
    except Exception as e:
        log.error(f"Failed to modify group points due to {e}")
        db_session.rollback()
    finally:
        db_session.close()


def add_transaction_entry(region, user_id, group_id, store, total, points_awarded, points_redeemed, items):
    db_session = DB_CONNECTION[region].get_session()
    try:
        effective_total = total - points_redeemed

        # Create and add the transaction
        new_transaction = Transaction(
            user_id=user_id,
            group_id=group_id,
            store=store,
            total=effective_total,
            points_redeemed=points_redeemed,
            points_awarded=points_awarded
        )
        db_session.add(new_transaction)

        # Iterate over each item in the transaction and add it
        transaction_items = []
        for item_data in items:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            item = db_session.query(Item).filter_by(item_id=item_id).first()
            if not item:
                raise Exception("Item not found")

            item_total = item.price * quantity
            transaction_item = TransactionItem(transaction_id=new_transaction.transaction_id, item_id=item_id,
                                               quantity=quantity,
                                               item_total=item_total)
            transaction_items.append(transaction_item.to_dict())
            db_session.add(transaction_item)
        db_session.commit()
        log.info(
            f"Transaction added for user {user_id} in group {group_id}. Points redeemed: {points_redeemed}.")
        return new_transaction.to_dict(), transaction_items
    except Exception as e:
        log.error(f"Failed to add transaction due to {e}")
        db_session.rollback()
    finally:
        db_session.close()

def get_user_details(user_id, region=utils.REGION_ID):
    db_session = DB_CONNECTION[region].get_session()

    user = db_session.query(User).filter_by(user_id=user_id).first()
    if not user:
        log.error("User not found!")
        return None
    return user


def get_user_groups_by_username(user_name, region=utils.REGION_ID):
    db_session = DB_CONNECTION[region].get_session()
    user = db_session.query(User).filter_by(user_name=user_name).first()
    if not user:
        log.error("User not found!")
        return None
    sr_groups = [{"group_id": group.group_id, "name": group.name, "owner_id": group.owner_id} for group in user.groups]
    group_member_mr_mapping = db_session.query(GroupMemberMR).filter_by(user_id=user.user_id).all()
    # TODO based on region_id of group do a recursive loopkup
    mr_groups = [mapping.group_id for mapping in group_member_mr_mapping]

    return {
        "multi_region": mr_groups,
        "single_region": sr_groups
    }


def get_user_details_by_username(user_name, user_region):
    db_session = DB_CONNECTION[user_region].get_session()

    user = db_session.query(User).filter_by(user_name=user_name).first()
    if not user:
        log.error("User not found!")
        return None
    return user


def get_group_details(group_id, region):
    db_session = DB_CONNECTION[region].get_session()

    group = db_session.query(Group).filter_by(group_id=group_id).first()
    if not group:
        log.error("Group not found!")
        return None

    # if multi region entry, get members from group_member
    if group.multi_region:
        group_member_mr_mapping = db_session.query(GroupMemberMR).filter_by(group_id=group_id).all()
        members = [member.user_id for member in group_member_mr_mapping]
    else:
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


def get_group_by_name(group_name, region=utils.REGION_ID):
    home_db_session = DB_CONNECTION[region].get_session()

    group = home_db_session.query(Group).filter_by(name=group_name).first()
    if not group:
        log.error("Group not found!")
        return None

    return group


def add_member_to_group(member_id, group_id, member_region, group_region):
    group_db_session = DB_CONNECTION[group_region].get_session()
    group = group_db_session.query(Group).filter_by(group_id=group_id).first()

    if group.multi_region:
        group_member_mr_mapping = group_db_session.query(GroupMemberMR).filter_by(group_id=group_id).all()
        members = [member.user_id for member in group_member_mr_mapping]
        if len(members) >= 4:
            return False, "Group is full!"

        if member_id in members:
            return False, "User already in group!"

        for region_i in DB_CONNECTION:
            db_session = DB_CONNECTION[region_i].get_session()
            mr_mapping = GroupMemberMR(
                group_id=group_id,
                user_id=member_id,
                group_region_id=utils.REGIONS_INT[group_region],
                user_region_id=utils.REGIONS_INT[member_region]
            )
            db_session.add(mr_mapping)
            db_session.commit()
        log.info(f"User '{member_id}' added to group '{group_id}'.")
        return True, None

    else:
        member = group_db_session.query(User).filter_by(user_id=member_id).first()
        if member in group.members:
            return False, "User already in group!"
        if len(group.members) >= 4:
            return False, "Group is full!"
        group.members.append(member)
        group_db_session.commit()
        log.info(f"User {member_id} added to group {group_id}.")
        return True, None


def get_item(item_id):
    home_db_session = HOME_DB_CONNECTION.get_session()

    return home_db_session.query(Item).filter_by(item_id=item_id).first()


def get_items():
    home_db_session = HOME_DB_CONNECTION.get_session()

    items = home_db_session.query(Item).all()
    return items


def get_user_transactions(user_id):
    home_db_session = HOME_DB_CONNECTION.get_session()

    transactions = home_db_session.query(Transaction).filter_by(user_id=user_id).all()
    return transactions


def get_group_transactions(group_id):
    home_db_session = HOME_DB_CONNECTION.get_session()

    transactions = home_db_session.query(Transaction).filter_by(group_id=group_id).all()
    return transactions
