import logging
from time import sleep
import utils
import random

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table, DateTime, text, pool, Boolean
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

Base = declarative_base()

# Association table for the many-to-many relationship between Group and User
group_member_association = Table('group_member', Base.metadata,
                                 Column('user_id', Integer, ForeignKey('user.user_id')),
                                 Column('group_id', Integer, ForeignKey('group.group_id'))
                                 )


def _gen_id():
    return random.randint(10000000, 99999999)


class User(Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True, autoincrement=False)
    user_name = Column(String, unique=True)
    password = Column(String)
    groups = relationship('Group', secondary=group_member_association, back_populates='members')

    def __init__(self, user_name, password):
        super(User, self).__init__()
        self.user_id = _gen_id()
        self.user_name = user_name
        self.password = password


class Group(Base):
    __tablename__ = 'group'
    group_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String, unique=True)
    owner_id = Column(Integer, ForeignKey('user.user_id'))
    points = Column(Integer, default=0)
    multi_region = Column(Boolean, default=False)
    members = relationship('User', secondary=group_member_association, back_populates='groups')

    def __init__(self, name, owner_id, multi_region):
        super(Group, self).__init__()
        self.group_id = _gen_id()
        self.name = name
        self.owner_id = owner_id
        self.points = 0
        self.multi_region = multi_region


class GroupMemberMR(Base):
    __tablename__ = 'group_member_mr'
    group_id = Column(Integer)
    user_id = Column(Integer)
    group_region_id = Column(Integer)
    user_region_id = Column(Integer)
    member_id = Column(Integer, primary_key=True, autoincrement=True)


class Transaction(Base):
    __tablename__ = 'transaction'
    transaction_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    group_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)
    store = Column(String)
    total = Column(Float)
    points_redeemed = Column(Integer)
    points_awarded = Column(Integer)
    user = relationship("User", backref="transactions")

    def __init__(self, user_id, group_id, store, total, points_redeemed, points_awarded):
        super(Transaction, self).__init__()
        self.transaction_id = _gen_id()
        self.user_id = user_id
        self.group_id = group_id
        self.store = store
        self.total = total
        self.points_redeemed = points_redeemed
        self.points_awarded = points_awarded
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "timestamp": self.timestamp,
            "store": self.store,
            "total": self.total,
            "points_redeemed": self.points_redeemed,
            "points_awarded": self.points_awarded,
        }


class Item(Base):
    __tablename__ = 'item'
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    price = Column(Float)


# Define function to add items if they do not exist
def add_items(session):
    items = [
        {'item_id': 1, 'name': 'Coffee Latte', 'price': 3},
        {'item_id': 2, 'name': 'Coffee Espresso', 'price': 1.5},
        {'item_id': 3, 'name': 'Cake', 'price': 8},
        {'item_id': 4, 'name': 'Cookies', 'price': 8},
        {'item_id': 5, 'name': 'Hot Chocolate', 'price': 3.5}
    ]
    for item_data in items:
        item = session.query(Item).filter_by(item_id=item_data['item_id']).first()
        if item is None:
            session.add(Item(**item_data))
    session.commit()


class TransactionItem(Base):
    __tablename__ = 'transaction_item'
    transaction_item_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('transaction.transaction_id'))
    item_id = Column(Integer, ForeignKey('item.item_id'))
    quantity = Column(Integer)
    item_total = Column(Float)

    # Relationships
    transaction = relationship("Transaction", backref="transaction_items")
    item = relationship("Item", backref="transaction_items")

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "item_total": self.item_total,
        }


class DatabaseConnection:
    def __init__(self, urls):
        self._primary_url = None
        self._urls = urls
        self.engine = None
        self._retries = 5
        self._retry_wait = 5
        self._connect_to_primary()

    def _connect_to_primary(self):
        # check if primary still the same or has changed
        if self._primary_url is not None:
            is_primary_same = not self._is_database_in_recovery_or_down(self._primary_url)
        else:
            is_primary_same = False

        # if not same, connect to db which is primary
        if not is_primary_same:
            number_of_tries = 0
            while number_of_tries <= self._retries:
                number_of_tries += 1
                for each_url in self._urls:
                    is_in_recovery_or_down = self._is_database_in_recovery_or_down(each_url)
                    if not is_in_recovery_or_down:
                        self._primary_url = each_url
                        self._is_current_connection_read_only = False
                        return
                sleep(self._retry_wait)
            raise Exception(f"Connecting to primary failed after {number_of_tries} retries!")

    def _is_database_in_recovery_or_down(self, url):
        self.engine = create_engine(url, poolclass=pool.QueuePool, pool_size=5, pool_recycle=3600)
        try:
            session = sessionmaker(bind=self.engine)()
            res = session.query(text('pg_is_in_recovery()')).all()
            is_in_recovery = res[0][0]
            session.close()
            self._is_current_connection_read_only = True
            return is_in_recovery
        except Exception as e:
            log.error(f"Failed to connect to database: {e}")
            return True

    def _connect_to_any(self):
        number_of_tries = 1

        while number_of_tries <= self._retries:
            number_of_tries += 1
            for each_url in self._urls:
                self.engine = create_engine(each_url, poolclass=pool.QueuePool, pool_size=5, pool_recycle=3600)
                try:
                    conn = self.engine.connect()
                    conn.close()
                    return
                except Exception as e:
                    log.error(f"Failed to connect to database: {e}")
        raise Exception(f"Connecting to any database failed after {number_of_tries} retries")

    # def _is_connected(self):
    #     return self.engine and self.engine.connect()

    def get_session(self, read_only=False):
        # if not self._is_connected():
        if read_only:
            self._connect_to_any()
        else:
            self._connect_to_primary()
        # elif self._is_current_connection_read_only and not read_only:
        #     self._connect_to_primary()
        return sessionmaker(bind=self.engine)()


DB_CONNECTION = {
    region_id: DatabaseConnection(url) for region_id, url in utils.REGION_URLS.items()
}

HOME_DB_CONNECTION = DB_CONNECTION[utils.REGION_ID]

# create all tables
Base.metadata.create_all(HOME_DB_CONNECTION.engine)

# add menu items
add_items(HOME_DB_CONNECTION.get_session())
