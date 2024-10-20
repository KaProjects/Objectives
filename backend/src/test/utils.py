import json
from datetime import date

import requests

origin = "http://127.0.0.1:7890"
token = requests.post(origin + "/authenticate", json.dumps({"user": "user", "password": "password"}), headers={"Content-Type": "application/json"}).text

def post_request(path, payload):
    response = requests.post(origin + path, payload, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    content = parse_content(response)
    return response.status_code, content, "Response: " + str(content)


def get_request(path):
    response = requests.get(origin + path, headers={"Authorization": "Bearer " + token})
    content = parse_content(response)
    return response.status_code, content, "Response: " + str(content)


def put_request(path, payload):
    response = requests.put(origin + path, payload, headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    content = parse_content(response)
    return response.status_code, content, "Response: " + str(content)


def delete_request(path):
    response = requests.delete(origin + path, headers={"Authorization": "Bearer " + token})
    content = parse_content(response)
    return response.status_code, content, "Response: " + str(content)


def parse_content(response):
    if response.headers.get('content-type').casefold() == "application/json":
        return response.json()
    else:
        return response.content.decode("utf-8")


def assert_bad_url(self, status, error, message):
    self.assertEqual(status, 404, message)
    self.assertTrue("The requested URL was not found on the server." in str(error), message)


def assert_method_not_allowed(self, status, error, message):
    self.assertEqual(status, 405, message)
    self.assertTrue("The method is not allowed for the requested URL." in str(error), message)


def today():
    return date.today().strftime("%d/%m/%Y")
