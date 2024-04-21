import os

REGION_ID = os.environ.get("REGION_ID")
REGION_URLS = {}

regions = os.environ.get("REGIONS").split(",")
for region in regions:
    user = os.environ.get(f"{region}_DB_USER")
    password = os.environ.get(f"{region}_DB_PASSWORD")
    hosts = os.environ.get(f"{region}_DB_HOSTS").split(",")
    ports = os.environ.get(f"{region}_DB_PORTS").split(",")
    db = os.environ.get(f"{region}_DB_DATABASE")
    db_urls = []
    for each_index in range(len(hosts)):
        db_urls.append(f"postgresql://{user}:{password}@{hosts[each_index]}:{ports[each_index]}/{db}")
    REGION_URLS[region] = db_urls
