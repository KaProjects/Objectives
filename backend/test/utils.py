from datetime import date

_client = None
_mutation_headers = None


def configure_client(client, mutation_headers=None):
    global _client, _mutation_headers
    _client = client
    _mutation_headers = mutation_headers


def _request(method, path, payload=None):
    if _client is None:
        raise RuntimeError('API test client is not configured; inherit from ApiTestCase')

    headers = dict(_mutation_headers or {}) if method in {'POST', 'PUT', 'PATCH', 'DELETE'} else {}
    request_arguments = {'method': method, 'headers': headers}
    if method in {'POST', 'PUT'}:
        request_arguments.update(data=payload, content_type='application/json')

    response = _client.open(path, **request_arguments)
    content = parse_content(response)
    return response.status_code, content, 'Response: ' + str(content)


def post_request(path, payload):
    return _request('POST', path, payload)


def get_request(path):
    return _request('GET', path)


def put_request(path, payload):
    return _request('PUT', path, payload)


def delete_request(path):
    return _request('DELETE', path)


def parse_content(response):
    if response.mimetype == 'application/json':
        body = response.get_json()
        if response.status_code >= 400 and isinstance(body, dict) and "error" in body:
            return body["error"]["message"]
        return body
    return response.get_data(as_text=True)


def assert_bad_url(self, status, error, message):
    self.assertEqual(status, 404, message)
    self.assertTrue("The requested URL was not found on the server." in str(error), message)


def assert_method_not_allowed(self, status, error, message):
    self.assertEqual(status, 405, message)
    self.assertTrue("The method is not allowed for the requested URL." in str(error), message)


def today():
    return date.today().isoformat()
