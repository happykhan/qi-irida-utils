import json
import logging
from urllib.parse import urlsplit

from rauth import OAuth2Service

LOGLEVEL_TRACE = 5

logger = logging.getLogger("irida_connector")


def decode_access_token(s):
    """
    Used to decode the access token.
    :param s: The input bytes.
    :return: A dictionary.
    """
    return json.loads(s.decode("utf-8"))


class IridaConnector(object):
    """Low-level connections to the IRIDA REST API"""

    def __init__(self, client_id, client_secret, username, password, base_url, timeout):
        """
        Creates a new object for connecting to the IRIDA REST API

        :param client_id:  The client_id for IRIDA.
        :param client_secret:  The client secret for IRIDA.
        :param username:  The username of the user for IRIDA.
        :param password:  The password for the user.
        :param base_url:  The base URL for IRIDA (minis the '/api' part)
        :param timeout:  The maximum timeout for any connection to IRIDA.

        :return: An object which can be used to connect to IRIDA.
        """
        base_url = base_url.rstrip("/")
        self._base_path = urlsplit(base_url).path
        self._timeout = timeout

        access_token_url = base_url + "/api/oauth/token"

        params = {
            "data": {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
            }
        }

        oauth_service = OAuth2Service(
            client_id=client_id,
            client_secret=client_secret,
            name="irida",
            access_token_url=access_token_url,
            base_url=base_url,
        )

        token = oauth_service.get_access_token(decoder=decode_access_token, **params)
        self.session = oauth_service.get_session(token)

    def get(self, path):
        """
        A GET request to a particular path in IRIDA.

        :param path: The path to GET, minus the IRIDA url (e.g., '/projects').

        :return:  The result of rauth.OAuth2Service.get()
        """
        path = self._join_path(path)
        logger.debug("Getting path=" + path)
        response = self.session.get(path, timeout=self._timeout)

        if response.ok:
            self._log_json(response.json())
            return response.json()["resource"]
        else:
            response.raise_for_status()

    def _join_path(self, path):
        if self._base_path is None or self._base_path == "":
            return path
        # If passed full URL like http://localhost/path, don't add on base_path
        elif urlsplit(path).scheme != "":
            return path
        else:
            if path[0] == "/":
                return self._base_path + path
            else:
                return self._base_path + "/" + path

    def get_resources(self, path):
        """
        GETs the resources from an IRIDA REST API endpoint (e.g., (get '/projects')['resources']

        :param path: The path to GET the resources.

        :return:  The ['resources'] part of the GET JSON response.
        """
        return self.get(path)["resources"]

    def get_file(self, path):
        """
        GETs the file contents from an IRIDA REST API endpoint.

        :param path: The path to GET the file.

        :return:  The file contents.
        """
        return self.session.get(
            path, headers={"Accept": "text/plain"}, timeout=self._timeout
        )

    def _log_json(self, json_obj):
        logger.log(
            LOGLEVEL_TRACE,
            json.dumps(json_obj, sort_keys=True, separators=(",", ":"), indent=4),
        )


j = IridaConnector(
    "nono",
    "39BLe5V70xroL6w3kL8L2C6eVTVCFpgUn01p1U02j5",
    "admin",
    "sXVN&4#JI5b4",
    "http://localhost:8080",
    30,
)
