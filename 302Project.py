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
		return open('Index.html')
	@cherrypy.expose
	def login(self):
		return open('Login.html')
	@cherrypy.expose
	def logoff(self):
		return open('Logoff.html')
	@cherrypy.expose
	def onlineUsers(self):
		return open('onlineUsers.html')
	
	@cherrypy.expose
	def ping(self, sender):
		# This API allows other users to check is the client is still there
		errorCode = 0
		return str(errorCode)

	# LOGGING IN AND OUT
	@cherrypy.expose
	def signin(self, username, password):
		"""Check their name and password and send them either to the main page, or back to the main login screen."""
		error = self.authoriseUserLogin(username,password)
		if (error == 0):
			cherrypy.session['username'] = username
			cherrypy.session['password'] = password
			raise cherrypy.HTTPRedirect('/onlineUsers')
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
		# Connecting to the database file
		clear = 'DELETE FROM OnlineUsers'
		c.execute(clear)
		userlist = self.getList(username, password)
		data = json.loads(userlist)
		for x in range(len(data)):
			username = data[str(x)]['username']
			ip = data[str(x)]['ip']
			lastLogin = data[str(x)]['lastLogin']
			port = data[str(x)]['port']
			string = """INSERT OR IGNORE INTO OnlineUsers (username,ip,port,lastlogin) VALUES ("{a}","{b}","{c}","{d}");"""
			command = string.format(a=username,b=ip,c=port,d=lastLogin)
			c.execute(command)
		conn.commit()
		conn.close()
		raise cherrypy.HTTPRedirect('/')
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
