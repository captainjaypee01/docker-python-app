import pymysql
from pymysql.err import OperationalError

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Connected to the database")
        except OperationalError as e:
            print("Error connecting to the database:", str(e))

    def execute_query(self, query, params=None):
        if not self.connection:
            print("No database connection. Connect to the database first.")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print("Error executing query:", str(e))
            return None

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Disconnected from the database")
        else:
            print("No database connection to disconnect")

# Create a singleton instance of the Database class
database = Database(host='localhost', user='your_user', password='your_password', database='your_database')
