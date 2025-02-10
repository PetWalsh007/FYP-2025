'''

Main file for the abstraction layer 
This file is responsible for the abstraction layer of the system where general connections and queries are passed to 
and passed to respective database connections

'''
from connections import connectcls_sql_server, connectcls_postgres
from fastapi import FastAPI
import subprocess
import logging
from contextlib import asynccontextmanager
import time

logging.basicConfig(filename="fastapi_lifespan.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Updated from FASTAPI docs to use async context manager https://fastapi.tiangolo.com/advanced/events/#lifespan

@asynccontextmanager
async def lifespan(app):
    # Runs at FastAPI startup
    global sqls_con 
    global postgres_con 
    logging.info("Starting FastAPI lifespan function...")
    sqls_con = connectcls_sql_server('ODBC Driver 17 for SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')
    
    postgres_con = connectcls_postgres(
        driver_name="PostgreSQL Unicode",
        server_name="192.168.1.55",
        db_name="Test_DB",
        connection_username="test_user",
        connection_password="test_user"
    )

    logging.info("Database connections initialized.")
    logging.info(f'SQL Server connection: {sqls_con.conn}, PostgreSQL connection: {postgres_con.conn}')

    yield

    # Closing connection when the worker shuts down
    if sqls_con:
        sqls_con.close_connection()
    if postgres_con:
        postgres_con.close_connection()

    logging.info("Database connections closed.")

app = FastAPI(lifespan=lifespan)


@app.get("/data")
async def get_data(database: str ="null", table_name: str = "null", fil_condition: str = '1=1', limit: int = 10):
    # Check if the database is SQL Server
    if database == 'sql_server':
        if table_name:
            query = f"SELECT TOP {limit} * from {table_name} WHERE {fil_condition}"
            result = await sql_server(query)
            return result
        else:
            return {"error": "No table name provided"}
    # Check if the database is PostgreSQL
    elif database == 'postgres':
        if table_name:
            query = f"SELECT * from {table_name} LIMIT {limit}"
            result = await postgres(query)
            return result
        else:
            return {"error": "No table name provided"}
    else:
        return {"error": "No database provided"}
    


@app.get("/command")
async def get_command(rst: str = "null"):
    # receive commands and resart the server

    # Code is to be updated to include a connection to server side db where rand_number is stored
    if rst == 'restart_server_main_abstraction':
        subprocess.Popen(["sudo", "systemctl", "stop", "gunicorn"])
        time.sleep(3)
        subprocess.Popen(["sudo", "systemctl", "start", "gunicorn"])
        
        return {"message": "Server restarted"}
    else:
        return {"error": "No command provided"}
    
    
# Function to query SQL Server database
async def sql_server(query):
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
async def postgres(query):

    
    if postgres_con.conn is None:
        if postgres_con.con_err:
            return postgres_con.con_err
        else:
            return {"error": "Postgres connection not established"}
    

    if postgres_con:
        # Execute query
            
        result = postgres_con.query(query)  


    return result

