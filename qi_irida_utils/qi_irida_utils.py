# -*- coding: utf-8 -*-
import threading
from urllib.request import urlopen, URLError
from rauth import OAuth2Service
import ast


class ApiCalls(object):

    _instance = None

    def __new__(cls, client_id, client_secret, base_url, username, password, max_wait_time=20):
        """
            Overriding __new__ to implement a singleton
            This is done instead of a decorator so that mocking still works for class.
            If the instance has not been created yet, or the passed in arguments are different, create a new instance,
                and drop the old (if existing) instance
            If the instance already exists and is valid, return the instance

            arguments:
                client_id -- client_id for creating access token.
                client_secret -- client_secret for creating access  token.
                base_URL -- url of the IRIDA server
                username -- username for server
                password -- password for given username
                max_wait_time -- timeout (seconds), default=20

        """

        if not ApiCalls._instance or ApiCalls._instance.parameters_are_different(
                client_id, client_secret, base_url, username, password, max_wait_time):

            # Create a new instance of the API
            ApiCalls._instance = object.__new__(cls)

            # initialize API instance variables
            ApiCalls._instance.client_id = client_id
            ApiCalls._instance.client_secret = client_secret
            ApiCalls._instance.base_url = base_url
            # Clean up missing '/'
            if ApiCalls._instance.base_URL[-1:] != "/":
                ApiCalls._instance.base_url = ApiCalls._instance.base_url + "/"
            ApiCalls._instance.username = username
            ApiCalls._instance.password = password
            ApiCalls._instance.max_wait_time = max_wait_time

            # initialize API object
            ApiCalls._instance._session_lock = threading.Lock()
            ApiCalls._instance._session_set_externally = False
            ApiCalls._instance.create_session()
            ApiCalls._instance.cached_projects = None
            ApiCalls._instance.cached_samples = {}

        return ApiCalls._instance

    def create_session(self):
        """
        create session to be re-used until expiry for get and post calls

        returns session (OAuth2Session object)
        """



        oauth_service = self.get_oauth_service()
        access_token = self.get_access_token(oauth_service)
        self._session = oauth_service.get_session(access_token)


        if self.validate_url_existence(self.base_url, use_session=True) is False:
            raise Exception("Cannot create session. Verify your credentials are correct.")
        else:
            raise URLError(self.base_url + " is not a valid URL")

    def get_oauth_service(self):
        """
        get oauth service to be used to get access token

        returns oauthService
        """

        access_token_url = self.base_url + "oauth/token"
        oauth_serv = OAuth2Service(
            client_id=self.client_id,
            client_secret=self.client_secret,
            name="irida",
            access_token_url=access_token_url,
            base_url=self.base_url
        )

        return oauth_serv

    def validate_url_existence(self, url, use_session=False):
        """
        tries to validate existence of given url by trying to open it.
        true if HTTP OK, false if HTTP NOT FOUND otherwise
            raises error containing error code and message

        arguments:
            url -- the url link to open and validate
            use_session -- if True then this uses self.session.get(url) instead
            of urlopen(url) to get response

        returns
            true if http response OK 200
            false if http response NOT FOUND 404
        """

        if use_session:
            response = self.session.get(url)

            if response.status_code == 200:
                return True
            elif response.status_code == 400:
                return False
            else:
                raise Exception(
                    str(response.status_code) + " " + response.reason)

        else:
            response = urlopen(url, timeout=self.max_wait_time)

            if response.code == 200:
                return True
            elif response.code == 404:
                return False
            else:
                raise Exception(str(response.code) + " " + response.msg)

    def get_access_token(self, oauth_service):
        """
        get access token to be used to get session from oauth_service

        arguments:
            oauth_service -- O2AuthService from get_oauth_service

        returns access token
        """

        params = {
            "data": {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }
        }
        access_token = oauth_service.get_access_token(
            decoder=self.decoder, **params)
        return access_token

    @staticmethod
    def decoder(return_dict):
        """
        safely parse given dictionary

        arguments:
            return_dict -- access token dictionary

        returns evaluated dictionary
        """

        irida_dict = ast.literal_eval(return_dict)
        return irida_dict


def test_connection():
    """Assumes localhost, tests Oauth"""
    ApiCalls('upload',
             'JFEq4dOPR2y9Arl5w6Mq7d94N07M1YORdaR2A3l6La',
             'http://localhost:8080/',
             'admin',
             'sXVN&4#JI5b4')


test_connection()
