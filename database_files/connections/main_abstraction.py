# Main file for the abstraction layer
# This file is responsible for the abstraction layer of the database connections and queries

# Here we will take the paramters passed from inside the system and setup the end points for the database

from connections import *
from flask import Flask, jsonify, request


app = Flask(__name__)
@app.route('/data', methods=['GET'])

def get_data():
    fil_condition = request.args.get('filter', '1=1') # Default to no filter
    limit = request.args.get('limit', 10)
    table_name = request.args.get('table_name', None)
    data_base = request.args.get('database', None)
    if data_base == 'sql_server':
            
        if table_name:
            query = f"SELECT TOP {limit} * from {table_name} WHERE {fil_condition}"

            result = sql_server(query)
  
            return jsonify(result)
        
        else:
            return jsonify({"error": "No table name provided"})
    elif data_base == 'postgres':
        if table_name:
            query = f"SELECT * from {table_name} LIMIT {limit}"
            result = postgres(query)

            return jsonify(result)
        else:
            return jsonify({"error": "No table name provided"})
    else:
        return jsonify({"error": "No database provided"})
    



def sql_server(query):
    # test sql server connection
    test_con = connectcls_sql_server('ODBC Driver 17 for SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')

    conn, cursor, errors = test_con.make_connection() # make connection and get cursor object
    if conn:
        result = test_con.query(cursor, query)
        if result:
            pass
    if errors:
        print(errors)
        return errors


    # close connection
    if conn:
        test_con.close_connection(conn)

    return result



def postgres(query):

    # test postgres connection
    test_conn_postgres = connectcls_postgres(
        driver_name="PostgreSQL Unicode",
        server_name="192.168.1.55",
        db_name="Test_DB",
        connection_username="test_user",
        connection_password="test_user"
    )

    conn, cursor, errors = test_conn_postgres.make_connection() # make connection and get cursor object

    if conn and not errors:
        result = test_conn_postgres.query(cursor, query)
        if result:
            print(result)
    if errors:
        print(errors)
        return errors
        
    # close connection
    if conn:
        test_conn_postgres.close_connection(conn)

    return result



