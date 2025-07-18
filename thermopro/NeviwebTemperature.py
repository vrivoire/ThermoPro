import json
import logging as log
import logging.handlers
import os.path
import traceback

import requests
from requests import Response

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"
LOGOUT_URL = f"{HOST}/api/logout"
LOCATIONS_URL = f"{HOST}/api/locations?account$id="
GATEWAY_DEVICE_URL = f"{HOST}/api/devices?location$id="
DEVICE_DATA_URL = f"{HOST}/api/device/"
NEVIWEB_LOCATION = f"{HOST}/api/location/"

ATTR_SIGNATURE = 'roomTemperatureDisplay'

HOME_PATH = f"{os.getenv('USERPROFILE')}/"
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"
LOG_FILE = f'{LOG_PATH}ThermoProScan.log'


def namer(name: str) -> str:
    return name.replace(".log", "") + ".log"


if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
fileHandler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='midnight', interval=1, backupCount=7,
                                                        encoding=None, delay=False, utc=False, atTime=None,
                                                        errors=None)
fileHandler.namer = namer
log.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
    handlers=[
        fileHandler,
        logging.StreamHandler()
    ]
)


class NeviwebTemperature:

    def __init__(
            self,
            hass,
            username,
            password,
            network,
            network2,
            network3,
            ignore_miwi,
            timeout=REQUESTS_TIMEOUT
    ):
        """Initialize the client object."""
        self.hass = hass
        self._email = username
        self._password = password
        self._network_name = network
        self._network_name2 = network2
        self._network_name3 = network3
        self._ignore_miwi = ignore_miwi
        self._gateway_id = None
        self._gateway_id2 = None
        self._gateway_id3 = None
        self.gateway_data = {}
        self.gateway_data2 = {}
        self.gateway_data3 = {}
        self.groups = {}
        self._headers = None
        self._account = None
        self._cookies = None
        self._timeout = timeout
        self._occupancyMode = None
        self.user = None

        # self.login()
        # self.__get_network()
        # self.__get_gateway_data()
        # self.logout()

    def login(self):
        data = {
            "username": self._email,
            "password": self._password,
            "interface": "neviweb",
            "stayConnected": 1,
        }
        try:
            raw_res: Response = requests.post(
                LOGIN_URL,
                json=data,
                cookies=self._cookies,
                allow_redirects=False,
                timeout=self._timeout,
            )
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

        if raw_res.status_code != 200:
            log.info("Login status: %s", raw_res.json())
            raise Exception("Cannot log in")

            # Update session
        self._cookies = raw_res.cookies
        data = raw_res.json()
        log.info("Login response: %s", data)
        if "error" in data:
            if data["error"]["code"] == "ACCSESSEXC":
                log.error(
                    "Too many active sessions. Close all neviweb130 "
                    + "sessions you have opened on other platform "
                    + "(mobile, browser, ...)"
                    + ", wait a few minutes, then reboot Home Assistant."
                )
            elif data["error"]["code"] == "USRBADLOGIN":
                log.error(
                    "Invalid Neviweb username and/or password... "
                    + "Check your configuration parameters"
                )
                self.notify_ha(
                    "Warning: Got USRBADLOGIN error, Invalid Neviweb username "
                    + "and/or password... Check your configuration parameters"
                )
            return False
        else:
            self.user = data["user"]
            self._headers = {"Session-Id": data["session"]}
            self._account = str(data["account"]["id"])
            log.info("Successfully logged in to: %s", self._account)

            return True

    # # https://neviweb.com/api/groups?location$id=33110&type=room
    def get_groups(self):
        if self._account is None:
            log.error(
                "Account ID is empty check your username and passord to log into Neviweb..."
            )
        else:
            try:
                raw_res = requests.get(
                    f'https://neviweb.com/api/groups?location$id={self.gateway_data[0]["location$id"]}',
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                self.groups = raw_res.json()
                # log.info("Number of groups found on Neviweb: %s", len(self.groups))
                # log.info("Updated groups data: %s", json.dumps(self.groups, indent=4))
            except OSError:
                raise Exception("Cannot get Neviweb's groups")

    def get_network(self):
        """Get gateway id associated to the desired network."""
        # Http requests
        if self._account is None:
            log.error(
                "Account ID is empty check your username and passord to log into Neviweb..."
            )
        else:
            try:
                raw_res = requests.get(
                    LOCATIONS_URL + self._account,
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                networks = raw_res.json()
                log.info("Number of networks found on Neviweb: %s", len(networks))
                log.info("networks: %s", networks)
                if (
                        self._network_name is None
                        and self._network_name2 is None
                        and self._network_name3 is None
                ):  # Use 1st network found, second or third if found
                    self._gateway_id = networks[0]["id"]
                    self._network_name = networks[0]["name"]
                    self._occupancyMode = networks[0]["mode"]
                    log.info("Selecting %s as first network", self._network_name)
                    if len(networks) > 1:
                        self._gateway_id2 = networks[1]["id"]
                        self._network_name2 = networks[1]["name"]
                        log.info(
                            "Selecting %s as second network", self._network_name2
                        )
                        if len(networks) > 2:
                            self._gateway_id3 = networks[2]["id"]
                            self._network_name3 = networks[2]["name"]
                            log.info(
                                "Selecting %s as third network", self._network_name3
                            )
                else:
                    for network in networks:
                        if network["name"] == self._network_name:
                            self._gateway_id = network["id"]
                            self._occupancyMode = network["mode"]
                            log.info(
                                "Selecting %s network among: %s",
                                self._network_name,
                                networks,
                            )
                            continue
                        elif (network["name"] == self._network_name.capitalize()) or (
                                network["name"]
                                == self._network_name[0].lower() + self._network_name[1:]
                        ):
                            self._gateway_id = network["id"]
                            log.info(
                                "Please check first letter of your network "
                                + "name, In capital letter or not? Selecting "
                                + "%s network among: %s",
                                self._network_name,
                                networks,
                            )
                            continue
                        else:
                            log.info(
                                "Your network name %s do not correspond to "
                                + "discovered network %s, skipping this one"
                                + ".... Please check your config if nothing "
                                + "is discovered.",
                                self._network_name,
                                network["name"],
                            )
                        if (
                                self._network_name2 is not None
                                and self._network_name2 != ""
                        ):
                            if network["name"] == self._network_name2:
                                self._gateway_id2 = network["id"]
                                log.info(
                                    "Selecting %s network among: %s",
                                    self._network_name2,
                                    networks,
                                )
                                continue
                            elif (
                                    network["name"] == self._network_name2.capitalize()
                            ) or (
                                    network["name"]
                                    == self._network_name2[0].lower()
                                    + self._network_name2[1:]
                            ):
                                self._gateway_id = network["id"]
                                log.info(
                                    "Please check first letter of your "
                                    + "network2 name, In capital letter or "
                                    + "not? Selecting %s network among: %s",
                                    self._network_name2,
                                    networks,
                                )
                                continue
                            else:
                                log.info(
                                    "Your network name %s do not correspond "
                                    + "to discovered network %s, skipping "
                                    + "this one...",
                                    self._network_name2,
                                    network["name"],
                                )
                        if (
                                self._network_name3 is not None
                                and self._network_name3 != ""
                        ):
                            if network["name"] == self._network_name3:
                                self._gateway_id3 = network["id"]
                                log.info(
                                    "Selecting %s network among: %s",
                                    self._network_name3,
                                    networks,
                                )
                                continue
                            elif (
                                    network["name"] == self._network_name3.capitalize()
                            ) or (
                                    network["name"]
                                    == self._network_name3[0].lower()
                                    + self._network_name3[1:]
                            ):
                                self._gateway_id = network["id"]
                                log.info(
                                    "Please check first letter of your "
                                    + "network3 name, In capital letter or "
                                    + "not? Selecting %s network among: %s",
                                    self._network_name3,
                                    networks,
                                )
                                continue
                            else:
                                log.info(
                                    "Your network name %s do not correspond "
                                    + "to discovered network %s, skipping "
                                    + "this one...",
                                    self._network_name3,
                                    network["name"],
                                )

            except OSError:
                raise Exception("Cannot get Neviweb's networks")
            # Update cookies
            self._cookies.update(raw_res.cookies)
            # Prepare data
            self.gateway_data = raw_res.json()
            # log.info("Updated gateway_data data: %s", json.dumps(self.gateway_data, indent=4))

    def get_gateway_data(self):
        """Get gateway data."""
        # Http requests
        try:
            raw_res = requests.get(
                GATEWAY_DEVICE_URL + str(self._gateway_id),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            log.info("Received gateway data: %s", raw_res.json())
        except OSError:
            raise Exception("Cannot get gateway data")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        self.gateway_data = raw_res.json()
        log.info("Gateway_data : %s", self.gateway_data)
        if self._gateway_id2 is not None:
            try:
                raw_res2 = requests.get(
                    GATEWAY_DEVICE_URL + str(self._gateway_id2),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                log.info("Received gateway data 2: %s", raw_res2.json())
            except OSError:
                raise Exception("Cannot get gateway data 2")
            # Prepare data
            self.gateway_data2 = raw_res2.json()
            log.info("Gateway_data2 : %s", self.gateway_data2)
        if self._gateway_id3 is not None:
            try:
                raw_res3 = requests.get(
                    GATEWAY_DEVICE_URL + str(self._gateway_id3),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                log.info("Received gateway data 3: %s", raw_res3.json())
            except OSError:
                raise Exception("Cannot get gateway data 3")
            # Prepare data
            self.gateway_data3 = raw_res3.json()
            log.info("Gateway_data3 : %s", self.gateway_data3)

        self.get_groups()
        for i in range(len(self.gateway_data)):
            data = self.groups[i]
            self.gateway_data[i]['displayName'] = self.groups[i]['name']

        for device in self.gateway_data:
            data = self.get_device_attributes(device["id"], [ATTR_SIGNATURE])
            if ATTR_SIGNATURE in data:
                device[ATTR_SIGNATURE] = data[ATTR_SIGNATURE]['value']
            log.info("Received signature data: %s", data)

        if self._gateway_id2 is not None:
            for device in self.gateway_data2:
                data2 = self.get_device_attributes(device["id"], [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data2:
                    device[ATTR_SIGNATURE] = data2[ATTR_SIGNATURE]
                log.info("Received signature data: %s", data2)

        if self._gateway_id3 is not None:
            for device in self.gateway_data3:
                data3 = self.get_device_attributes(device["id"], [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data3:
                    device[ATTR_SIGNATURE] = data3[ATTR_SIGNATURE]
                log.info("Received signature data: %s", data3)

        # log.info("Updated gateway data: %s", json.dumps(self.gateway_data, indent=4))
        # log.info(self.gateway_data)

    def get_device_attributes(self, device_id, attributes):
        """Get device attributes."""
        # Prepare return
        data = {}
        # Http requests
        try:
            log.info(attributes)
            log.info(",".join(attributes))
            raw_res = requests.get(
                DEVICE_DATA_URL
                + str(device_id)
                + "/attribute?attributes="
                + ",".join(attributes),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        #            _LOGGER.debug("Received devices data: %s", raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise Exception("Cannot get device attributes", e)
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                log.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
                # raise PyNeviweb130Error("Session expired... reconnecting...")
        # log.info(f"Updated data for device={device_id}: {json.dumps(data, indent=4)}")
        return data

    def logout(self):
        """Get gateway id associated to the desired network."""
        # Http requests
        if self._account is None:
            return "Account ID is empty check your username and passord to log into Neviweb..."

        else:
            try:
                raw_res = requests.get(
                    LOGOUT_URL,
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                resp = raw_res.json()
                return resp
            except OSError as ex:
                raise ex


if __name__ == '__main__':
    test2: NeviwebTemperature = NeviwebTemperature(None, "rivoire.vincent@gmail.com", "Mlvelc123.", None, None, None, None)
    try:
        log.info(f'login={test2.login()}')
        log.info(test2.get_network())
        log.info(test2.get_gateway_data())
        data: {str, int} = {}
        for gateway_data2 in test2.gateway_data:
            data[gateway_data2['displayName']] = gateway_data2['roomTemperatureDisplay']
        log.info("Updated data: %s", json.dumps(data, indent=4))
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
    finally:
        log.info(f'logout={test2.logout()}')
        test2.logout()
