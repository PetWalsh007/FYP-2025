# Main file for the abstraction layer
# This file is responsible for the abstraction layer of the database

# Here we take the paramters passed from inside the system and setup the end points for the database

from connections import *

test_con = connectcls_sql_server('SQL Server', '192.168.1.50', 'Test_db01', 'sa', '01-SQL-DEV-01')

print(test_con.connect_str())

conn, cursor = test_con.make_connection()

query = "select * from testtable"

result = test_con.query(conn, cursor, query)

print(result)



