import MySQLdb

mysql_connection = MySQLdb.connect(host="localhost", user="root", passwd="admin")
cur = mysql_connection.cursor()
cur.execute("CREATE DATABASE monitor;")

cur = mysql_connection.cursor()
cur.execute("USE monitor;")
sql = """
CREATE TABLE profiles (
id INT NOT NULL AUTO_INCREMENT,
name VARCHAR(100) NOT NULL,
project_name VARCHAR(100) NOT NULL,
cpu_util_avg DOUBLE(11, 10) NULL,
samples_count DECIMAL(65,0) NULL,
memory_usage_avg INT NULL,
last_updated timestamp NULL DEFAULT 0,
PRIMARY KEY (id)) ENGINE=INNODB;
"""
cur.execute(sql)

sql = """
CREATE TABLE servers (
id VARCHAR(100) NOT NULL,
profile_id INT NULL,
PRIMARY KEY(id),
FOREIGN KEY(profile_id) REFERENCES profiles(id)) ENGINE=INNODB;
"""
cur.execute(sql)

