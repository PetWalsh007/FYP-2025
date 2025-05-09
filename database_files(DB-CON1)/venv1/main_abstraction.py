'''

Main file for the abstraction layer 
This file is responsible for the abstraction layer of the system where general connections and queries are passed to 
and passed to respective database connections

'''
from connections import connectcls_sql_server, connectcls_postgres
from fastapi import FastAPI, Request
import subprocess
import logging
from contextlib import asynccontextmanager
import time
import asyncio
import redis as rd
import random
import json
from datetime import datetime
import time as time

logging.basicConfig(filename="fastapi_lifespan.log", level=logging.INFO, format="%(asctime)s - %(message)s")

redis_host ='192.168.1.83'
redis_port = 6379


# Updated from FASTAPI docs to use async context manager https://fastapi.tiangolo.com/advanced/events/#lifespan

postgres_server_con = None  # Global variable for Postgres Server connection
# Global dictionary for all external DB connections
db_connections = {}
db_time_cols = {}
redis_client = None  # Global variable for Redis connection

def app_startup_routine():
    # this will serve as the app startup routine to check if the database connections are established 
    global postgres_server_con  
    global redis_client
 
    attempt = 0
    max_attempts = 5
    logging.info("***********************************")
    logging.info("Starting FastAPI lifespan function...")
    logging.info("Connecting to Postgres Server side database...")

    while postgres_server_con is None or attempt < max_attempts:
        try:
            postgres_server_con = open_server_db_con()
            if postgres_server_con.conn is not None:
                logging.info(f"Postgres Server connection established. {postgres_server_con}")
                break
        except Exception as e:
            logging.error(f"Error While starting connection to backend database server: {e}")
            postgres_server_con = None
        wait_time = (5 * attempt) + 3
        time.sleep(wait_time)
        attempt += 1
        
        logging.info(f"Retrying in {wait_time}s... (Attempt {attempt}/{max_attempts})")
        time.sleep(wait_time)

    if postgres_server_con is None:
        logging.error("Max attempts reached for Postgres Server DB connection.")
        logging.error("Check connection string, server status, or network access.")
        logging.info("***********************************")


    try:
        redis_client = rd.StrictRedis(host=redis_host, port=redis_port, db=0)
        redis_client.ping()
        logging.info("Connected to Redis server successfully.")
    except rd.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")

    pass

def connect_to_external_servers():
    # this will connect to the external servers and check if they are up and running 
    # we can use this to check if the servers are up and running before starting the app
    global postgres_server_con

    
    try:
        
        query = ("""
            SELECT 
                endpoint_name, endpoint_type, endpoint_ip, endpoint_port,
                driver_name, database_name, connection_uname, connection_pwd, metadata
            FROM "Platform-Data".databases
            WHERE is_active = TRUE
        """)
        rows = postgres_server_con.query(query)

        for row in rows:
            endpoint_name = row["endpoint_name"]
            endpoint_type = row["endpoint_type"]
            endpoint_ip = row["endpoint_ip"]
            endpoint_port = row["endpoint_port"]
            driver_name = row["driver_name"]
            database_name = row["database_name"]
            connection_uname = row["connection_uname"]
            connection_pwd = row["connection_pwd"]
            metadata = row["metadata"]

            logging.info(f"Attempting to connect to {endpoint_name} [{endpoint_type}] at {endpoint_ip}:{endpoint_port}...")

            try:
                if endpoint_type == 'sqlserver':
                    con = connectcls_sql_server(
                        driver_name, endpoint_ip, database_name, connection_uname, connection_pwd
                    )
                    logging.info(f"SQL Server connection [{endpoint_name}] established.")

                elif endpoint_type == 'postgresql':
                    con = connectcls_postgres(
                        driver_name=driver_name,
                        server_name=endpoint_ip,
                        db_name=database_name,
                        connection_username=connection_uname,
                        connection_password=connection_pwd
                    )
                    logging.info(f"PostgreSQL connection [{endpoint_name}] established.")

                else:
                    logging.warning(f"Unsupported DB type: {endpoint_type} for {endpoint_name}")

            except Exception as e:
                logging.error(f"Failed to connect to {endpoint_name}: {e}")

            # need to extract 'time_col_name' from metadata and add to the dict along with the connection obj
            metadata_load = json.loads(metadata) if metadata else {}
            time_col_name = metadata_load.get('time_col_name', None)
            if time_col_name:
                logging.info(f"Time column name for {endpoint_name}: {time_col_name}")
            else:
                logging.warning(f"No time column name found in metadata for {endpoint_name}.")
                
            db_connections[endpoint_name] = con
            db_time_cols[endpoint_name] = time_col_name

    except Exception as e:
        logging.error(f"Error fetching external DB config: {e}")
    pass



@asynccontextmanager
async def lifespan(app):
    # Runs at FastAPI startup

    global postgres_server_con

    app_startup_routine()
    connect_to_external_servers()
    pull_config_data()
    logging.info("Connecting to external databases...")
    # loop through the global db_connections dictionary and connect to the databases
    for db_name, con in db_connections.items():
        if con.conn is None:
            logging.error(f"Connection to {db_name} failed.")
        else:
            logging.info(f"Connection to {db_name} established.")





    yield

    # loop through the global db_connections dictionary and close the connections

    for db_name, con in db_connections.items():
        try:
            if con.conn is not None:
                con.close_connection()
                logging.info(f"Connection to {db_name} closed.")
            else:
                logging.warning(f"Connection to {db_name} was not established.")
        except Exception as e:
            logging.error(f"Error closing connection to {db_name}: {e}")



    if postgres_server_con:
        postgres_server_con.close_connection()
    if redis_client:
        redis_client.close()
    

    logging.info("Database connections closed.")
    logging.info("***********************************")

app = FastAPI(lifespan=lifespan)

CONFIG_FILE = "pwd.json"
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        return {}


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        return {}

def save_config(config_data):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)



def pull_config_data():
    # function to pull the updated config data from the server db 

    # send a request to the abstraction layer /healthcheck endpoint to see if tis active 
    # if it is active then send a request to the abstraction layer /config endpoint to get the config data



    config_local = load_config()
    config_server = None


    config_server = fetch_configuration_Data()
    if config_server is None:
        logging.error("Failed to fetch configuration data from server.")
        return
    if "error" in config_server:
        logging.error(f"Error fetching configuration data from server: {config_server['error']}")
        return
    if "endpoints" not in config_server:
        logging.error("No endpoints found in the configuration data from server.")
        return

    try:
        # Extracting the "endpoints" section from both configurations
        local_endpoints = config_local.get("endpoints", {})
        server_endpoints = config_server.get("endpoints", {})

        # Compare and update the local endpoints with server endpoints
        for key, server_endpoint in server_endpoints.items():
            if key not in local_endpoints or local_endpoints[key] != server_endpoint:
                logging.info(f"Updating endpoint '{key}' in local config with server data.")
                local_endpoints[key] = server_endpoint

        # Save the updated endpoints back to the local configuration
        config_local["endpoints"] = local_endpoints

        # Save the updated local configuration to the config file
        save_config(config_local)
        logging.info("Local configuration updated successfully with server data.")

    except Exception as e:
        logging.error(f"Error updating local config with server data: {e}")


    pass









# adding health check to endpoints to help startups
@app.get("/healthcheck")
async def healthcheck():
    #Health check endpoint to verify if the service is running.
    
    return {"status": "OK"}

def fetch_configuration_Data():
# Health check endpoint to verify if the service is running.
    global db_connections
    global postgres_server_con
    global redis_client

    
    
    # Check if the Postgres Server connection is established
    if postgres_server_con.conn is None:
        if postgres_server_con.con_err:
            logging.error(f"Postgres Server connection error: {postgres_server_con.con_err}")
            return {"error": postgres_server_con.con_err}
        else:
            logging.error("Postgres Server connection not established")
            return {"error": "Postgres Server connection not established"}
    
    # Check if the Redis connection is established
    if redis_client is None:
        logging.error("Redis connection not established")
        return {"error": "Redis connection not established"}

    # fetch platform-Data.endpoints table and we can bundle it up into a json object and return it

    query = """
        SELECT
            endpoint_name, endpoint_ip, endpoint_port
            FROM "Platform-Data".endpoints
            WHERE is_active = TRUE
    """
    try:
        postgres_server_con.cursor.execute(query)
        rows = postgres_server_con.cursor.fetchall()
        logging.info(f"Query executed successfully: {query}")

       
        endpoints = {}
        for row in rows:
            endpoint_name = row[0]
            endpoint_ip = row[1]
            endpoint_port = row[2]
            endpoints[endpoint_name] = {
                "ip": endpoint_ip,
                "port": endpoint_port
            }

        # log to output
        logging.info(f"Formatted endpoints: {endpoints}")


        return {"endpoints": endpoints}

    except Exception as e:
        logging.error(f"Error fetching endpoints: {e}")
        return {"error": "Failed to fetch endpoints"}
   

@app.get("/config")
async def get_config():
    logging.info("Received request for /config")
    return fetch_configuration_Data()


# https://stackoverflow.com/questions/10252010/serializing-class-instance-to-json 
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")




@app.post("/add_database_connection")
async def add_database_connection(request: Request):
    """
    Accepts a JSON payload to add a new database connection to the PostgreSQL server.
    """
    logging.info("Received request for /add_database_connection")
    try:
        
        data = await request.json()
        logging.info(f"Received data: {data}")
        # Unpack the JSON data
        endpoint_name = data.get("endpoint_name")
        endpoint_type = data.get("endpoint_type")
        endpoint_ip = data.get("endpoint_ip")
        endpoint_port = data.get("endpoint_port")
        driver_name = data.get("driver_name")
        database_name = data.get("database_name")
        connection_uname = data.get("connection_uname")
        connection_pwd = data.get("connection_password")
        metadata = data.get("metadata", {})
        is_active = data.get("is_active", True)  

        # Validate 
        if not all([endpoint_name, endpoint_type, endpoint_ip, endpoint_port, driver_name, database_name, connection_uname, connection_pwd]):
            logging.error("Missing required fields in the JSON payload.")
            return {"error": "Missing required fields in the JSON payload."}

        # Check con
        if postgres_server_con.conn is None:
            if postgres_server_con.con_err:
                logging.error(f"Postgres Server connection error: {postgres_server_con.con_err}")
                return {"error": postgres_server_con.con_err}
            else:
                logging.error("Postgres Server connection not established")
                return {"error": "Postgres Server connection not established"}

        # https://stackoverflow.com/questions/26703476/how-to-perform-update-operations-on-columns-of-type-jsonb
        # https://community.retool.com/t/updating-jsonb-column/19314
        
        query = """
            INSERT INTO "Platform-Data".databases 
            (endpoint_name, endpoint_type, endpoint_ip, endpoint_port, 
            driver_name, database_name, connection_uname, connection_pwd, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (endpoint_name, endpoint_type, endpoint_ip, endpoint_port, driver_name, database_name, connection_uname, connection_pwd, is_active)
        
        # Update the metadata column
        metadata_json = json.dumps(metadata) 
        update_query = """
            UPDATE "Platform-Data".databases 
            SET metadata = ?::jsonb
            WHERE endpoint_name = ?;
        """
        update_values = (metadata_json, endpoint_name)


        try:
            postgres_server_con.cursor.execute(query, values)
            postgres_server_con.conn.commit()

            logging.info(f"Query executed successfully: {query}")

            postgres_server_con.cursor.execute(update_query, update_values)
            postgres_server_con.conn.commit()
            logging.info(f"Metadata updated successfully for endpoint: {endpoint_name}")
     
            logging.info(f"Database connection added successfully: {endpoint_name}")
            return {"message": f"Database connection '{endpoint_name}' added successfully."}


        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return {"error": "Error executing query"}
        

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return {"error": f"Error processing request {e}"}



@app.get("/data")
async def get_data(database: str = "null",table_name: str = "null", fil_condition: str = '1=1', limit: int = 10, start: str = None, end: str = None, user:str = "null"):
    # Check if the database is SQL Server
    # log all the inputs to the function
    global db_connections
    global postgres_server_con

    # build a query string to store in a lookup in redis 
    logging.info(f"user: {user}")
    redis_query_key = f"{database}_{table_name}_{start}_{end}"
    # check redis for key and return value to front end if it exsits 
    try:
        # check if the key exists in redis
        redis_value = redis_client.get(redis_query_key)
        if redis_value:
            logging.info(f"Key {redis_query_key} found in Redis, returning cached value.")
            store_query_data(redis_value, reuse_qry=True)
            
            return {"redis_key": redis_value}
    except Exception as e:
        logging.error(f"Error checking Redis for key {redis_query_key}: {e}")
        return {"error": f"Error checking Redis for key {redis_query_key}"}


    logging.info(f"Received request for /data with database: {database},  table_name: {table_name}, fil_condition: {fil_condition}, limit: {limit}, start: {start}, end: {end}")
    if start is None or end is None:
        logging.error("No start or end date provided")
        return {"error": "No start or end date provided"}
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').strftime('%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d').strftime('%Y-%m-%d')
        logging.info(f"Parsed start date: {start_date}, end date: {end_date}")
    except ValueError as e:
        logging.error(f"Date format error: {e}")
        return {"error": "Invalid date format"}
    
    # database sent will be 

    # get the connection object from the db_connections dictionary
    # we will use the connection object created globally
    connection_obj = db_connections.get(database)
    time_col_name = db_time_cols.get(database)
    if connection_obj is None:
        logging.error(f"Connection to {database} failed.")
        return {"error": f"Connection to {database} failed."}
    
    if "server" in database.lower():

        if table_name:
            date_filter = ""
            if start and end:
                date_filter = f" {time_col_name} BETWEEN '{start_date}' AND '{end_date}'"
            query = f"SELECT * from {table_name} WHERE {date_filter}"
            logging.info(f"Executing SQL Server query: {query}")
            result = await db_query(query, connection_obj)
            redis_db_key = send_to_redis(result, redis_query_key)
            # we need to send to postgres server db to store key id etc 
            store_query_data(redis_db_key, query_table=table_name, query_db=database, reuse_qry=False, qry=query, user=user)
            return {"redis_key": redis_db_key}
        else:
            return {"error": "No table name provided"}
    # Check if the database contains 'postgres'
    elif 'postgres' in database.lower():
        if table_name:
            date_filter = ""
            if start and end:
                date_filter = f" AND {table_name}.{time_col_name} BETWEEN '{start}' AND '{end}'"
            query = f"SELECT * from {table_name} WHERE {fil_condition}{date_filter}"
            logging.info(f"Executing PostgreSQL query: {query}")
            result = await db_query(query, connection_obj)
            redis_db_key = send_to_redis(result, redis_query_key)
            store_query_data(redis_db_key, query_table=table_name, query_db=database, reuse_qry=False, qry=query, user=user)
            return {"redis_key": redis_db_key}
        else:
            return {"error": "No table name provided"}
    else:
        return {"error": "No database provided"}
    


@app.get("/command")
async def get_command(rst: str = "null"):
    # receive commands and resart the server

    # Code is to be updated to include a connection to server side db where rand_number is stored
    if rst == 'restart_server_main_abstraction':
        subprocess.Popen(["sudo", "killall", "gunicorn"])
        
        return {"message": "Server shutdown initiated, Server will automatically restart."}
    else:
        return {"error": "No command provided"}
    

@app.post("/store_processed_data")
async def rec_store_req(key_proc: str = "null", key_raw: str = "null", analysis_type: str = "null"):  
    # recieve the request from backend to store in redis db - redis_processed_log - this will be passed to 
    logging.info(f"Received request for /store_processed_data with key_proc: {key_proc}, key_raw: {key_raw}, analysis_type: {analysis_type}")
    if postgres_server_con.conn is None:
        if postgres_server_con.con_err:
            logging.error(f"Postgres Server connection error: {postgres_server_con.con_err}")
            return postgres_server_con.con_err
        else:
            logging.error("Postgres Server connection not established")
            return {"error": "SQL Server connection not established"}
    
    table = "redis_data.redis_processed_log"
    query = f"INSERT INTO {table} (redis_processed_key, redis_key, analysis_type, processed_request) VALUES (?, ?, ?, ?)"
    values = (key_proc, key_raw, analysis_type, 1)
    try:
        postgres_server_con.cursor.execute(query, values)
        postgres_server_con.conn.commit()
        logging.info(f"Query executed successfully: {query}")
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return {"error": "Error executing query"}




def store_query_data(key, query_table="", query_db="", reuse_qry=False, qry="", user="null"):
    # this will take the redis key and the query and store iin the data base 
     # Shared connection check
    if postgres_server_con.conn is None:
        if postgres_server_con.con_err:
            logging.error(f"Postgres Server connection error: {postgres_server_con.con_err}")
            return postgres_server_con.con_err
        else:
            logging.error("Postgres Server connection not established")
            return {"error": "SQL Server connection not established"}
    logging.info(f"value of reuse_qry: {reuse_qry}")
    if reuse_qry:
        logging.info(f"Received request for /store_query_data with reuse_qry: {reuse_qry}, key: {key}, query_table: {query_table}, query_db: {query_db}")
        table = "redis_data.reused_queries"
        query = f"INSERT INTO {table} (redis_key) VALUES (?)"
        values = (key,) # one tuple value req
    else:
        logging.info(f"Received request for /store_query_data")
        table = "redis_data.redis_cache_log"
        query = f"INSERT INTO {table} (redis_key, query_text, query_database, query_table, client_ip) VALUES (?, ?, ?, ?, ?)"
        values = (key, qry, query_db, query_table, user)
    logging.info(f"Executing Postgres Server query: {query} with values {values}")
    # execute and commit the query
    try:
        postgres_server_con.cursor.execute(query, values)
        postgres_server_con.conn.commit()
        logging.info(f"Query executed successfully: {query}")
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return {"error": "Error executing query"}





    
# Function to query SQL Server database
async def db_query(query, con_obj):
    # standard function to query the database and return the result
    
    logging.info(f"Received request for /sql_server")
    if con_obj.conn is None:
        if con_obj.con_err:
            return con_obj.con_err
        else:
            return {"error": "SQL Server connection not established"}
    result = await asyncio.to_thread(con_obj.query, query)

    return result



# function to send to redis

def send_to_redis(redis_value, redis_qry_key):
    # Send data to Redis with a random key and return the key to the call which returns to user


    while True:
        try:
            logging.info(f"Storing result in Redis with random key")
            rand_number = random.randint(1, 1000)
            # add 5 random alpha chars to the rand_number to make it unique
            redis_key = str(rand_number) + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
            # check if key already exists in redis
            if redis_client.exists(redis_key):
                logging.info(f"Key {redis_key} already exists in Redis, generating a new key...")
                continue  # Key exists, generate a new one
            else:
                logging.info(f"Generated random key: {redis_key}")
                break  # Key is unique, exit the loop
            
        except Exception as e:
            logging.error(f"Error generating random key: {e}")
            return {"Error generating random key"}
    try:
        redis_client.set(redis_key, json.dumps(redis_value, default=json_serial), ex=3600)  # Set TTL to 1 hour
        logging.info(f"Stored result in Redis with key: {redis_key}")
    except Exception as e:
        logging.error(f"Error storing result in Redis: {e}")
        return {"Error storing result in Redis"}

    
    # first store the query in redis with the key as the query string
    try:
        redis_client.set(redis_qry_key, redis_key,  ex=3600)  # Set TTL to 1 hour
        logging.info(f"Stored result in Redis with key: {redis_qry_key}")
    except Exception as e:
        logging.error(f"Error storing result in Redis: {e}")
        return {"Error storing result in Redis"}

    return redis_key


def open_server_db_con():
    # Open the connection to the server side database
    logging.info("Opening connection to server side database...")
    try:
        with open('pwd.json') as json_file:
            data = json.load(json_file)
            postgres_con2 = connectcls_postgres(
                driver_name="PostgreSQL Unicode",
                server_name=data['postgres']['host'],
                db_name=data['postgres']['db_name'],
                connection_username=data['postgres']['uname'],
                connection_password=data['postgres']['password']
            )

        logging.info(f"Postgres Server connection established: {postgres_con2}")
        logging.info(f"data returned from connection: {postgres_con2.conn}, {postgres_con2.cursor}, {postgres_con2.con_err}")
        logging.info(f"Postgres Server connection established: {postgres_con2.conn is not None}")
        return postgres_con2
    except Exception as e:
        logging.error(f"Error While starting connection to backend database server: {e}")
        postgres_con2 = None
        return postgres_con2
    