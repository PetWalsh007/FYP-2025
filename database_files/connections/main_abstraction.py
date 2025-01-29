# Main file for the abstraction layer
# This file is responsible for the abstraction layer of the database connections and queries

# Here we will take the paramters passed from inside the system and setup the end points for the database

from connections import *



def sql_server():

    # test sql server connection


    test_con = connectcls_sql_server('SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')
    print(test_con) # test __str__ method
    print(test_con.connect_str())

    conn, cursor = test_con.make_connection() # make connection and get cursor object
    qry = "select * from testtable" # test query
    result = test_con.query(cursor, qry)

    print(result)

    # close connection
    test_con.close_connection(conn)




def postgres():

    # test postgres connection
    test_conn_postgres = connectcls_postgres(
        driver_name="PostgreSQL Unicode",
        server_name="192.168.1.55",
        db_name="Test_DB",
        connection_username="test_user",
        connection_password="test_user"
    )

    conn, cursor = test_conn_postgres.make_connection() # make connection and get cursor object


    
    qry = "select * from plc_step_test limit 20"
    result = test_conn_postgres.query(cursor, qry)

    print(result)

    # close connection
    test_conn_postgres.close_connection(conn)



    
def main():

    sql_server()
    #postgres()


if __name__ == "__main__":
    main()