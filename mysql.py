import MySQLdb
mysql_connection = MySQLdb.connect(host="localhost", user="root", passwd="admin", db="monitor")
cur = mysql_connection.cursor(MySQLdb.cursors.DictCursor)

def commit():
    mysql_connection.commit()

#def execute(sql, values=None):
    #cur.execute(sql, values)
