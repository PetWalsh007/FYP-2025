'''

Main file for the abstraction layer 
This file is responsible for the abstraction layer of the system where general connections and queries are passed to 
and passed to respective database connections

'''
from connections import connectcls_sql_server, connectcls_postgres
from fastapi import FastAPI

app = FastAPI()


sqls_con = None


@app.on_event("startup")
def startup():
    #Runs at FastAPI startup
    global sqls_con
    sqls_con = connectcls_sql_server('ODBC Driver 17 for SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')
    sqls_con.make_connection()

@app.on_event("shutdown")
def shutdown():
    # Closing connection when the worker shuts down
    global sqls_con
    if sqls_con:
        sqls_con.close_connection()



@app.get("/data")
def get_data(database: str ="null", table_name: str = "null", fil_condition: str = '1=1', limit: int = 10):
    # Check if the database is SQL Server
    if database == 'sql_server':
        if table_name:
            query = f"SELECT TOP {limit} * from {table_name} WHERE {fil_condition}"
            result = sql_server(query)
            return result
        else:
            return {"error": "No table name provided"}
    # Check if the database is PostgreSQL
    elif database == 'postgres':
        if table_name:
            query = f"SELECT * from {table_name} LIMIT {limit}"
            result = postgres(query)
            return result
        else:
            return {"error": "No table name provided"}
    else:
        return {"error": "No database provided"}
    
    
# Function to query SQL Server database
def sql_server(query):
    # Test SQL Server connection
    # we want to use the connection object created globally 
    
    if sqls_con.conn is None:
        if sqls_con.con_err:
            return sqls_con.con_err
        else:
            return {"error": "SQL Server connection not established"}
    

    if sqls_con:
        # Execute query
            
        result = sqls_con.query(query)  


    return result

# Function to query PostgreSQL database
def postgres(query):

    # Test PostgreSQL connection
    test_conn_postgres = connectcls_postgres(
        driver_name="PostgreSQL Unicode",
        server_name="192.168.1.55",
        db_name="Test_DB",
        connection_username="test_user",
        connection_password="test_user"
    )

    # Make connection and get cursor object
    conn, cursor, errors = test_conn_postgres.make_connection()

    if conn and not errors:
        # Execute query
        result = test_conn_postgres.query(cursor, query)
        if result:
            print(result)
    if errors:
        # Print errors if any
        print(errors)
        return errors
        
    # Close connection
    if conn:
        test_conn_postgres.close_connection(conn)

    return result

