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
import datetime
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('template'))

# The address we listen for connections on
listen_ip = socket.gethostbyname(socket.gethostname())

if '172.23' in listen_ip:
    location = '1'
elif '10.103' in listen_ip:
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

	# PAGES (which return HTML that can be viewed in browser)
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
	def onlineUsers(self):
		temp = env.get_template('onlineUsers.html')
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		c.execute("select username, ip, location, lastlogin from OnlineUsers")
		list=[]
		for row in c.fetchall():
			list.append(row)
		#print list
		return temp.render(listOfUsers = list)
		
	@cherrypy.expose
	def ping(self, sender):
		# This API allows other users to check is the client is still there
		print "--PING----PING----PING----PING----PING----PING----PING----PING----PING----PING--"
		print "You just pinged by " + sender
		return '0'

	# LOGGING IN AND OUT
	@cherrypy.expose
	def signin(self, username, password):
		"""Check their name and password and send them either to the main page, or back to the main login screen."""
		error = self.authoriseUserLogin(username,password)
		if (error == 0):
			cherrypy.session['username'] = username
			cherrypy.session['password'] = password
			raise cherrypy.HTTPRedirect('/getUsers')
		else:
			raise cherrypy.HTTPRedirect('/login')

	@cherrypy.expose
	def signout(self):
		"""Logs the current user out, expires their session"""
		username = cherrypy.session.get('username')
		password = cherrypy.session.get('password')
		hashword = hashlib.sha256()
		hashword.update(password)
		hashword.update(username)
		variable = {}
		variable['username'] = username
		variable['password'] = hashword.hexdigest()
		variable['enc'] = 0
		url_values = urllib.urlencode(variable)
		url = 'http://cs302.pythonanywhere.com/logoff'
		url_completed = url + '?' +url_values
		feedback = urllib2.urlopen(url_completed).read()
		if (feedback == "0, Logged off successfully"):
			cherrypy.lib.sessions.expire()
			raise cherrypy.HTTPRedirect('/index')
		else:
			raise cherrypy.HTTPRedirect('/logoff')
			
	@cherrypy.expose
	def getUsers(self):	
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		username = cherrypy.session.get('username')
		password = cherrypy.session.get('password')
		if (password == None):
			raise cherrypy.HTTPRedirect('/login')
		# Connecting to the database file
		clear = 'DELETE FROM OnlineUsers'
		c.execute(clear)
		userlist = self.getList(username, password)
		data = json.loads(userlist)
		for x in range(len(data)):
			username = data[str(x)]['username']
			ip = data[str(x)]['ip']
			port = data[str(x)]['port']
			location = data[str(x)]['location']
			lastLogin = datetime.datetime.fromtimestamp(
				int(data[str(x)]['lastLogin'])
			).strftime('%Y-%m-%d %H:%M:%S')
			string = """INSERT OR IGNORE INTO OnlineUsers (username,ip,port,location,lastlogin) VALUES ("{a}","{b}","{c}","{d}","{e}");"""
			command = string.format(a=username,b=ip,c=port,d=location,e=lastLogin)
			c.execute(command)
		conn.commit()
		conn.close()
		raise cherrypy.HTTPRedirect('/onlineUsers')
		
	@cherrypy.expose
	def getList(self, username, password):
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
		return feedback
		
	@cherrypy.expose
	def sendMessage(self, receiver, message):
		"""Call receiveMessage on the receiver's side"""
		sender = cherrypy.session.get('username')
		ip = self.findIp(receiver)
		port = self.findPort(receiver)
		variable = {}
		variable['sender'] = sender
		variable['destination'] = receiver
		variable['message'] = message
		stamp = time.time()
		variable['stamp'] = stamp
		data = json.dumps(variable) 
		url = 'http://' + str(ip) + ':' + str(port) + '/receiveMessage'
		req = urllib2.Request(url,data,{'Content-Type':'application/json'})
		feedback = urllib2.urlopen(req)
		return '0, action success'
	@cherrypy.expose
	@cherrypy.tools.json_in()
	def receiveMessage(self):
		# This API allows other users to send messages to this client
		currentTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(time.mktime(time.localtime()))))
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		sender = cherrypy.request.json['sender']
		message = cherrypy.request.json['message']
		c.execute('INSERT INTO MessageReceived VALUES(?, ?, ?)', (currentTime, sender, message))
		conn.commit()
		conn.close()
		print message
		print "Message received from "+sender
		return '0: <Action was successful> '
		
	def findIp(self,username):
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		c.execute('SELECT ip FROM OnlineUsers WHERE username=?',(username,))
		ip=c.fetchone()
		return ip[0]
		
	def findPort(self,username):
		conn = sqlite3.connect('302python.db')
		c = conn.cursor()
		c.execute('SELECT port FROM OnlineUsers WHERE username=?',(username,))
		port=c.fetchone()
		return port[0]
		
	def authoriseUserLogin(self, username, password):
		if(username == '' or password == ''):
			return 1
		hashword = hashlib.sha256()
		hashword.update(password)
		hashword.update(username)
		variable = {}
		variable['username'] = username
		variable['password'] = hashword.hexdigest()
		variable['location'] = location
		variable['ip']       = listen_ip
		variable['port']      = listen_port
		url_values = urllib.urlencode(variable)
		url = 'http://cs302.pythonanywhere.com/report'
		url_completed = url + '?' +url_values
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
