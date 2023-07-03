import requests

# Step 1: Redirect the user to the service provider
# This step is usually done on the client side,
# by redirecting the user to a URL like this
# "https://orcid.org/oauth/authorize?client_id={client_id}&response_type=code&scope=/authenticate&redirect_uri={redirect_uri}"

# Step 2: User authorizes your app and is redirected back
# When the user is redirected back, your app will receive
# an authorization code in the URL.
# You will need to extract this authorization code from the URL

# Suppose you have received the authorization code
authorization_code = "KB-24-"
client_id = "APP-L8RLLJ0TD489GSTA"
client_secret = "724d959d-5b58-4e63-a535-fcfd1b2001b2"
redirect_uri = "https://www.google.com/"

# Step 3: Exchange authorization code for access token
url = "https://orcid.org/oauth/token"
data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "client_credentials",
    "scope": "/read-public",
}

response = requests.post(url, data=data)
response_data = response.json()
print(response_data)

access_token = response_data["access_token"]

print("Access token: ", access_token)
