"""Create Org, Profile, and PAT via session auth."""
import requests, re, json, sys, secrets, hashlib

base = 'https://allshoptotal.onrender.com'
s = requests.Session()

# Login
r = s.get(base + '/admin/login/')
csrf = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)
print(f"CSRF: {csrf}")

r = s.post(base + '/admin/login/', data={
    'username': 'admin@allshoptotal.com.br',
    'password': 'admin',
    'csrfmiddlewaretoken': csrf,
    'next': '/admin/'
}, headers={'Referer': base + '/admin/login/'})
print(f"Login: {r.status_code} -> {r.url}")

if '/admin/login/' in r.url:
    print("Login failed!"); sys.exit(1)
print("✅ Logged in!")

# Create Org
print("\n--- Creating Org ---")
r = s.post(base + '/api/common/org/', json={
    'name': 'AllShopTotal',
    'email': 'contato@allshoptotal.com',
    'website': 'https://allshoptotal.com',
    'address': 'Foz do Iguaçu, PR',
}, headers={'Referer': base + '/admin/'})
print(f"Org create: {r.status_code}")
if r.status_code < 400:
    print(json.dumps(r.json(), indent=2))
    org_id = r.json().get('org', {}).get('id')
    print(f"Org ID: {org_id}")
else:
    print(r.text[:500])
    sys.exit(1)

# Create PAT
print("\n--- Creating PAT ---")
raw_token = f"bcrm_pat_{secrets.token_urlsafe(32)}"
r = s.post(base + '/api/common/profile/tokens/', json={
    'name': 'MCP Server Token',
    'is_active': True,
}, headers={'Referer': base + '/admin/'})
print(f"PAT create: {r.status_code}")
if r.status_code < 400:
    print(json.dumps(r.json(), indent=2))
    print(f"\n✅ RAW TOKEN: {raw_token}")
else:
    print(r.text[:500])
    # The PAT might not return the raw token - try API response
    print("Note: PAT endpoint may not expose raw token, check response above")