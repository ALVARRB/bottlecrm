"""Login to AllShopTotal CRM admin, create org, profile, and PAT via session auth."""
import urllib.request, urllib.parse, http.cookiejar, re, json, sys

base = 'https://allshoptotal.onrender.com'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler()
)

def get_csrf():
    for c in cj:
        if c.name == 'csrftoken':
            return c.value
    return None

# Step 1: Get login page (sets CSRF cookie)
resp = opener.open(base + '/admin/login/')
html = resp.read().decode()
csrf = get_csrf()
print(f"Step 1: CSRF cookie={csrf}")

# Step 2: Login with CSRF from cookie
data = urllib.parse.urlencode({
    'username': 'admin@allshoptotal.com.br',
    'password': 'admin',
    'csrfmiddlewaretoken': csrf,
    'next': '/admin/'
}).encode()

req = urllib.request.Request(
    base + '/admin/login/',
    data=data,
    headers={
        'Referer': base + '/admin/login/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
)
resp = opener.open(req)
print(f"Step 2: Login status={resp.getcode()}, url={resp.url}")

if '/admin/login/' in resp.url:
    print("Login failed!")
    sys.exit(1)
print("Login successful!")
csrf = get_csrf()
print(f"Session CSRF: {csrf}")

# Step 3: Check admin pages
for path in ['/admin/common/profile/', '/admin/common/org/',
             '/admin/common/personalaccesstoken/']:
    try:
        resp = opener.open(base + path)
        html = resp.read().decode()
        title = re.search(r'<title>([^<]+)</title>', html)
        if 'Page not found' in html or '404' in html:
            print(f'{path} -> 404 NOT FOUND')
        else:
            print(f'{path} -> {title.group(1) if title else "OK"}')
    except Exception as e:
        print(f'{path} -> ERROR: {e}')

# Step 4: Try creating org via API with session auth
print("\n--- Trying to create Org via API ---")
org_data = json.dumps({
    'name': 'AllShopTotal',
    'email': 'contato@allshoptotal.com',
    'website': 'https://allshoptotal.com',
    'address': 'Foz do Iguaçu, PR',
}).encode()

req = urllib.request.Request(
    base + '/api/common/org/',
    data=org_data,
    headers={
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
        'Referer': base + '/admin/',
    }
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read().decode())
    print(f"Org created! status={resp.getcode()}")
    print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Org create failed: {e.code}")
    print(body[:500])

# Step 5: Try browseable API (GET)
print("\n--- Trying GET /api/common/org/ ---")
try:
    resp = opener.open(base + '/api/common/org/')
    print(f"GET status={resp.getcode()}")
    print(resp.read().decode()[:500])
except urllib.error.HTTPError as e:
    print(f"GET failed: {e.code}")
    print(e.read().decode()[:500])