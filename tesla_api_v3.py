import argparse
import base64
import hashlib
import os
import re
import time
from urllib.parse import parse_qs

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

CLIENT_ID = "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
#UA = "Mozilla/5.0 (Linux; Android 10; Pixel 3 Build/QQ2A.200305.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/94.0.4606.61 Mobile Safari/537.36"
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
X_TESLA_USER_AGENT = "TeslaApp/3.10.9-433/adff2e065/android/10"

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.add_argument('--start-maximized')
options.add_argument(f'user-agent={UA}')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
driver = webdriver.Chrome(chrome_options=options)

session, resp, params, code_verifier = (None,) * 4
verifier_bytes = os.urandom(86)
code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=")
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b"=")
state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode("utf-8")


headers = {
    "User-Agent": UA,
    "x-tesla-user-agent": X_TESLA_USER_AGENT,
    "X-Requested-With": "com.teslamotors.tesla",
}

params = (
    ("audience", ""),
    ("client_id", "ownerapi"),
    ("code_challenge", code_challenge),
    ("code_challenge_method", "S256"),
    ("locale", "en"),
    ("prompt", "login"),
    ("redirect_uri", "https://auth.tesla.com/void/callback"),
    ("response_type", "code"),
    ("scope", "openid email offline_access"),
    ("state", state),
)

session = requests.Session()
resp = session.post("https://auth.tesla.com/oauth2/v3/authorize", headers=headers, params=params, timeout=5)
driver.get(resp.request.url)
time.sleep(5)
while driver.title == "Tesla SSO - Sign In":
    time.sleep(2)
    print("Wating for login")


response = parse_qs(driver.current_url)
code = response["https://auth.tesla.com/void/callback?code"][0]
payload = {
    "grant_type": "authorization_code",
    "client_id": "ownerapi",
    "code_verifier": code_verifier.decode("utf-8"),
    "code": code,
    "redirect_uri": "https://auth.tesla.com/void/callback",
}
resp = session.post("https://auth.tesla.com/oauth2/v3/token", headers=headers, json=payload)
access_token = resp.json()["access_token"]

headers["authorization"] = "bearer " + access_token
payload = {
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "client_id": CLIENT_ID,
}
resp = session.post("https://owner-api.teslamotors.com/oauth/token", headers=headers, json=payload)
driver.get(f"data:text/html;charset=utf-8,{resp.content}")
