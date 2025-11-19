from time import time
import json
import math
from typing import Dict
from .. import validator
from .._http_client import HttpClient
from ..exceptions import CatalystConnectorError
from .._constants import (
    CLIENT_ID,
    CLIENT_SECRET,
    AUTH_URL,
    REFRESH_IN,
    REFRESH_URL,
    CONNECTOR_NAME,
    REFRESH_TOKEN,
    EXPIRES_IN,
    REDIRECT_URL,
    GRANT_TYPE,
    CODE,
    RequestMethod,
    ACCESS_TOKEN
)


class Connector:
    def __init__(self, connection_instance, connector_details: Dict[str, str]) -> None:
        self._app = connection_instance._app
        self._requester: HttpClient = connection_instance._requester
        self.connector_name = connector_details.get(CONNECTOR_NAME)
        self.auth_url = connector_details.get(AUTH_URL)
        self.refresh_url = connector_details.get(REFRESH_URL)
        self.refresh_token = connector_details.get(REFRESH_TOKEN)
        self.client_id = connector_details.get(CLIENT_ID)
        self.client_secret = connector_details.get(CLIENT_SECRET)
        self.expires_in = (int(connector_details.get(EXPIRES_IN))
                           if connector_details.get(EXPIRES_IN)
                           else None)
        self.refresh_in = (int(connector_details.get(REFRESH_IN))
                           if connector_details.get(REFRESH_IN)
                           else None)
        self.redirect_url = connector_details.get(REDIRECT_URL)
        self.access_token = None
        self._expires_at = None

    @property
    def expires_at(self):
        return self._expires_at or None

    @property
    def _connector_name(self):
        return 'ZC_CONN_' + self.connector_name

    def generate_access_token(self, code: str) -> str:
        validator.is_non_empty_string(code, 'grant_token', CatalystConnectorError)
        validator.is_non_empty_string(self.redirect_url, REDIRECT_URL, CatalystConnectorError)
        resp = self._requester.request(
            method=RequestMethod().POST,
            url=self.auth_url,
            data={
                GRANT_TYPE: 'authorization_code',
                CODE: code,
                CLIENT_ID: self.client_id,
                CLIENT_SECRET: self.client_secret,
                REDIRECT_URL: self.redirect_url
            }
        )
        token_obj = resp.response_json
        try:
            self.access_token = token_obj[ACCESS_TOKEN]
            self.refresh_token = token_obj[REFRESH_TOKEN]
            self.expires_in = token_obj[EXPIRES_IN]
            current_time_ms = round(time() * 1000)
            self._expires_at = ((self.refresh_in * 1000 + current_time_ms) if self.refresh_in \
                    else current_time_ms + ((self.expires_in * 1000) - 900000))
        except KeyError as err:
            raise CatalystConnectorError(
                'Invalid Auth Response',
                f'{str(err)} is missing in the response json',
                token_obj
            ) from None
        self._persist_token_in_cache()
        return self.access_token

    def get_access_token(self):
        if self.access_token and self._expires_at and self._expires_at > round(time() * 1000):
            return self.access_token
        cached_token = self._app.cache().segment().get(self._connector_name)
        value = cached_token['cache_value']

        if value and self.is_valid_json(value):
            json_str = json.loads(value)
            self.access_token = json_str['access_token']
            self._expires_at = json_str['expires_at']
            if round(time() * 1000) < self._expires_at:
                return value

        validator.is_non_empty_string(self.refresh_token, 'refresh_token', CatalystConnectorError)

        resp = self._requester.request(
            method=RequestMethod.POST,
            url=self.refresh_url,
            data={
                GRANT_TYPE: 'refresh_token',
                CLIENT_ID: self.client_id,
                CLIENT_SECRET: self.client_secret,
                REFRESH_TOKEN: self.refresh_token
            }
        )
        token_obj = resp.response_json
        try:
            self.access_token = token_obj[ACCESS_TOKEN]
            self.expires_in = int(token_obj[EXPIRES_IN])
            current_time_ms = round(time() * 1000)
            self._expires_at = ((self.refresh_in * 1000 + current_time_ms) if self.refresh_in \
                    else current_time_ms + ((self.expires_in * 1000) - 900000))
        except KeyError as err:
            raise CatalystConnectorError(
                'Invalid Auth Response',
                f'{str(err)} is missing in the response json',
                token_obj
            ) from None
        self._persist_token_in_cache()
        return self.access_token

    def _persist_token_in_cache(self):
        token_obj = {
            'access_token': self.access_token,
            'expires_in': self.expires_in,
            'expires_at': self._expires_at
        }
        return self._app.cache().segment().put(
            self._connector_name,
            token_obj,
            math.ceil(self.expires_in/3600)
        )

    def is_valid_json(self, value: str) -> bool:
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
