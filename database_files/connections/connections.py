# Class definition for the Connections class
import pyodbc

class connectcls_sql_server:

    def __init__(self, driver_name , server_name, db_name,connection_username, connection_password, connection_id=None, user_id=None, connection_name=None,  connection_url=None, connection_type=None):
        self.driver_name = driver_name
        self.server_name = server_name
        self.db_name = db_name
        self.connection_username = connection_username
        self.connection_password = connection_password
        self.connection_id = connection_id
        self.user_id = user_id
        self.connection_name = connection_name
        self.connection_url = connection_url
        self.connection_type = connection_type

    def __str__(self):
        return f'Connection ID: {self.connection_id}, User ID: {self.user_id}, Connection Name: {self.connection_name}, Connection Type: {self.connection_type}, Connection URL: {self.connection_url}, Connection Port: {self.connection_port}, Connection Username: {self.connection_username}, Connection Password: {self.connection_password}'
    
    def connect_str(self):
        # connection string 
        return  f'DRIVER={{{self.driver_name}}};SERVER={self.server_name};DATABASE={self.db_name};UID={self.connection_username};PWD={self.connection_password};'
    
    def make_connection(self):
        try:
            conn = pyodbc.connect(self.connect_str())
            print("Connection to SQL Server is successful")
            cursor = conn.cursor()
        except pyodbc.DatabaseError as e:
            print(f"Database connection failed: {e}")
        return conn, cursor
    
    def query(self, cursor, query):
        
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [dict(zip([column[0] for column in cursor.description], row)) for row in rows] # Placeholder for returning the result
        return result
    
    def close_connection(self, conn):
        conn.close()
        print("Connection closed")