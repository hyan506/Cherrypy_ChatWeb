
import hashlib
import urllib
import urllib2
import json
import socket

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
print feedback