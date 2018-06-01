
import hashlib
import urllib
import urllib2
import json
import socket

listen_ip = socket.gethostbyname(socket.gethostname())
print listen_ip
if '172.23' in listen_ip:
    location = '1'
elif '10.103' in listen_ip:
    location = '0'
else:
    location = '2'
	
listen_port = 10001

username = "hyan506"
password = "flightperception"
hashword = hashlib.sha256()
hashword.update(password)
hashword.update(username)
variable = {}
variable['username'] = username
variable['password'] = hashword.hexdigest()
variable['enc'] = 0
variable['json'] = 0
url_values = urllib.urlencode(variable)
url = 'http://cs302.pythonanywhere.com/getList'
url_completed = url + '?' +url_values
feedback = urllib2.urlopen(url_completed).read()
print feedback

		
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
