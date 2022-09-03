import os


# Returns a dictionary with configuration information, to load up the database
def con_config(host="localhost", database="attendance", user="postgres") -> dict:
    config = {
        'host': host,
        'database': database,
        'user': user,
        'password': os.getenv("POSTGRES_PASSWORD")
    }
    return config
