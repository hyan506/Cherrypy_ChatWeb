import hashlib


def passowrdhash(username, password):
	hashword = hashlib.sha256()
	hashword.update(password)
	hashword.update(username)
	return hashword
def function(name = ''):
	print "Yo what up " + name +'!!'