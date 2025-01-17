import requests

try:
    from . import custom_logging
except Exception:
    import custom_logging

LOGGING_ID = "AdminUser"
LOGGER = custom_logging.getLogger(LOGGING_ID)
NAME = LOGGING_ID


class AdminUser(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.init_token()

    def init_token(self):
        self.access_token = None

        url = self.host + "/auth/api_token"
        payload = {"username": self.username, "password": self.password}

        try:
            resp = requests.post(url, json=payload)

            if resp.status_code == 200:
                self.access_token = resp.json()["access_token"]
                LOGGER.debug(
                    f"AdminUser: Token Load Success [{url}]: " + str(resp.status_code)
                )
            else:
                LOGGER.error(
                    f"Admin: Token Load Fail [{url}]: " + str(resp.status_code)
                )
        except Exception as ex:
            LOGGER.error(f"RemoteSync: Token Load Fail [{url}]: ", exc_info=ex)

    def get_access_headers(self):
        if self.access_token is None:
            return None
        return {"Authorization": "Bearer " + self.access_token}
