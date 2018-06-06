import sqlite3
import time
import datetime
def OnlineUserDatabase(data):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	clear = 'DELETE FROM OnlineUsers'
	c.execute(clear)
	for x in range(len(data)):
		username = data[str(x)]['username']
		ip = data[str(x)]['ip']
		port = data[str(x)]['port']
		location = data[str(x)]['location']
		lastLogin = datetime.datetime.fromtimestamp(
		int(data[str(x)]['lastLogin'])
		).strftime('%Y-%m-%d %H:%M:%S')
		c.execute('INSERT INTO OnlineUsers VALUES(?, ?, ?, ?, ?)',
		(username, ip, location, port, lastLogin))
	conn.commit()
	conn.close()

def MessageDatabase(currentTime, sender, message, receicer):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('INSERT INTO Message VALUES(?, ?, ?, ?)',
	(currentTime, sender, message, receicer))
	c.execute('INSERT INTO Notice VALUES(?, ?)',
	(sender,"message"))
	conn.commit()
	conn.close()

def ReceiveFileDatabase(time, sender, filename, content_type, message, receicer):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('INSERT INTO FileReceived VALUES(?, ?, ?, ?)',
	(time, sender, filename, content_type))
	
	c.execute('INSERT INTO Message VALUES(?, ?, ?, ?)',
	(time, sender, message, receicer))
	
	c.execute('INSERT INTO Notice VALUES(?, ?)',
	(sender,"File"))
	conn.commit()
	conn.close()
	
def ClearDatabase():
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	clear = 'DELETE FROM OnlineUsers'
	c.execute(clear)
	clear = 'DELETE FROM FileReceived'
	c.execute(clear)
	clear = 'DELETE FROM Message'
	c.execute(clear)
	conn.commit()
	conn.close()

def ClearNoticeOf(username):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('DELETE FROM Notice WHERE source=?',(username,))
	print "-----deleted Notice From------" + username
	conn.commit()
	conn.close()
	
def IfHasProfile(username):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("SELECT 1 FROM Profile WHERE EXISTS (SELECT username FROM Profile WHERE username=?)",(username,))
	if c.fetchone():
		print("Found!")
	else:
		print("Not found...")
		stamp = time.time()
		c.execute('INSERT INTO Profile VALUES(?,?,?,?,?,?,?)',
		(username,'Fullname Not Set','Description Not Set','Location Not Set','Picture Not Set','Position Not Set',stamp))
	conn.commit()
	conn.close()
def getProfileList(username):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("SELECT fullname,position,description,location,picture,lastUpdated FROM Profile WHERE username=?",(username,))
	variablelist={}
	list = []
	for row in c.fetchone():
		print row
		list.append(row)
	variablelist['fullname'] = list[0]
	variablelist['position'] = list[1]
	variablelist['description'] = list[2]
	variablelist['location'] = list[3]
	variablelist['picture'] = list[4]
	variablelist['lastUpdated'] = list[5] 
	conn.commit()
	conn.close()
	return variablelist
def editProfile(fullname, position, description, location, picture, username):
	conn = sqlite3.connect('302python.db')
	if(fullname == ''):fullname ='Fullname Not Set'
	if(position == ''):position ='Position Not Set'
	if(description == ''):description ='Description Not Set'
	if(location == ''):location ='Location Not Set'
	if(picture == ''):picture ='Picture Not Set'
	stamp = time.time()
	c = conn.cursor()
	c.execute('UPDATE profile SET fullname = ?, position = ?, description = ?, location = ?, picture = ?,lastUpdated = ? WHERE username = ?', (fullname, position, description, location, picture, stamp, username))
	conn.commit()
	conn.close()
def findIp(username):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('SELECT ip FROM OnlineUsers WHERE username=?',(username,))
	ip=c.fetchone()
	return ip[0]
	
def findPort(username):
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('SELECT port FROM OnlineUsers WHERE username=?',(username,))
	port=c.fetchone()
	return port[0]