from decorators import AUTH_COOKIE_NAME, CLIENT_HEADER_NAME, CLIENT_HEADER_VALUE
from support import ApiTestCase, TEST_FRONTEND_ORIGIN, TEST_PASSWORD, TEST_USER


class TestAuthApi(ApiTestCase):

    def test_login_sets_an_http_only_host_cookie_without_returning_the_token(self):
        self.client.delete_cookie(AUTH_COOKIE_NAME)

        response = self.client.post(
            '/authenticate',
            json={'user': TEST_USER, 'password': TEST_PASSWORD},
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.get_data(), b'')
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], TEST_FRONTEND_ORIGIN)
        self.assertEqual(response.headers['Access-Control-Allow-Credentials'], 'true')
        cookie_header = response.headers['Set-Cookie']
        attributes = {attribute.strip() for attribute in cookie_header.split(';')}
        self.assertTrue(cookie_header.startswith(f'{AUTH_COOKIE_NAME}='))
        self.assertIn('Path=/', attributes)
        self.assertIn('HttpOnly', attributes)
        self.assertIn('SameSite=Strict', attributes)
        self.assertNotIn('Secure', attributes)
        self.assertFalse(any(attribute.startswith('Domain=') for attribute in attributes))

        cookie = self.client.get_cookie(AUTH_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertTrue(self.app.extensions['auth'].validate_token(cookie.value))

    def test_invalid_credentials_do_not_set_a_cookie(self):
        self.client.delete_cookie(AUTH_COOKIE_NAME)

        response = self.client.post(
            '/authenticate',
            json={'user': TEST_USER, 'password': 'wrong-password'},
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()['error']['message'], 'unauthorized')
        self.assertNotIn('Set-Cookie', response.headers)
        self.assertIsNone(self.client.get_cookie(AUTH_COOKIE_NAME))

    def test_session_check_validates_the_cookie(self):
        response = self.client.get('/authenticate')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.get_data(), b'')

    def test_session_check_rejects_a_missing_or_invalid_cookie(self):
        self.client.delete_cookie(AUTH_COOKIE_NAME)

        missing = self.client.get(
            '/authenticate',
            headers={'Authorization': f'Bearer {self.token}'},
        )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(missing.get_data(as_text=True), 'missing auth cookie')

        self.client.set_cookie(AUTH_COOKIE_NAME, 'not-a-valid-token')
        invalid = self.client.get('/authenticate')
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(invalid.get_data(as_text=True), 'invalid token')

    def test_logout_clears_the_cookie(self):
        response = self.client.delete('/authenticate', headers=self.auth_headers)

        self.assertEqual(response.status_code, 204)
        cookie_header = response.headers['Set-Cookie']
        attributes = {attribute.strip() for attribute in cookie_header.split(';')}
        self.assertTrue(cookie_header.startswith(f'{AUTH_COOKIE_NAME}='))
        self.assertIn('Max-Age=0', attributes)
        self.assertIn('Path=/', attributes)
        self.assertIn('HttpOnly', attributes)
        self.assertIn('SameSite=Strict', attributes)
        self.assertNotIn('Secure', attributes)
        self.assertIsNone(self.client.get_cookie(AUTH_COOKIE_NAME))
        self.assertEqual(self.client.get('/authenticate').status_code, 401)

    def test_unsafe_requests_require_the_exact_origin_and_client_header(self):
        cases = (
            {},
            {'Origin': TEST_FRONTEND_ORIGIN},
            {CLIENT_HEADER_NAME: CLIENT_HEADER_VALUE},
            {'Origin': 'http://untrusted.test', CLIENT_HEADER_NAME: CLIENT_HEADER_VALUE},
            {'Origin': TEST_FRONTEND_ORIGIN, CLIENT_HEADER_NAME: 'other'},
        )

        for headers in cases:
            with self.subTest(headers=headers):
                response = self.client.post(
                    '/authenticate',
                    json={'user': TEST_USER, 'password': TEST_PASSWORD},
                    headers=headers,
                )
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.get_json()['error']['code'], 'forbidden')

    def test_safe_requests_do_not_require_the_unsafe_request_headers(self):
        response = self.client.get('/values')

        self.assertEqual(response.status_code, 200)

    def test_credentialed_cors_preflight_allows_the_configured_origin(self):
        self.client.delete_cookie(AUTH_COOKIE_NAME)

        response = self.client.options(
            '/authenticate',
            headers={
                'Origin': TEST_FRONTEND_ORIGIN,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': f'Content-Type, {CLIENT_HEADER_NAME}',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], TEST_FRONTEND_ORIGIN)
        self.assertEqual(response.headers['Access-Control-Allow-Credentials'], 'true')
        allowed_headers = response.headers['Access-Control-Allow-Headers']
        self.assertIn('Content-Type', allowed_headers)
        self.assertIn(CLIENT_HEADER_NAME, allowed_headers)

    def test_cors_does_not_allow_an_unconfigured_origin(self):
        response = self.client.get('/values', headers={'Origin': 'http://untrusted.test'})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
