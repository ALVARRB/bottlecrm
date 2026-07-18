import os, sys, secrets

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
os.environ['DEBUG'] = 'True'
os.environ['DBNAME'] = 'crm_db'
os.environ['DBUSER'] = 'crm_user'
os.environ['DBPASSWORD'] = 'crm_user'
os.environ['DBHOST'] = 'dpg-cv-xxxxx-a.oregon-postgres.render.com'
os.environ['DBPORT'] = '5432'
os.environ['SECRET_KEY'] = 'dev-secret-key-for-testing-only'

import django
django.setup()

from django.contrib.auth import get_user_model
from common.models import Org, Profile, PersonalAccessToken

User = get_user_model()

# Create org
org, created = Org.objects.get_or_create(
    name="AllShopTotal",
    defaults={
        "address": "Foz do Iguaçu, PR",
        "email": "contato@allshoptotal.com",
        "website": "https://allshoptotal.com",
    }
)
print(f"Org: {org.name} (id={org.id}, created={created})")

# Get admin user
user = User.objects.get(email="admin@allshoptotal.com.br")

# Create profile
profile, p_created = Profile.objects.get_or_create(
    user=user,
    org=org,
    defaults={"role": "admin"}
)
print(f"Profile: {profile.user.email} -> {profile.org.name} (created={p_created})")

# Create PAT
raw_token = f"bcrm_pat_{secrets.token_urlsafe(32)}"
pat = PersonalAccessToken.objects.create(
    profile=profile,
    token_hash=PersonalAccessToken.hash_token(raw_token),
    token_prefix=raw_token[:20],
    name="MCP Server Token",
    is_active=True,
)
print(f"\n✅ PAT created!")
print(f"Token: {raw_token}")
print(f"Name: {pat.name}")