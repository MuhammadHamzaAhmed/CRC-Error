import requests

requests.packages.urllib3.disable_warnings()

session = requests.Session()
session.verify = False
