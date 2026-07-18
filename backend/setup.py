"""Create Org, Profile, and PAT via session auth (SessionAuthentication now enabled)."""
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

# Login
resp = opener.open(base + '/admin/login/')
html = resp.read().decode()
csrf_html = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html).group(1)

data = urllib.parse.urlencode({
    'username': 'admin@allshoptotal.com.br',
    'password': 'admin',
    'csrfmiddlewaretoken': csrf_html,
    'next': '/admin/'
}).encode()
resp = opener.open(base + '/admin/login/', data=data)
print(f"Login: {resp.getcode()} -> {resp.url}")

if '/admin/login/' in resp.url:
    print("Login failed!"); sys.exit(1)

csrf = get_csrf()
print(f"Session CSRF: {csrf}")

# Create Org
print("\n--- Creating Org ---")
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
    
    org_id = result.get('org', {}).get('id')
    print(f"Org ID: {org_id}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Org create failed: {e.code}")
    print(body[:500])
    sys.exit(1)

# Create PAT
print("\n--- Creating PAT ---")
from secrets import token_urlsafe
raw_token = f"bcrm_pat_{token_urlsafe(32)}"
import hashlib
token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
token_prefix = raw_token[:20]

pat_data = json.dumps({
    'name': 'MCP Server Token',
    'token_prefix': token_prefix,
    'token_hash': token_hash,
    'is_active': True,
}).encode()

req = urllib.request.Request(
    base + '/api/common/profile/tokens/',
    data=pat_data,
    headers={
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
        'Referer': base + '/admin/',
    }
)
try:
    resp = opener.open(req)
    result = json.loads(resp.read().decode())
    print(f"PAT created! status={resp.getcode()}")
    print(json.dumps(result, indent=2))
    print(f"\n✅ RAW TOKEN: {raw_token}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"PAT create failed: {e.code}")
    print(body[:500])