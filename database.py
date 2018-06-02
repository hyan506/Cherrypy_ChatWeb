import sqlite3
import hashlib
import urllib
import urllib2
import json

username = "hyan506"
password = "flightperception"
hashword = hashlib.sha256()
hashword.update(password)
hashword.update(username)
variable = {}
variable['username'] = username
variable['password'] = hashword.hexdigest()
variable['enc'] = 0
variable['json'] = 1
url_values = urllib.urlencode(variable)
url = 'http://cs302.pythonanywhere.com/getList'
url_completed = url + '?' +url_values
feedback = urllib2.urlopen(url_completed).read()




sqlite_file = '302python.db'    # name of the sqlite database file
table_name = 'OnlineUsers'   # name of the table to be created
id_column = 'username' # name of the PRIMARY KEY column
ip_column = 'ip'  # name of the new column
port_column = 'port'  # name of the new column
lastlogin_column = 'lastlogin'  # name of the new column
column_type = 'TEXT' # E.g., INTEGER, TEXT, NULL, REAL, BLOB
# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
sql = 'DELETE FROM OnlineUsers'
c.execute(sql)
data = json.loads(feedback)
for x in range(len(data)):
	username = data[str(x)]['username']
	ip = data[str(x)]['ip']
	lastLogin = data[str(x)]['lastLogin']
	port = data[str(x)]['port']
	location = data[str(x)]['location']
	string = """INSERT OR IGNORE INTO OnlineUsers (username,ip,port,lastlogin) VALUES ("{a}","{b}","{c}","{d}");"""
	command = string.format(a=username,b=ip,c=port,d=lastLogin)
	c.execute(command)
	
c.execute('SELECT ip FROM OnlineUsers WHERE username=?',(username,))
ip=c.fetchone()
print ip[0]

c.execute('SELECT port FROM OnlineUsers WHERE username=?',(username,))
port=c.fetchone()
print port[0]
'''
# A) Adding a new column without a row value
c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
        .format(tn=table_name, cn=new_column1, ct=column_type))
# A) Adding a new column without a row value
c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
        .format(tn=table_name, cn=new_column2, ct=column_type))
# A) Adding a new column without a row value
c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
        .format(tn=table_name, cn=new_column3, ct=column_type))
'''
# Committing changes and closing the connection to the database file
conn.commit()
conn.close()