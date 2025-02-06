# Class definition for the Connections class 

'''
This module for import into main_abstration.py contains the class definitions for the connections to various databases,
such as SQL Server and PostgreSQL.

Class is also set to define differnt sytnax for various databases.

'''
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

        # Placeholder testing for initalising and establishing a connection as the class is initalised - to allow reuse of connections
        # self.con_string = self.connect_str() # call connect string func on initalisation of object 


    def __str__(self):
        return f'Connection ID: {self.connection_id}, User ID: {self.user_id}, Connection Name: {self.connection_name}, Connection Type: {self.connection_type}, Connection URL: {self.connection_url}, Connection Username: {self.connection_username}, Connection Password: {self.connection_password}'
    
    def connect_str(self):
        """
        Constructs the connection string for the database connection.
        
        Returns:
            str: The connection string.
        """
        # connection string 
        return  f'DRIVER={{{self.driver_name}}};SERVER={self.server_name};DATABASE={self.db_name};UID={self.connection_username};PWD={self.connection_password};'
    
    def make_connection(self):
        try:
            conn = pyodbc.connect(self.connect_str())
            
            cursor = conn.cursor()
            return conn, cursor, None
        except pyodbc.OperationalError as e:
            return None, None, [{"error": "Operational error - Check database connection and server status"}]
        except pyodbc.IntegrityError as e:
            return None, None, [{"error": "Integrity error - Check data integrity constraints"}]
        except pyodbc.ProgrammingError as e:
            return None, None, [{"error": "Programming error - Check SQL syntax and table/column names"}]
        except pyodbc.DatabaseError as e:
            return None, None, [{"error": "Database error - General database error occurred"}]
        except pyodbc.Error as e:
            return None, None, [{"error": f"General error - {str(e)}"}]

        
    
    def query(self, cursor, query):
        try: 
            cursor.execute(query)  # Execute the query
            rows = cursor.fetchall()  # Fetch all rows
            # Convert rows to list of dictionaries
            result = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
            return result
        except pyodbc.ProgrammingError as e:
            print(f"Query failed: {e}")
            return [{"error": "Query failure - Check SQL syntax"}]
        except pyodbc.DatabaseError as e:
            print(f"Database failure: {e}")
            return [{"error": "Database failure - Check database connection and query"}]
        except pyodbc.Error as e:
            print(f"Query failed: {e}")
            return [{"error": f"General error - {str(e)}"}]
    
    def close_connection(self, conn):
        conn.close()
        print("Connection closed")

# class for the connections to postgresql

class connectcls_postgres:

    def __init__(self, driver_name, server_name, db_name, connection_username, connection_password, port=5432):
        self.driver_name = driver_name
        self.server_name = server_name
        self.db_name = db_name
        self.connection_username = connection_username
        self.connection_password = connection_password
        self.port = port

    def __str__(self):
        return f'Connection ID: {self.connection_id}, User ID: {self.user_id}, Connection Name: {self.connection_name}, Connection Type: {self.connection_type}, Connection URL: {self.connection_url}, Connection Port: {self.connection_port}, Connection Username: {self.connection_username}, Connection Password: {self.connection_password}'

    def connect_str(self):
        # connection string 
        return  f"DRIVER={{{self.driver_name}}};SERVER={self.server_name};DATABASE={self.db_name};PORT={self.port};UID={self.connection_username};PWD={self.connection_password};"
    
    def make_connection(self):
        
        try:
            conn = pyodbc.connect(self.connect_str())
            print("Connection to PostgreSQL is successful")
            cursor = conn.cursor()
            return conn, cursor, None
        except pyodbc.OperationalError as e:
            return None, None, [{"error": "Operational error - Check database connection and server status"}]
        except pyodbc.IntegrityError as e:
            return None, None, [{"error": "Integrity error - Check data integrity constraints"}]
        except pyodbc.ProgrammingError as e:
            return None, None, [{"error": "Programming error - Check SQL syntax and table/column names"}]
        except pyodbc.DatabaseError as e:
            return None, None, [{"error": "Database error - General database error occurred"}]
        except pyodbc.Error as e:
            return None, None, [{"error": f"General error - {str(e)}"}]

    def query(self, cursor, query):
        try:
            cursor.execute(query)  # Execute the query
            rows = cursor.fetchall()  # Fetch all rows
            # Convert rows to list of dictionaries
            result = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
            return result
        except pyodbc.ProgrammingError as e:
            print(f"Query failed: {e}")
            return [{"error": "Query failure - Check SQL syntax"}]
        except pyodbc.DatabaseError as e:
            print(f"Database failure: {e}")
            return [{"error": "Database failure - Check database connection and query"}]
        except pyodbc.Error as e:
            print(f"Query failed: {e}")
            return [{"error": f"General error - {str(e)}"}]

    def close_connection(self, conn):
        conn.close()  # Close the connection
        print("Connection closed")
