from api.core import app
import database.query as query


if __name__ == "__main__":
    app.config.update({"db_query": query})
    app.run(debug=True)