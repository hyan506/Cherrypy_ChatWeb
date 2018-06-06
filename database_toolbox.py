import sqlite3
import time
import datetime
import toolbox
def OnlineUserDatabase(data):				#Write Data into OnlineUser table in database
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

def MessageDatabase(currentTime, sender, message, receicer,currentUser):#Write Data into Message table in database
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('INSERT INTO Message VALUES(?, ?, ?, ?)',
	(currentTime, sender, message, receicer))
	if(sender != currentUser):
		c.execute('INSERT INTO Notice VALUES(?, ?)',
		(sender,"message"))
	conn.commit()
	conn.close()

def ReceiveFileDatabase(time, sender, filename, content_type, message, receicer):#Write Data into ReceiveFile table in database
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
	
def ClearDatabase():								#Clear the message,OnlineUsers and FileReceived Table
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

def ClearNoticeOf(username):						#Clear the Notices came from one user
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('DELETE FROM Notice WHERE source=?',(username,))
	print "-----deleted Notice From------" + username
	conn.commit()
	conn.close()
	
def IfHasProfile(username):							#Check if the a user have a profile locally, if not, make an empty one
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("SELECT 1 FROM Profile WHERE EXISTS (SELECT username FROM Profile WHERE username=?)",(username,))
	if c.fetchone():
		print("Found! This guy's profile is in the database")
	else:
		print("Not found...Creating a new empty profile for this guy")
		stamp = time.time()
		c.execute('INSERT INTO Profile VALUES(?,?,?,?,?,?,?)',
		(username,'Fullname Not Set','Description Not Set','Location Not Set','Picture Not Set','Position Not Set',stamp))
	conn.commit()
	conn.close()
def getProfileList(username):					#Make the local profile into a list
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
def getOnlineUserList():		#Make the OnlineUser table into a list
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("select username, ip, location, lastlogin from OnlineUsers")
	userlist=[]
	for row in c.fetchall():
		userlist.append(row)
	return userlist
def getMessageList(name=None):	#Make the Message table into a list
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("SELECT time,sender,message FROM Message WHERE sender=? or receiver=?",(name,name))
	messagelist=[]
	for row in c.fetchall():
		messagelist.append(row)
		
	return messagelist
def getNoticeList():			#Make the List table into a list
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute("SELECT source,type FROM Notice")
	noticelist=[]
	for row in c.fetchall():
		noticelist.append(row)
	return noticelist
def editProfile(fullname, position, description, location, picture, username): #Edit someone's profile locally
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
def findIp(username):				#Find someone's IP address from the OnlineUser Table
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('SELECT ip FROM OnlineUsers WHERE username=?',(username,))
	ip=c.fetchone()
	try:
		return ip[0]
	except:
		return "0.0.0.0"
	
def findPort(username):				#Find someone's Port from the OnlineUser Table
	conn = sqlite3.connect('302python.db')
	c = conn.cursor()
	c.execute('SELECT port FROM OnlineUsers WHERE username=?',(username,))
	try:
		port=c.fetchone()
		return port[0]
	except:
		return "0"