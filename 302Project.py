#!/usr/bin/python
""" cherrypy_example.py

	COMPSYS302 - Software Design
	Author: Andrew Chen (andrew.chen@auckland.ac.nz)
	Last Edited: 19/02/2018

	This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)
import cherrypy
import hashlib
import urllib
import urllib2
import json
import socket
import sqlite3
import time
import mimetypes
import datetime
import os, base64


import toolbox
import database_toolbox
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('template'))

# The address we listen for connections on
listen_ip = "0.0.0.0"
report_ip = socket.gethostbyname(socket.gethostname())
print report_ip
print report_ip
if '172.23' in report_ip:
    location = '1'
elif '10.103' in report_ip:
    location = '0'
else:
    location = '2'
	
listen_port = 10001




class MainApp(object):

	#CherryPy Configuration
	_cp_config = {'tools.encode.on': True,
				  'tools.encode.encoding': 'utf-8',
				  'tools.sessions.on' : 'True',
				 }

	# If they try somewhere we don't know, catch it here and send them to the right place.
	@cherrypy.expose
	def default(self, *args, **kwargs):
		"""The default page, given when we don't recognise where the request is for."""
		Page = "I don't know where you're trying to go, so have a 404 Error."
		cherrypy.response.status = 404
		return Page

	# PAGES ---------------------------------------Start-------------------------------
	@cherrypy.expose
	def index(self):
		return open('template/Index.html')
	@cherrypy.expose
	def login(self):
		return open('template/Login.html')
	@cherrypy.expose
	def logoff(self):
		return open('template/Logoff.html')
	@cherrypy.expose
	def profile(self):
		temp = env.get_template('Profile.html')
		username = cherrypy.session.get('username')
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		c.execute("select fullname,position,description,location,picture from Profile WHERE username=?",(username,))
		profilelist={}
		list=[]
		for row in c.fetchone():
			list.append(row)
		profilelist['fullname'] = list[0]
		profilelist['position'] = list[1]
		profilelist['description'] = list[2]
		profilelist['location'] = list[3]
		profilelist['picture'] = list[4]
		print profilelist
		return temp.render(listOfProfile = profilelist)
	@cherrypy.expose
	def EditProfilePage(self):
		return open('template/EditProfile.html')
	@cherrypy.expose
	def onlineUsers(self,**kwargs):
		temp = env.get_template('onlineUsers.html')
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		c.execute("select username, ip, location, lastlogin from OnlineUsers")
		userlist=[]
		for row in c.fetchall():
			userlist.append(row)
		name = kwargs.get('username')
		c.execute("SELECT time,sender,message FROM Message WHERE sender=? or receiver=?",(name,name))
		messagelist=[]
		for row in c.fetchall():
			messagelist.append(row)
		
		return temp.render(listOfUsers = userlist, receiver = name,listOfMessage = messagelist)
	@cherrypy.expose
	def openChatbox(self, username):
		direct = '/onlineUsers?username='+username
		raise cherrypy.HTTPRedirect(direct)
	# PAGES ---------------------------------------End-------------------------------	

	# Login and Logoff ---------------------------------------Start-------------------------------	
	@cherrypy.expose
	def signin(self, username, password):
		"""Check their name and password and send them either to the main page, or back to the main login screen."""
		hashword = toolbox.passowrdhash(username,password)
		error = self.authoriseUserLogin(username,hashword)
		if (error == 0):
			cherrypy.session['username'] = username
			cherrypy.session['password'] = hashword
			database_toolbox.IfHasProfile(username)
			raise cherrypy.HTTPRedirect('/getUsers')
		else:
			raise cherrypy.HTTPRedirect('/login')

	@cherrypy.expose
	def signout(self):
		"""Logs the current user out, expires their session"""
		username = cherrypy.session.get('username')
		password = cherrypy.session.get('password')
		variable = {}
		variable['username'] = username
		variable['password'] = password.hexdigest()
		variable['enc'] = 0
		url_values = urllib.urlencode(variable)
		url = 'http://cs302.pythonanywhere.com/logoff'
		url_completed = url + '?' +url_values
		feedback = urllib2.urlopen(url_completed).read()
		if (feedback == "0, Logged off successfully"):
			cherrypy.lib.sessions.expire()
			database_toolbox.ClearDatabase()
			raise cherrypy.HTTPRedirect('/index')
		else:
			raise cherrypy.HTTPRedirect('/logoff')
	# Login and Logoff ---------------------------------------End-------------------------------	
	
	# Get Online Users ---------------------------------------Start-------------------------------
	@cherrypy.expose
	def getUsers(self):	
		username = cherrypy.session.get('username')
		password = cherrypy.session.get('password')
		if (password == None or username == None):
			raise cherrypy.HTTPRedirect('/login')
		# Connecting to the database file
		userlist = toolbox.getList(username, password)
		data = json.loads(userlist)
		database_toolbox.OnlineUserDatabase(data)
		raise cherrypy.HTTPRedirect('/onlineUsers')
	# Get Online Users ---------------------------------------End-------------------------------

	# Ping ---------------------------------------Start-------------------------------	
	@cherrypy.expose
	def ping(self, sender):
		# This API allows other users to check is the client is still there
		print "--PING----PING----PING----PING----PING----PING----PING----PING----PING----PING--"
		print "You just pinged by " + sender
		return '0'
	# Ping ---------------------------------------End-------------------------------

	# Send Message and File ---------------------------------------Start-------------------------------

	@cherrypy.expose
	def sendMessage(self, receiver = '', message = ''):
		"""Call receiveMessage on the receiver's side"""
		sender = cherrypy.session.get('username')
		if (sender == None):
			raise cherrypy.HTTPRedirect('/login')
		if (receiver == 'None' or message == ''):
			raise cherrypy.HTTPRedirect('/onlineUsers')
		ip = database_toolbox.findIp(receiver)
		port = database_toolbox.findPort(receiver)
		variable = {}
		variable['sender'] = sender
		variable['destination'] = receiver
		variable['message'] = message
		stamp = time.time()
		variable['stamp'] = stamp
		data = json.dumps(variable) 
		url = 'http://' + str(ip) + ':' + str(port) + '/receiveMessage'
		req = urllib2.Request(url,data,{'Content-Type':'application/json'})
		try:
			feedback = urllib2.urlopen(req)
		except:
			raise cherrypy.HTTPRedirect('/onlineUsers')
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		database_toolbox.MessageDatabase(currentTime, sender, message,receiver)
		self.openChatbox(receiver)
			
	@cherrypy.expose
	def sendFile(self, receiver, myFile):
		username = cherrypy.session.get('username')
		print "++++++++++++sending file to " + receiver + "++++++++++++++++++"
		file64 = base64.b64encode(myFile.file.read())
		ip = database_toolbox.findIp(receiver)
		port = database_toolbox.findPort(receiver)
		content_type = str(mimetypes.guess_type(myFile.filename)[0])
		print "ContentType is " + content_type
		print "FileName is " + myFile.filename
		variable = {}
		variable['sender'] = username
		variable['destination'] = receiver
		variable['file'] = file64
		variable['filename'] = myFile.filename
		variable['content_type'] = content_type
		stamp = time.time()
		variable['stamp'] = stamp
		url = 'http://' + str(ip) + ':' + str(port) + '/receiveFile'
		data = json.dumps(variable)
		req = urllib2.Request(url,data,{'Content-Type':'application/json'})
		feedback = urllib2.urlopen(req)
		print feedback
		message = "You sent a file : \""+myFile.filename+ "\" "
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		database_toolbox.MessageDatabase(currentTime, username, message,receiver)
		self.openChatbox(receiver)
	# Send Message and File ---------------------------------------End-------------------------------
		
		
	# Receive Message and File ---------------------------------------Start-------------------------------
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def receiveMessage(self):
		# This API allows other users to send messages to this client
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		sender = cherrypy.request.json['sender']
		message = cherrypy.request.json['message']
		receiver = cherrypy.request.json['destination']
		database_toolbox.MessageDatabase(currentTime, sender, message,receiver)
		print message
		print "Message received from "+sender
		return '0: <Action was successful>'
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def receiveFile(self):
		sender = cherrypy.request.json['sender']
		filename = cherrypy.request.json['filename']
		destination = cherrypy.request.json['destination']
		content_type = cherrypy.request.json['content_type']
		stamp = cherrypy.request.json['stamp']
		time = datetime.datetime.fromtimestamp(
		int(stamp)
		).strftime('%Y-%m-%d %H:%M:%S')
		receiver = cherrypy.request.json['destination']
		database_toolbox.ReceiveFileDatabase(time, sender, filename, content_type)
		message = "Sent a file \""+filename+ "\" to you"
		database_toolbox.MessageDatabase(time, sender, message,receiver)
		file = cherrypy.request.json['file']
		data = base64.b64decode(file)
		f = open(filename, 'wb')
		f.write(data)
		f.close()
		print "Message received from "+sender
		return '0: <Action was successful>'	
	# Receive Message and File ---------------------------------------End-------------------------------
	
	# Profile------------------------------------Start-----------------------------
	@cherrypy.expose
	def getProfile(self):
		username = cherrypy.session.get('username')
		list = database_toolbox.getProfileList(username)
		'''variable = {}
		variable['fullname'] = "Steven Yan"
		variable['position'] = "Shooting Guard / Small Forward"
		variable['description'] = "This is a Basketball Player"
		variable['location'] = "China"
		variable['picture'] = "https://pbs.twimg.com/media/DOsuNmmW4AEQPmg.jpg"
		'''
		profile = json.dumps(list)
		print profile
		return profile
	@cherrypy.expose
	def editProfile(self,fullname='Fullname Not Set', position='Position Not Set', description='Description Not Set', location='Location Not Set', picture='Picture Not Set'):
        #This action allows users to change their profile page.
		username = cherrypy.session.get('username')
		database_toolbox.editProfile(fullname, position, description, location, picture, username)
		raise cherrypy.HTTPRedirect('/profile')
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def askForProfile(self,profileOwner):
		return profileOwner
	# Profile------------------------------------End-------------------------------
	def authoriseUserLogin(self, username, password):
		if(username == '' or password == ''):
			return 1
		variable = {}
		variable['username'] = username
		variable['password'] = password.hexdigest()
		variable['location'] = location
		variable['ip']       = '172.23.153.95'
		variable['port']      = listen_port
		url_values = urllib.urlencode(variable)
		url = 'http://cs302.pythonanywhere.com/report'
		url_completed = url + '?' +url_values
		print url_completed
		feedback= urllib2.urlopen(url_completed).read()
		print feedback
		if (feedback == "0, User and IP logged"):
			return 0
		else:
			return 1

def runMainApp():
	# Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
	cherrypy.tree.mount(MainApp(), "/")

	# Tell Cherrypy to listen for connections on the configured address and port.
	cherrypy.config.update({'server.socket_host': listen_ip,
							'server.socket_port': listen_port,
							'engine.autoreload.on': True,
						   })

	print "========================="
	print "University of Auckland"
	print "COMPSYS302 - Software Design Application"
	print "========================================"

	# Start the web server
	cherrypy.engine.start()

	# And stop doing anything else. Let the web server take over.
	cherrypy.engine.block()
 
#Run the function to start everything
runMainApp()
