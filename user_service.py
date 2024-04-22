from api.user import app
import database.query as query


if __name__ == "__main__":
    app.config.update({"db_query": query})
    app.run(host="0.0.0.0")