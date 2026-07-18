"""Setup BottleCRM: create Org via session auth."""
import urllib.request, http.cookiejar, re, json, ssl

base = 'https://bottlecrm.onrender.com'
ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler(context=ctx)
)

# Login
r = opener.open(base + '/admin/login/')
csrf = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', r.read().decode()).group(1)
data = urllib.parse.urlencode({'username':'admin@bottlecrm.com','password':'admin','csrfmiddlewaretoken':csrf,'next':'/admin/'}).encode()
req = urllib.request.Request(base + '/admin/login/', data=data, headers={'Referer':base+'/admin/login/','Content-Type':'application/x-www-form-urlencoded'})
r = opener.open(req)
print(f'Login: {r.getcode()} -> {r.url}')

# Try org creation
csrf = next((c.value for c in cj if c.name == 'csrftoken'), '')
org_data = json.dumps({'name':'AllShopTotal','email':'contato@allshoptotal.com'}).encode()
req = urllib.request.Request(base + '/api/common/org/', data=org_data,
    headers={'Content-Type':'application/json','X-CSRFToken':csrf,'Referer':base+'/admin/'})
try:
    r = opener.open(req)
    print(f'Org: {r.getcode()}')
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'Org failed: {e.code}')
    print(body[:500])