"""Login to AllShopTotal CRM admin, create org, profile, and PAT via session auth."""
import urllib.request, urllib.parse, http.cookiejar, re, json, sys

base = 'https://allshoptotal.onrender.com'

# Setup cookie jar
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

# Step 1: Get login page (gets CSRF cookie)
resp = opener.open(base + '/admin/login/')
html = resp.read().decode()
print(f"Step 1: Got login page, status={resp.getcode()}")

# Step 2: Login
csrf = get_csrf()
print(f"CSRF token: {csrf}")

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
try:
    resp = opener.open(req)
    print(f"Step 2: Login status={resp.getcode()}, url={resp.url}")
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code}")
    print(e.read().decode()[:500])
    sys.exit(1)

# Check if we're logged in
if '/admin/login/' in resp.url:
    print("Login failed - still on login page")
    sys.exit(1)
print("Login successful!")

# Step 3: Create org via API
csrf = get_csrf()
print(f"Using CSRF: {csrf}")

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
    print(f"Step 3: Org created! status={resp.getcode()}")
    print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Org create failed: {e.code}")
    print(body[:500])
    # Try browseable API format
    if e.code == 403:
        print("CSRF validation failed - trying different approach")
except Exception as e:
    print(f"Error: {e}")

# Step 4: List cookies for debugging
print("\nCookies:")
for c in cj:
    print(f"  {c.name}={c.value[:20] if c.value else 'None'}... domain={c.domain} path={c.path}")