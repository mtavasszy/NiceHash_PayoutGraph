import uuid
import hmac
import requests
import json
from hashlib import sha256
import pandas as pd
import matplotlib.pyplot as plt

# NH payouts API call setup - https://www.nicehash.com/docs/
path = "/main/api/v2/mining/rigs/payouts"
host = "https://api2.nicehash.com"
method = "GET"
query = "size=1000"											  # INCREASE THIS DEPENDING ON HOW LONG YOU'VE BEEN MINING

currentTime = requests.get("https://api2.nicehash.com/api/v2/time") # fetch current time using NH API
if currentTime.status_code != 200:
    if currentTime.content:
        raise Exception(str(currentTime.status_code) + ": " + currentTime.reason + ": " + str(currentTime.content))
    else:
        raise Exception(str(currentTime.status_code) + ": " + currentTime.reason)

xtime = str(currentTime.json()['serverTime'])
xnonce = str(uuid.uuid4())

organisation_id = ""                                          # PUT ORG ID HERE    
X_Request_Id =""
key = ""                                                      # API KEY HERE
secret = ""                                                   # API SECRET HERE

message = bytearray(key, 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(str(xtime), 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(xnonce, 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(organisation_id, 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(method, 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(path, 'utf-8')
message += bytearray('\x00', 'utf-8')
message += bytearray(query, 'utf-8')

digest = hmac.new(bytearray(secret, 'utf-8'), message, sha256).hexdigest()
xauth = key + ":" + digest

headers = {
    'X-Time': str(xtime),
    'X-Nonce': xnonce,
    'X-Auth': xauth,
    'Content-Type': 'application/json',
    'X-Organization-Id': organisation_id,
    'X-Request-Id': str(uuid.uuid4())
}
s = requests.Session()
s.headers = headers
url = host + path
if query:
    url += '?' + query

response = s.request(method, url)

if response.status_code == 200:
    data = response.json()
elif response.content:
    raise Exception(str(response.status_code) + ": " + response.reason + ": " + str(response.content))
else:
    raise Exception(str(response.status_code) + ": " + response.reason)

# Process received JSON
payouts = pd.json_normalize(data['list'])
payouts['amount'] = payouts['amount'].astype(float)
payouts['created'] = pd.to_datetime(payouts['created'],  unit='ms').dt.date
payouts_day = payouts.groupby(payouts['created'])['amount'].sum().reset_index()
payouts_day = payouts_day.iloc[1:len(payouts_day.index)-1]

# Fetch current Bitcoin price using the coindesk API (currently fetching EUR price)
currentBTC = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
if currentBTC.status_code != 200:
    print('could not retrieve time')
    raise
BTC_EUR = currentBTC.json()['bpi']['EUR']['rate_float']

# Plot data
x = payouts_day['created']
y = payouts_day['amount'] * BTC_EUR

plt.plot(x, y)
plt.ylabel("current BTC EUR")
plt.xticks(x, x.astype(str), rotation='vertical')

plt.show()