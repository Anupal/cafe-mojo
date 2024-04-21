import os

# DB_URL = "sqlite:///./database/sqlite.db"
# DB_URL = "postgresql://user:password@localhost:5432/cafe_mojo"


def get_db_urls(home=True):
    region = "HOME" if home else "PEER"
    user = os.environ.get(f"{region}_DB_USER")
    if os.environ.get(f"{region}_DB_HOSTS") and "," in os.environ.get(f"{region}_DB_HOSTS"):
        hosts = os.environ.get(f"{region}_DB_HOSTS").split(",")
    else:
        hosts = None
    password = os.environ.get(f"{region}_DB_PASSWORD")
    if os.environ.get(f"{region}_DB_PORTS") and "," in os.environ.get(f"{region}_DB_PORTS"):
        ports = os.environ.get(f"{region}_DB_PORTS").split(",")
    else:
        ports = None
    db = os.environ.get(f"{region}_DB_DATABASE")

    if not user or not hosts or not password or not ports or not db:
        print(f"ERROR: Environment variables not set properly -> {region}_DB_HOSTS, {region}_DB_PORTS, {region}_DB_USER, {region}_DB_PASSWORD, {region}_DB_DATABASE")
        exit()
    db_urls = []
    for each_index in range(len(hosts)):
        db_urls.append(f"postgresql://{user}:{password}@{hosts[each_index]}:{ports[each_index]}/{db}")
    return db_urls


HOME_DB_CLUSTER_URLS = get_db_urls(True)
PEER_DB_CLUSTER_URLS = get_db_urls(False)

if "euw" in os.environ.get(f"HOME_DB_HOSTS"):
    HOME_REGION_ID = 0
    PEER_REGION_ID = 1
else:
    HOME_REGION_ID = 1
    PEER_REGION_ID = 0
