DB_CLUSTER_URLS = ["postgresql://postgres:password@localhost:5430/cafe_mojo", "postgresql://postgres:password@localhost:5431/cafe_mojo"]
# import os
#
# # DB_URL = "sqlite:///./database/sqlite.db"
# # DB_URL = "postgresql://user:password@localhost:5432/cafe_mojo"
#
# def get_db_url():
#     user = os.environ.get("DB_USER")
#     host = os.environ.get("DB_HOST")
#     password = os.environ.get("DB_PASSWORD")
#     port = os.environ.get("DB_PORT")
#     db = os.environ.get("DB_DATABASE")
#
#     if not user or not host or not password or not port or not db:
#         print("ERROR: Environment variables not set properly -> DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE")
#         exit()
#     return f"postgresql://{user}:{password}@{host}:{port}/{db}"
#
# DB_URL = get_db_url()