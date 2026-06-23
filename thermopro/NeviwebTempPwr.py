import math
import traceback
from queue import Queue
from typing import Any

import requests
from pandas import DataFrame
from requests import Response

import thermopro
from constants import NEVIWEB_EMAIL, NEVIWEB_PASSWORD
from thermopro import log

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"
LOGOUT_URL = f"{HOST}/api/logout"
LOCATIONS_URL = f"{HOST}/api/locations?account$id="
GATEWAY_DEVICE_URL = f"{HOST}/api/devices?location$id="
DEVICE_DATA_URL = f"{HOST}/api/device/"
GROUPS_URL = f'{HOST}/api/groups?location$id='

ATTR_ROOM_TEMPERATURE = "roomTemperature"


class NeviwebTempPwr:

    def __init__(
            self,
            username=NEVIWEB_EMAIL,
            password=NEVIWEB_PASSWORD,
            network=None,
            timeout=REQUESTS_TIMEOUT
    ):
        log.info(' Starting NeviwebTempPwr '.center(100, '*'))
        self._email = username
        self._password = password
        self._network_name = network
        self._gateway_id = None
        self._headers = None
        self._account = None
        self._cookies = None
        self._timeout = timeout
        self._occupancyMode = None

        self.user = {}
        self.locations = {}
        self.groups: dict[str, list[dict[str, Any]]] = {}
        self.gateway_data = {}

    def login(self) -> bool:
        input_data: dict[str, str | int] = {
            "username": self._email,
            "password": self._password,
            "interface": "neviweb",
            "stayConnected": 1,
        }
        raw_res: Response = None
        try:
            raw_res: Response = requests.post(
                LOGIN_URL,
                json=input_data,
                cookies=self._cookies,
                allow_redirects=False,
                timeout=self._timeout,
            )
            # raise Exception('toto')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            raise Exception("Cannot log in")

        if raw_res and raw_res.status_code != 200:
            log.info("Login status: %s", raw_res.json())
            raise Exception("Cannot log in")

        self._cookies = raw_res.cookies
        data = raw_res.json()
        # print(f'login:\n{thermopro.ppretty(data)}')
        # log.info("Login response: %s", data)
        if "error" in data:
            if data["error"]["code"] == "ACCSESSEXC":
                log.error("Too many active sessions. Close all neviweb130 sessions you have opened on other platform (mobile, browser, ...), wait a few minutes, then reboot Home Assistant.")
            elif data["error"]["code"] == "USRBADLOGIN":
                log.error("Invalid Neviweb username and/or password... Check your configuration parameters")
            else:
                log.error(f"Not logged: {data["error"]}")
            return False
        else:
            self.user = data["user"]
            self._headers = {"Session-Id": data["session"]}
            self._account = str(data["account"]["id"])
            log.info("Successfully logged in to: %s", self._account)
            return True

    def logout(self):
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
                log.error(ex)
                log.error(traceback.format_exc())
                return "Account ID is empty"
                # raise Exception("Cannot log out")

    def get_device_hourly_stats(self, device_id: int) -> list[dict[str, int]] | None:
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL + str(device_id) + "/consumption/hourly",
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise "Cannot get device hourly stats..."

        self._cookies.update(raw_res.cookies)
        data: list[dict[str, int]] = raw_res.json()
        if "history" in data:
            return data["history"]
        else:
            log.info(f"Hourly stat error for device: id: {device_id}, name: {device_id} --> {data}")
            return None

    def get_groups(self) -> None:
        for id in set([device['location$id'] for device in self.gateway_data.values()]):
            datas: list[dict[str, Any]] | None = self.get_group(id)
            if datas is not None:
                for data in datas:
                    self.groups[data['id']] = data
            else:
                raise Exception("Cannot get Neviweb's groups")
        # print(f'groups:\n{thermopro.ppretty(self.groups)}')

    def get_group(self, location_id: int) -> list[dict[str, Any]] | None:
        if self._account is None:
            log.error("Account ID is empty check your username and password to log into Neviweb...")
            return None
        else:
            try:
                raw_res = requests.get(
                    GROUPS_URL + str(location_id),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                group: list[dict[str, Any]] = raw_res.json()
                # print(f'group: location: {location_id}\n{thermopro.ppretty(group)}')
                return group
            except OSError:
                raise Exception("Cannot get Neviweb's group")

    def get_locations(self):
        if self._account is None:
            log.error("Account ID is empty check your username and passord to log into Neviweb...")
        else:
            try:
                raw_res = requests.get(
                    LOCATIONS_URL + self._account,
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                networks = raw_res.json()
                # print(f'location:\n{thermopro.ppretty(networks)}')
                log.info("Number of networks found on Neviweb: %s", len(networks))
                if self._network_name is None:
                    self._gateway_id = networks[0]["id"]
                    self._network_name = networks[0]["name"]
                    self._occupancyMode = networks[0]["mode"]
                    log.info("Selecting '%s' as first network", self._network_name)
            except OSError:
                raise Exception("Cannot get Neviweb's networks")
            self._cookies.update(raw_res.cookies)
            self.locations = raw_res.json()

    def get_gateway_data(self):
        try:
            raw_res = requests.get(
                GATEWAY_DEVICE_URL + str(self._gateway_id),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise Exception("Cannot get gateway data")

        self._cookies.update(raw_res.cookies)

        for device in raw_res.json():
            self.gateway_data[device['id']] = device

        # print(f'***gateway_data:\n{thermopro.ppretty(self.gateway_data)}')

    def get_device_attributes(self, device_id, attributes):
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL
                + str(device_id)
                + "/attribute?attributes="
                + ",".join(attributes),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout
            )

        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise Exception("Cannot get device attributes", e)
        self._cookies.update(raw_res.cookies)
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                log.error("Session expired. Set a scan_interval less than 10 minutes, otherwise the session will end.")
        return data

    def load_neviweb(self, result_queue: Queue):
        log.info(' Start load_neviweb '.center(100, '*'))
        result: dict[str, int | float | None] = {}
        try:
            if self.login():

                self.get_locations()
                self.get_gateway_data()
                self.get_groups()

                for device_id in self.gateway_data:
                    columns = [ATTR_ROOM_TEMPERATURE]
                    data: dict[str, Any] = self.get_device_attributes(device_id, columns)
                    for name in columns:
                        self.gateway_data[device_id][name] = data.get(name)['value'] if data.get(name) and type(data.get(name)) == dict and data.get(name).get('value') else None

                kwh_total = 0.0
                for device_id in self.gateway_data:
                    device_hourly_stats_list: list[dict[str, int]] | None = self.get_device_hourly_stats(device_id)
                    device = self.gateway_data[device_id]
                    group_name = str(self.groups[device["group$id"]]['name']).replace(' ', '-').lower()
                    if device_hourly_stats_list is not None:
                        kwh: float = round(device_hourly_stats_list[len(device_hourly_stats_list) - 1]["period"] / 1000, 3)
                        kwh_total += kwh
                        result[f'kwh_{group_name}'] = kwh if not math.isnan(kwh) else 0.0

                    if device['roomTemperature'] is not None:
                        result[f'int_temp_{group_name}'] = float(device['roomTemperature']) if not math.isnan(device['roomTemperature']) else 0.0

                result['kwh_neviweb'] = kwh_total if not math.isnan(kwh_total) else 0.0

                names = {int(g['id']): str(g['name']).replace(' ', '-').lower() for g in self.groups.values()}
                name_size = max((len(name) for name in names.values()), default=0)
                for name in sorted(names.values()):
                    _temp = f'{result.get('int_temp_' + name):.2f}' if result.get('int_temp_' + name) else 0.0
                    _kwh = result.get('kwh_' + name) if result.get('kwh_' + name) else 0
                    log.info(f'>>>>>> {name:<{name_size + 1}} {_temp:>6}°C {_kwh:>6}KWh')
                log.info(f'>>>>>> {'kwh_neviweb':<{name_size + 1}} {result['kwh_neviweb']:>4}KWh')
                log.info(f'result={result}')

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            log.error("Using previous data")
            df: DataFrame = thermopro.load_json()
            last_row_series = df.iloc[-1]
            # print(last_row_series)
            result = {
                "int_temp_bureau": last_row_series['int_temp_bureau'],
                "int_temp_chambre": last_row_series['int_temp_chambre'],
                "int_temp_corridor": last_row_series['int_temp_corridor'],
                "int_temp_salle-de-bain": last_row_series['int_temp_salle-de-bain'],
                "int_temp_salon": last_row_series['int_temp_salon'],
                "kwh_bureau": last_row_series['kwh_bureau'],
                "kwh_chambre": last_row_series['kwh_chambre'],
                "kwh_neviweb": last_row_series['kwh_neviweb'],
                "kwh_salle-de-bain": last_row_series['kwh_salle-de-bain'],
                "kwh_salon": last_row_series['kwh_salon'],
            }
        finally:
            log.info(f'logout={self.logout()}')
            result_queue.put(result)
        log.info(f' End load_neviweb '.center(100, '*'))


if __name__ == '__main__':

    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    neviweb_temperature: NeviwebTempPwr = NeviwebTempPwr()
    neviweb_temperature.load_neviweb(result_queue)
    while not result_queue.empty():
        result: dict[str, int | float | None] = result_queue.get()
        print(thermopro.ppretty(result))
