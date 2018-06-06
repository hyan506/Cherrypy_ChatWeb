#!/usr/bin/python
""" cherrypy_example.py

	COMPSYS302 - Software Design
	Author: Steven Yan
	ID:661784348
	UPI:hyan506
	Last Edited: 6/06/2018

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
import threading

import toolbox
import database_toolbox

from jinja2 import Environment, FileSystemLoader		#Set up Jinja2
env = Environment(loader=FileSystemLoader('template'))	#Set up Jinja2

# The address we listen for connections on
listen_ip = '0.0.0.0'
report_ip = socket.gethostbyname(socket.gethostname())	# Use Socket to get the current IP

if '172.23' in report_ip:								#Determine location depends on IP address
    location = '1'
elif '10.103' in report_ip:
    location = '0'
else:
    location = '2'
	
listen_port = 10001										#Port for reporting


global LOGIN											#Global variable to start the Thread
LOGIN = 0
global success
success = ''											
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
	def index(self):									#Return the HTML page for index
		return open('template/Index.html')
	@cherrypy.expose
	def login(self):									#Return the HTML page for login
		return open('template/Login.html')
	@cherrypy.expose
	def logoff(self):									#Return the HTML page for logoff
		return open('template/Logoff.html')
	@cherrypy.expose
	def profile(self,owner):							#Render the HTML page, and then Return the HTML page for profile
		temp = env.get_template('Profile.html')
		username = cherrypy.session.get('username')
		profilelist = database_toolbox.getProfileList(owner) # Get Profile data for profile_owner from the database
		return temp.render(listOfProfile = profilelist,owner = owner,user=username)	#Render and return
	@cherrypy.expose
	def EditProfilePage(self):							#Render the HTML page, and then Return the HTML page for EditProfile
		temp = env.get_template('EditProfile.html')
		username = cherrypy.session.get('username')
		return temp.render(user = username)				#Render the HTML page, and then Return the HTML page for EditProfile
	@cherrypy.expose
	def onlineUsers(self,**kwargs):		#Render and return the Main Page => OnlineUsers. 
		global success
		temp = env.get_template('onlineUsers.html')
		username = cherrypy.session.get('username')
		userlist = database_toolbox.getOnlineUserList()		#Get List of Online Users from the database
		name = kwargs.get('username')
		messagelist = database_toolbox.getMessageList(name) #Get the Message to display in the Message Box
		noticelist = database_toolbox.getNoticeList()		#Get the Notice from the database
		return temp.render(success = success, currentUser = username, receiver = name, listOfUsers = userlist,listOfMessage = messagelist,listOfNotice = noticelist)
	@cherrypy.expose
	def openChatbox(self, username):
		database_toolbox.ClearNoticeOf(username)		#Give a username to the OnlineUsers so it know who are you talking to
		direct = '/onlineUsers?username='+username
		raise cherrypy.HTTPRedirect(direct)				#Raise the page (Call the function with variable built in)
	# PAGES ---------------------------------------End-------------------------------	

	# Login and Logoff ---------------------------------------Start-------------------------------	
	@cherrypy.expose
	def signin(self, username, password):
		#Check if the user entered the correct username and password by communicate with the server
		#if not, stay in login page
		hashword = toolbox.passowrdhash(username,password)	#Hash the password
		error = self.authoriseUserLogin(username,hashword)	#Check with the server and get the feedback
		if (error == 0):
			global LOGIN
			LOGIN = 1
			cherrypy.session['username'] = username
			cherrypy.session['password'] = hashword			#Store the hashed password in session
			database_toolbox.IfHasProfile(username)			#Check if the current user has a profile in local database, if not, make one
			kwargs=dict(username=username,password=hashword)
			self.update(**kwargs)
			raise cherrypy.HTTPRedirect('/onlineUsers')		
		else:
			raise cherrypy.HTTPRedirect('/login')			
	def update(self,**kwargs):
		#Start threads if logged in, Otherwise stop the thread.
		username = kwargs.get('username')
		password = kwargs.get('password')
		global LOGIN
		if(LOGIN == 1):
			keepreporting = cherrypy.process.plugins.BackgroundTask(20, self.getUsers,kwargs=dict(username=username,password=password))
			keepreporting.start()
			keepupdating = cherrypy.process.plugins.BackgroundTask(20, self.authoriseUserLogin,kwargs=dict(username=username,password=password))
			keepupdating.start()
			
		else:
			print str(LOGIN) +"Update not start"
			return
	@cherrypy.expose
	def signout(self,**kwargs):
		#Logs the current user out, expires their session. And stop the thread
		try:
			username = cherrypy.session.get('username')
			password = cherrypy.session.get('password')
		except:
			username = kwargs.get('username')
			password = kwargs.get('password')
			
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
			#database_toolbox.ClearDatabase()
			#keepreporting.cancel()
			#keepupdating.cancel()
			raise cherrypy.HTTPRedirect('/index')
		else:
			raise cherrypy.HTTPRedirect('/logoff')
	# Login and Logoff ---------------------------------------End-------------------------------	
	
	# Get Online Users ---------------------------------------Start-------------------------------
	@cherrypy.expose
	def getUsers(self,username,password):	
		#Get the List of Online users 
		if (password == None or username == None):
			raise cherrypy.HTTPRedirect('/login')
		# Connecting to the database file
		userlist = toolbox.getList(username, password.hexdigest())
		data = json.loads(userlist)
		database_toolbox.OnlineUserDatabase(data)
		print "----------Got the newest list------------"
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
			global success
			if(feedback.read()[0] == '0'):
				success = "success"
			else:
				success = "fail"
		except:
			global success
			success = "fail"
			raise cherrypy.HTTPRedirect('/onlineUsers')
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		database_toolbox.MessageDatabase(currentTime, sender, message,receiver,sender)
		self.openChatbox(receiver)
			
	@cherrypy.expose
	def sendFile(self, receiver, myFile):
		username = cherrypy.session.get('username')
		file64 = base64.b64encode(myFile.file.read())
		ip = database_toolbox.findIp(receiver)
		port = database_toolbox.findPort(receiver)
		content_type = str(mimetypes.guess_type(myFile.filename)[0])
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
		message = "You sent a file : \""+myFile.filename+ "\" "
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		database_toolbox.MessageDatabase(currentTime, username, message,receiver, username)
		self.openChatbox(receiver)
	# Send Message and File ---------------------------------------End-------------------------------
		
		
	# Receive Message and File ---------------------------------------Start-------------------------------
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def receiveMessage(self):
		# Others can send message to this client by calling this api
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		sender = cherrypy.request.json['sender']
		message = cherrypy.request.json['message']
		receiver = cherrypy.request.json['destination']
		message = toolbox.htmlProtect(message)
		database_toolbox.MessageDatabase(currentTime, sender, message,receiver,receiver)
		return '0: <Action was successful>'
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def receiveFile(self):
		# Others can send Files to this client by calling this api
		sender = cherrypy.request.json['sender']
		filename = cherrypy.request.json['filename']
		destination = cherrypy.request.json['destination']
		content_type = cherrypy.request.json['content_type']
		stamp = cherrypy.request.json['stamp']
		time = datetime.datetime.fromtimestamp(
		int(stamp)
		).strftime('%Y-%m-%d %H:%M:%S')
		receiver = cherrypy.request.json['destination']
		message = "Sent a file \""+filename+ "\" to you"
		database_toolbox.ReceiveFileDatabase(time, sender, filename, content_type, message,receiver)
		file = cherrypy.request.json['file']
		data = base64.b64decode(file)
		f = open("files/"+filename, 'wb')
		f.write(data)
		f.close()
		print "Message received from "+sender
		return '0: <Action was successful>'	
	# Receive Message and File ---------------------------------------End-------------------------------
	
	# Profile------------------------------------Start-----------------------------
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def getProfile(self):
		# Others can Get anybodys profiles from this client's local database by calling this api
		username = cherrypy.request.json['profile_username']
		list = database_toolbox.getProfileList(username)
		profile = json.dumps(list)
		print profile
		return profile
	@cherrypy.expose
	def editProfile(self,fullname='Fullname Not Set', position='Position Not Set', description='Description Not Set', location='Location Not Set', picture='Picture Not Set'):
        #This function allows the current user to edit their local profile
		username = cherrypy.session.get('username')
		database_toolbox.editProfile(fullname, position, description, location, picture, username)
		raise cherrypy.HTTPRedirect('/profile?owner='+username)
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def askForProfile(self,profileOwner):
		#This function allows the current user to ask for others profile by calling their getProfile API
		sender = cherrypy.session.get('username')
		if (sender == None):
			raise cherrypy.HTTPRedirect('/login')
		if (profileOwner == 'None'):
			raise cherrypy.HTTPRedirect('/onlineUsers')
		ip = database_toolbox.findIp(profileOwner)
		port = database_toolbox.findPort(profileOwner)
		variable = {}
		variable['sender'] = sender
		variable['profile_username'] = profileOwner
		data = json.dumps(variable) 
		url = 'http://' + str(ip) + ':' + str(port) + '/getProfile'
		req = urllib2.Request(url,data,{'Content-Type':'application/json'})
		database_toolbox.IfHasProfile(profileOwner)
		try:
			feedback = urllib2.urlopen(req)
			print "-Responded--Responded--Responded--Responded--Responded--Responded--Responded-"
			profile = json.loads(feedback.read())
			try:
				fullname = profile['fullname']
			except:
				fullname = ''
			try:
				position = profile['position']
			except:
				position = ''
			try:
				description = profile['description']
			except:
				description = ''
			try:
				location = profile['location']
			except:
				location = ''
			try:
				picture = profile['picture']
			except:
				picture = ''
			database_toolbox.editProfile(fullname, position, description, location, picture, profileOwner)
			print "adsngiasngaskfgnrojgnaeiognaerohgaegawgasdfjgndgneraoginargaiorwgnadfsjhanr"
			raise cherrypy.HTTPRedirect('/profile?owner='+profileOwner)
		except:
			print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
			raise cherrypy.HTTPRedirect('/profile?owner='+profileOwner)
			
		
	# Profile------------------------------------End-------------------------------
	def authoriseUserLogin(self, username, password):
		#This function allows user to communicate with the server to check if the password is correct
		print "Starting-------------"
		if(username == '' or password == ''):
			return 1
		variable = {}
		variable['username'] = username
		variable['password'] = password.hexdigest()
		variable['location'] = location
		variable['ip']       = report_ip
		variable['port']      = listen_port
		url_values = urllib.urlencode(variable)
		url = 'http://cs302.pythonanywhere.com/report'
		url_completed = url + '?' +url_values
		print "Reporting-------------"
		res= urllib2.urlopen(url_completed).read()
		print res
		if (res == "0, User and IP logged"):
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
