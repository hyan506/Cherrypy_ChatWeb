import hashlib
import urllib
import urllib2
def getList(username, password):
	#Communicate with the server and ask for Online User List
	variable = {}
	variable['username'] = username
	variable['password'] = password
	variable['enc'] = 0
	variable['json'] = 1
	url_values = urllib.urlencode(variable)
	url = 'http://cs302.pythonanywhere.com/getList'
	url_completed = url + '?' +url_values
	feedback = urllib2.urlopen(url_completed).read()
	return feedback
def passowrdhash(username, password):
	#Hash the password with username as salt
	hashword = hashlib.sha256()
	hashword.update(password)
	hashword.update(username)
	return hashword
def htmlProtect(message):
	#protect the html file by replacing <>
	frontRemove=message.replace("<","&lt;")
	backRemove=frontRemove.replace(">","&gt;")
	return backRemove