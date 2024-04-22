from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

import utils

# Initialize Flask app
app = Flask(__name__)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"  # Change this to your secret key
jwt = JWTManager(app)


# Assume the add_*, get_*, and authenticate_user functions are defined here or imported

@app.route('/user/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    region = request.json.get('region', utils.REGION_ID)
    if region not in utils.REGIONS:
        return jsonify({'error': f'Invalid region, allowed values - {utils.REGIONS}'}), 400

    user = app.config["db_query"].authenticate_user(username, password, region)
    if user:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@app.route('/user/signup', methods=['POST'])
def signup():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username is None or password is None:
        return jsonify({"msg": "Invalid data"}), 400
    user = app.config["db_query"].add_user(username, password)
    if user:
        return jsonify({"msg": "User created", "user_id": user.user_id}), 201
    else:
        return jsonify({"msg": "Username already exists"}), 400


@app.route('/user/memberships', methods=['GET'])
@jwt_required()
def get_user_groups():
    current_user_username = get_jwt_identity()

    region = request.args.get('region', utils.REGION_ID)
    if region not in utils.REGIONS:
        return jsonify({'error': f'Invalid region, allowed values - {utils.REGIONS}'}), 400

    user = app.config["db_query"].get_user_details_by_username(current_user_username, region)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    groups = app.config["db_query"].get_user_groups_by_username(current_user_username, region)
    return jsonify(groups), 200


@app.route('/transaction/add', methods=['POST'])
@jwt_required()
def add_transaction_with_items():
    # Extract the current user's identity from the JWT token
    current_user_username = get_jwt_identity()

    region = request.json.get('region', utils.REGION_ID)
    if region not in utils.REGIONS:
        return jsonify({'error': f'Invalid region, allowed values - {utils.REGIONS}'}), 400

    # Find the user by username
    user = app.config["db_query"].get_user_details_by_username(current_user_username, region)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    user_id = user.user_id
    group_id = data.get('group_id')
    store = data.get('store')
    points_redeemed = data.get('points_redeemed')
    items = data.get('items')  # Expected to be a list of dicts, each with 'item_id', 'quantity'

    transaction, transaction_items = app.config["db_query"].add_transaction(
        user_id, group_id, store, points_redeemed, items
    )

    if not transaction or not transaction_items:
        return jsonify({"msg": "Transaction failed!"}), 500
    else:
        return jsonify({
            "msg": "Transaction and items added successfully",
            "transaction": transaction,
            "transaction_items": transaction_items
        }), 201


@app.route('/item/add', methods=['POST'])
@jwt_required()
def add_item():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    if not name or price is None:
        return jsonify({"msg": "Missing item name or price"}), 400

    item = app.config["db_query"].add_item(name, price)
    if item:
        return jsonify({"msg": "Item added successfully", "item_id": item.item_id}), 201
    else:
        return jsonify({"msg": "Failed to add item"}), 500


@app.route('/item/all', methods=['GET'])
@jwt_required()
def get_items():
    items = app.config["db_query"].get_items()
    items_data = [{"item_id": item.item_id, "name": item.name, "price": item.price} for item in items]
    return jsonify(items_data), 200


@app.route('/group/add', methods=['POST'])
@jwt_required()
def create_group():
    current_user = get_jwt_identity()
    group_name = request.json.get('name', None)

    region = request.json.get('region', utils.REGION_ID)
    if region not in utils.REGIONS:
        return jsonify({'error': f'Invalid region, allowed values - {utils.REGIONS}'}), 400

    multi_region = request.json.get('multi_region', None)
    if multi_region == 'true':
        multi_region = True
    elif not multi_region or multi_region == 'false':
        multi_region = False
    else:
        return jsonify({"msg": "Invalid value for 'multi_region', use 'true' or 'false'"}), 400

    # Find the user ID based on the JWT identity
    user = app.config["db_query"].get_user_details_by_username(current_user, region)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    group = app.config["db_query"].add_group(user.user_id, group_name, region, multi_region)
    if group:
        return jsonify({"msg": "Group created", "group_id": group.group_id}), 201
    else:
        return jsonify({"msg": "Failed to create group"}), 400


@app.route('/group/add-member', methods=['POST'])
@jwt_required()
def add_group_member():
    data = request.get_json()

    group_region = request.json.get('region', utils.REGION_ID)
    if group_region not in utils.REGIONS:
        return jsonify({'error': f'Invalid group region, allowed values - {utils.REGIONS}'}), 400

    group_name = data.get('group_name')
    member_user_name = data.get('member_user_name')
    member_region = request.json.get('member_region', utils.REGION_ID)
    if member_region not in utils.REGIONS:
        return jsonify({'error': f'Invalid member region, allowed values - {utils.REGIONS}'}), 400

    group = app.config["db_query"].get_group_by_name(group_name, group_region)
    if not group:
        return jsonify({"msg": "Group not found"}), 404

    if not group.multi_region and member_region != group_region:
        return jsonify({"msg": "Cannot add user from different region to a non multi-region group"}), 400

    user = app.config["db_query"].get_user_details_by_username(member_user_name, member_region)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    success, msg = app.config["db_query"].add_member_to_group(user.user_id, group.group_id, member_region, group_region)
    if success:
        return jsonify({"msg": "Member added to group successfully"}), 201
    else:
        return jsonify({"msg": f"Failed to add member to group - '{msg}'"}), 500


@app.route('/group/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group(group_id):
    region = request.args.get('region', utils.REGION_ID)
    if region not in utils.REGIONS:
        return jsonify({'error': f'Invalid region, allowed values - {utils.REGIONS}'}), 400

    group_details = app.config["db_query"].get_group_details(group_id, region)
    if not group_details:
        return jsonify({"msg": "Group not found"}), 404

    # Enhance group details with member information
    members_data = [{"user_id": member_id} for member_id in group_details['members']]
    group_details['members'] = members_data
    return jsonify(group_details), 200


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "ok"}), 200