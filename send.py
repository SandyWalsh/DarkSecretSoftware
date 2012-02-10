import json
import urllib
import urllib2

url = 'http://darksecretsoftware.com/stacktach/data/'

values = {'first': [1,2,3], 'second': dict(a=1, b=2), 'third': (1,2,3)}
jvalues = json.dumps(values)

raw_data = dict(args=jvalues)
cooked_data = urllib.urlencode(raw_data)
req = urllib2.Request(url, cooked_data)
response = urllib2.urlopen(req)
page = response.read()

print page


