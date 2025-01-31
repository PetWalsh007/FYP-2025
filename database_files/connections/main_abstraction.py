# Main file for the abstraction layer
# This file is responsible for the abstraction layer of the database connections and queries

# Here we will take the paramters passed from inside the system and setup the end points for the database

from connections import *



def sql_server(query):
    # test sql server connection
    test_con = connectcls_sql_server('ODBC Driver 17 for SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')

    conn, cursor = test_con.make_connection() # make connection and get cursor object
    if conn:
        result = test_con.query(cursor, query)
        if result:
            print(result)


    # close connection
    if conn:
        test_con.close_connection(conn)



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
        
    # close connection
    if conn:
        test_conn_postgres.close_connection(conn)


    
def main():
    qry = "select * from testtble"
    sql_server(qry)
    qry = "select * from plc_step_test limit 20"
    postgres(qry)


if __name__ == "__main__":
    main()
    print("Done")