import urllib
f = urllib.urlopen("http://cs302.pythonanywhere.com/report?username=hyan506&password=9696751B9069D7FB53A12F5500DB71B427E9898C10AC713F18A027ED434B7E96&location=1&ip=172.23.153.95&port=10010&enc=0")
print f.read()