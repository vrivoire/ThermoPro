import traceback
from queue import Queue
from typing import Any

import requests
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

ATTR_ALERT = "alert"
ATTR_SIGNATURE = "signature"
ATTR_POWER_MODE = "powerMode"
ATTR_MODE = "mode"
ATTR_ONOFF = "onOff"
ATTR_ONOFF2 = "onOff2"
ATTR_INTENSITY = "intensity"
ATTR_INTENSITY_MIN = "intensityMin"
ATTR_WATTAGE = "loadConnected"
ATTR_WATTAGE_INSTANT = "wattageInstant"
ATTR_WATTAGE_OVERRIDE = "wattageOverride"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_ROOM_SETPOINT = "roomSetpoint"
ATTR_ROOM_SETPOINT_AWAY = "roomSetpointAway"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_OUTPUT_PERCENT_DISPLAY = "outputPercentDisplay"
ATTR_ROOM_SETPOINT_MIN = "roomSetpointMin"
ATTR_ROOM_SETPOINT_MAX = "roomSetpointMax"
ATTR_GFCI_STATUS = "gfciStatus"
ATTR_GFCI_ALERT = "alertGfci"
ATTR_WATER_LEAK_STATUS = "waterLeakStatus"
ATTR_WATER_LEAK_ALARM_STATUS = "waterleakDetectionAlarmStatus"
ATTR_WATER_LEAK_DISCONECTED_STATUS = "waterleakDisconnectedAlarmStatus"
ATTR_POWER_SUPPLY = "backupPowerSupply"
ATTR_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_BATTERY_STATUS = "batteryStatus"
ATTR_BATTERY_TYPE = "batteryType"
ATTR_FLOOR_MODE = "airFloorMode"
ATTR_FLOOR_OUTPUT2 = "loadWattOutput2"  # status on/off, value=xx
ATTR_FLOOR_AUX = "auxHeatConfig"
ATTR_KEYPAD = "lockKeypad"
ATTR_OCCUPANCY = "occupancyMode"
ATTR_FLOOR_OUTPUT1 = "loadWattOutput1"  # status on/off, value=xx
ATTR_LIGHT_WATTAGE = "loadWattOutput1"  # status on/off, value=xx
ATTR_OUTPUT1 = "loadWattOutput1"
ATTR_WIFI_WATTAGE = "loadWatt"
ATTR_WIFI_WATT_NOW = "loadWattNow"
ATTR_WIFI = "wifiRssi"
ATTR_RSSI = "rssi"
ATTR_DISPLAY2 = "config2ndDisplay"
ATTR_WIFI_KEYPAD = "keyboardLock"
ATTR_TIMER = "powerTimer"
ATTR_TIMER2 = "powerTimer2"
ATTR_DRSTATUS = "drStatus"
ATTR_BACKLIGHT = "backlightAdaptive"
ATTR_BACKLIGHT_AUTO_DIM = "backlightAutoDim"
ATTR_LED_ON_INTENSITY = "statusLedOnIntensity"
ATTR_LED_OFF_INTENSITY = "statusLedOffIntensity"
ATTR_LED_ON_COLOR = "statusLedOnColor"
ATTR_LED_OFF_COLOR = "statusLedOffColor"
ATTR_STATE = "state"
ATTR_RED = "red"
ATTR_GREEN = "green"
ATTR_BLUE = "blue"
ATTR_TIME = "timeFormat"
ATTR_TEMP = "temperatureFormat"
ATTR_MOTOR_POS = "motorPosition"
ATTR_TEMP_ALARM = "temperatureAlarmStatus"
ATTR_LOW_TEMP_STATUS = "alertLowTempStatus"
ATTR_TEMPERATURE = "temperature"
ATTR_WATER_TEMPERATURE = "waterTemperature"
ATTR_ROOM_TEMP_ALARM = "roomTemperatureAlarmStatus"
ATTR_VALVE_CLOSURE = "valveClosureSource"  # source
ATTR_LEAK_ALERT = "alertWaterLeak"
ATTR_BATT_ALERT = "alertLowBatt"
ATTR_TEMP_ALERT = "alertLowTemp"
ATTR_FUEL_ALERT = "alertLowFuel"
ATTR_REFUEL = "alertRefuel"
ATTR_FUEL_PERCENT_ALERT = "alertLowFuelPercent"
ATTR_CONF_CLOSURE = "cfgValveClosure"
ATTR_MOTOR_TARGET = "motorTargetPosition"
ATTR_FLOOR_AIR_LIMIT = "floorMaxAirTemperature"
ATTR_FLOOR_MAX = "floorLimitHigh"
ATTR_FLOOR_MIN = "floorLimitLow"
ATTR_ROOM_TEMP_DISPLAY = "roomTemperatureDisplay"
ATTR_EARLY_START = "earlyStartCfg"
ATTR_FLOOR_SENSOR = "floorSensorType"
ATTR_AUX_CYCLE = "auxCycleLength"
ATTR_CYCLE = "cycleLength"
ATTR_CYCLE_OUTPUT2 = "cycleLengthOutput2"  # status on/off, value (second)
ATTR_PUMP_PROTEC = "pumpProtection"  # status on/off, duration, frequency
ATTR_PUMP_PROTEC_DURATION = "pumpProtectDuration"  # status on/off, value
ATTR_PUMP_PROTEC_PERIOD = "pumpProtectPeriod"  # status on/off, value
ATTR_TYPE = "type"
ATTR_PHASE_CONTROL = "phaseControl"
ATTR_SYSTEM_MODE = "systemMode"
ATTR_DRSETPOINT = "drSetpoint"
ATTR_DRACTIVE = "drActive"
ATTR_OPTOUT = "optOut"
ATTR_SETPOINT = "setpoint"
ATTR_INPUT_STATUS = "inputStatus"
ATTR_INPUT2_STATUS = "input2Status"
ATTR_EXT_TEMP = "externalTemperature"
ATTR_REL_HUMIDITY = "relativeHumidity"
ATTR_STATUS = "status"
ATTR_ERROR_CODE_SET1 = "errorCodeSet1"
ATTR_FLOW_METER_CONFIG = "flowMeterMeasurementConfig"
ATTR_VALVE_INFO = "valveInfo"
ATTR_STM8_ERROR = "stm8Error"
ATTR_TANK_SIZE = "tankSize"
ATTR_CONTROLLED_DEVICE = "controlledDevice"
ATTR_COLD_LOAD_PICKUP_STATUS = "coldLoadPickupStatus"
ATTR_KEY_DOUBLE_UP = "configKeyDoubleUp"
ATTR_ANGLE = "angle"
ATTR_SAMPLING = "samplingTime"
ATTR_TANK_TYPE = "tankType"
ATTR_TANK_HEIGHT = "tankHeight"
ATTR_TANK_PERCENT = "tankPercent"
ATTR_GAUGE_TYPE = "gaugeType"
ATTR_COOL_SETPOINT = "coolSetpoint"
ATTR_COOL_SETPOINT_MIN = "coolSetpointMin"
ATTR_COOL_SETPOINT_MAX = "coolSetpointMax"
ATTR_WATER_TEMP_MIN = "drConfigWaterTempMin"
ATTR_MIN_WATER_TEMP = "minWaterTankTemperature"
ATTR_WATT_TIME_ON = "drWTTimeOn"
ATTR_DR_WATER_TEMP_TIME = "drConfigWaterTempTime"
ATTR_WATER_TEMP_TIME = "waterTempTime"
ATTR_FLOW_ALARM1 = "flowMeterAlarm1Config"
ATTR_FLOW_ALARM2 = "flowMeterAlarm2Config"
ATTR_AWAY_ACTION = "awayAction"
ATTR_FLOW_ENABLED = "flowMeterEnabled"
ATTR_FLOW_MODEL_CONFIG = "FlowModel"
ATTR_FLOW_ALARM_TIMER = "flowMeterAlarmDisableTimer"
ATTR_FLOW_THRESHOLD = "alarm1FlowThreshold"
ATTR_FLOW_ALARM1_LENGHT = "alarm1Length"
ATTR_FLOW_ALARM1_PERIOD = "alarm1Period"
ATTR_FLOW_ALARM1_OPTION = "alarm1Options"
ATTR_DR_PROTEC_STATUS = "drProtectionLegStatus"
ATTR_LEG_PROTEC_STATUS = "legProtectionStatus"
ATTR_COLD_LOAD_PICKUP_REMAIN_TIME = "coldLoadPickupRemainingTime"
ATTR_COLD_LOAD_PICKUP_TEMP = "coldLoadPickupTemperature"
ATTR_TEMP_ACTION_LOW = "temperatureActionLow"
ATTR_BATT_ACTION_LOW = "batteryActionLow"
ATTR_NAME_1 = "input1name"
ATTR_NAME_2 = "input2name"
ATTR_OUTPUT_NAME_1 = "output1name"
ATTR_OUTPUT_NAME_2 = "output2name"
ATTR_WATER_TANK_ON = "waterTankTimeOn"
ATTR_HEAT_LOCK_TEMP = "heatLockoutTemperature"
ATTR_COOL_LOCK_TEMP = "coolLockoutTemperature"
ATTR_AVAIL_MODE = "availableMode"
ATTR_FAN_SPEED = "fanSpeed"
ATTR_FAN_CAP = "fanCapabilities"
ATTR_FAN_SWING_VERT = "fanSwingVertical"
ATTR_FAN_SWING_HORIZ = "fanSwingHorizontal"
ATTR_FAN_SWING_CAP = "fanSwingCapabilities"
ATTR_FAN_SWING_CAP_HORIZ = "fanSwingCapabilityHorizontal"
ATTR_FAN_SWING_CAP_VERT = "fanSwingCapabilityVertical"
ATTR_DISPLAY_CONF = "displayConfig"
ATTR_DISPLAY_CAP = "displayCapability"
ATTR_MODEL = "model"
ATTR_SOUND_CONF = "soundConfig"
ATTR_SOUND_CAP = "soundCapability"
ATTR_LANGUAGE = "language"
ATTR_MODE = "mode"
ATTR_HC_DEV = "hcDevice"
ATTR_BALANCE_PT = "balancePoint"
ATTR_BALANCE_PT_TEMP_LOW = "balancePointTempLow"
ATTR_BALANCE_PT_TEMP_HIGH = "balancePointTempHigh"
ATTR_BATT_PERCENT_NORMAL = "batteryPercentNormalized"
ATTR_BATT_STATUS_NORMAL = "batteryStatusNormalized"
ATTR_BATT_INFO = "displayBatteryInfo"
ATTR_INPUT_1_ON_DELAY = "inputOnDebounceDelay"
ATTR_INPUT_2_ON_DELAY = "inputOnDebounceDelay2"
ATTR_INPUT_1_OFF_DELAY = "inputOffDebounceDelay"
ATTR_INPUT_2_OFF_DELAY = "inputOffDebounceDelay2"
ATTR_VALUE = "value"
ATTR_ACTIVE = "active"
ATTR_ONOFF_NUM = "onOff_num"
ATTR_CLOSE_VALVE = "closeValve"
ATTR_TRIGGER_ALARM = "triggerAlarm"
ATTR_DELAY = "delay"
ATTR_INPUT_NUMBER = "input_number"
ATTR_COLD_LOAD_PICKUP = "coldLoadPickup"
ATTR_HEAT_LOCKOUT_TEMP = "heatLockoutTemp"
ATTR_OCCUPANCY_SENSOR_DELAY = "occupancySensorUnoccupiedDelay"
ATTR_LEAK_CLOSURE_CONFIG = "waterLeakClosureConfig"
ATTR_HUMID_DISPLAY = "humidityDisplay"
ATTR_HUMID_SETPOINT = "humiditySetpoint"
ATTR_DUAL_STATUS = "dualEnergyStatus"
ATTR_HEAT_SOURCE_TYPE = "heatSourceType"
ATTR_AUX_HEAT_SOURCE_TYPE = "auxHeatSourceType"
ATTR_COOL_SETPOINT_AWAY = "coolSetpointAway"
ATTR_FAN_FILTER_REMAIN = "fanFilterReminderPeriod"
ATTR_AUX_HEAT_TIMEON = "auxHeatMinTimeOn"
ATTR_AUX_HEAT_START_DELAY = "auxHeatStartDelay"
ATTR_HEAT_INTERSTAGE_MIN_DELAY = "heatInterstageMinDelay"
ATTR_COOL_INTERSTAGE_MIN_DELAY = "coolInterstageMinDelay"
ATTR_BACK_LIGHT = "backlight"
ATTR_HEAT_COOL = "heatCoolMode"
ATTR_VALVE_POLARITY = "reversingValvePolarity"
ATTR_HUMIDIFIER_TYPE = "humidifierType"
ATTR_COOL_CYCLE_LENGTH = "coolCycleLength"
ATTR_HEATCOOL_SETPOINT_MIN_DELTA = "heatCoolSetpointMinDelta"
ATTR_TEMP_OFFSET_HEAT = "temperatureOffsetHeat"
ATTR_COOL_MIN_TIME_ON = "coolMinTimeOn"
ATTR_COOL_MIN_TIME_OFF = "coolMinTimeOff"
ATTR_WATER_TEMP_PROTEC = "waterTempProtectionType"
ATTR_OUTPUT_CONNECT_STATE = "bulkOutputConnectedState"
ATTR_HEAT_INSTALL_TYPE = "heatInstallationType"
ATTR_HUMIDITY = "humidity"
ATTR_ACCESSORY_TYPE = "accessoryType"
ATTR_HUMID_SETPOINT_OFFSET = "humiditySetpointOffset"
ATTR_HUMID_SETPOINT_MODE = "humiditySetpointMode"
ATTR_AIR_EX_MIN_TIME_ON = "airExchangerMinTimeOn"
ATTR_HC_LOCK_STATUS = "heatCoolLockoutStatus"
ATTR_DRAUXCONF = "drAuxConfig"
ATTR_DRFANCONF = "drFanSpeedConfig"
ATTR_DRACCESORYCONF = "drAccessoryConfig"
ATTR_DRAIR_CURT_CONF = "drAirCurtainConfig"
ATTR_INTERLOCK_ID = "interlockUniqueId"
ATTR_HEAT_PURGE_TIME = "heatPurgeTime"
ATTR_COOL_PURGE_TIME = "coolPurgeTime"
ATTR_AIR_CONFIG = "airCurtainConfig"
ATTR_AIR_ACTIVATION_TEMP = "airCurtainActivationTemperature"
ATTR_AIR_MAX_POWER_TEMP = "airCurtainMaxPowerTemperature"
ATTR_AUX_HEAT_MIN_TIMEOFF = "auxHeatMinTimeOff"
ATTR_HEAT_MIN_TIME_ON = "heatMinTimeOn"
ATTR_HEAT_MIN_TIME_OFF = "heatMinTimeOff"

WATT_ATTRIBUTES = [
    ATTR_ROOM_TEMPERATURE,
    ATTR_PHASE_CONTROL,
    ATTR_KEY_DOUBLE_UP,
    ATTR_WATTAGE_INSTANT,
    ATTR_ERROR_CODE_SET1,
    ATTR_WATTAGE_OVERRIDE,
    ATTR_WIFI_WATTAGE,
    ATTR_WIFI_WATT_NOW,
    ATTR_WATTAGE,
    ATTR_KEYPAD,
    ATTR_BACKLIGHT,
    ATTR_SYSTEM_MODE,
    ATTR_CYCLE,
    ATTR_DISPLAY2,
    ATTR_RSSI,
]

ALL_ATTRIBUTES = [ATTR_ALERT, ATTR_SIGNATURE, ATTR_POWER_MODE, ATTR_MODE, ATTR_ONOFF, ATTR_ONOFF2, ATTR_INTENSITY, ATTR_INTENSITY_MIN, ATTR_WATTAGE, ATTR_WATTAGE_INSTANT, ATTR_WATTAGE_OVERRIDE, ATTR_SETPOINT_MODE, ATTR_ROOM_SETPOINT, ATTR_ROOM_SETPOINT_AWAY,
                  ATTR_ROOM_TEMPERATURE, ATTR_OUTPUT_PERCENT_DISPLAY, ATTR_ROOM_SETPOINT_MIN, ATTR_ROOM_SETPOINT_MAX, ATTR_GFCI_STATUS, ATTR_GFCI_ALERT, ATTR_WATER_LEAK_STATUS, ATTR_WATER_LEAK_ALARM_STATUS, ATTR_WATER_LEAK_DISCONECTED_STATUS, ATTR_POWER_SUPPLY,
                  ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_BATTERY_TYPE, ATTR_FLOOR_MODE, ATTR_FLOOR_OUTPUT2, ATTR_FLOOR_AUX, ATTR_KEYPAD, ATTR_OCCUPANCY, ATTR_FLOOR_OUTPUT1, ATTR_LIGHT_WATTAGE, ATTR_OUTPUT1, ATTR_WIFI_WATTAGE, ATTR_WIFI_WATT_NOW, ATTR_WIFI,
                  ATTR_RSSI, ATTR_DISPLAY2, ATTR_WIFI_KEYPAD, ATTR_TIMER, ATTR_TIMER2, ATTR_DRSTATUS, ATTR_BACKLIGHT, ATTR_BACKLIGHT_AUTO_DIM, ATTR_LED_ON_INTENSITY, ATTR_LED_OFF_INTENSITY, ATTR_LED_ON_COLOR, ATTR_LED_OFF_COLOR, ATTR_STATE, ATTR_RED, ATTR_GREEN,
                  ATTR_BLUE, ATTR_TIME, ATTR_TEMP, ATTR_MOTOR_POS, ATTR_TEMP_ALARM, ATTR_LOW_TEMP_STATUS, ATTR_TEMPERATURE, ATTR_WATER_TEMPERATURE, ATTR_ROOM_TEMP_ALARM, ATTR_VALVE_CLOSURE, ATTR_LEAK_ALERT, ATTR_BATT_ALERT, ATTR_TEMP_ALERT, ATTR_FUEL_ALERT,
                  ATTR_REFUEL, ATTR_FUEL_PERCENT_ALERT, ATTR_CONF_CLOSURE, ATTR_MOTOR_TARGET, ATTR_FLOOR_AIR_LIMIT, ATTR_FLOOR_MAX, ATTR_FLOOR_MIN, ATTR_ROOM_TEMP_DISPLAY, ATTR_EARLY_START, ATTR_FLOOR_SENSOR, ATTR_AUX_CYCLE, ATTR_CYCLE, ATTR_CYCLE_OUTPUT2,
                  ATTR_PUMP_PROTEC, ATTR_PUMP_PROTEC_DURATION, ATTR_PUMP_PROTEC_PERIOD, ATTR_TYPE, ATTR_PHASE_CONTROL, ATTR_SYSTEM_MODE, ATTR_DRSETPOINT, ATTR_DRACTIVE, ATTR_OPTOUT, ATTR_SETPOINT, ATTR_INPUT_STATUS, ATTR_INPUT2_STATUS, ATTR_EXT_TEMP, ATTR_STATUS,
                  ATTR_ERROR_CODE_SET1, ATTR_FLOW_METER_CONFIG, ATTR_VALVE_INFO, ATTR_STM8_ERROR, ATTR_TANK_SIZE, ATTR_CONTROLLED_DEVICE, ATTR_COLD_LOAD_PICKUP_STATUS, ATTR_KEY_DOUBLE_UP, ATTR_ANGLE, ATTR_SAMPLING, ATTR_TANK_TYPE, ATTR_TANK_HEIGHT, ATTR_TANK_PERCENT,
                  ATTR_GAUGE_TYPE, ATTR_COOL_SETPOINT, ATTR_COOL_SETPOINT_MIN, ATTR_COOL_SETPOINT_MAX, ATTR_WATER_TEMP_MIN, ATTR_MIN_WATER_TEMP, ATTR_WATT_TIME_ON, ATTR_DR_WATER_TEMP_TIME, ATTR_WATER_TEMP_TIME, ATTR_FLOW_ALARM1, ATTR_FLOW_ALARM2, ATTR_AWAY_ACTION,
                  ATTR_FLOW_ENABLED, ATTR_FLOW_MODEL_CONFIG, ATTR_FLOW_ALARM_TIMER, ATTR_FLOW_THRESHOLD, ATTR_FLOW_ALARM1_LENGHT, ATTR_FLOW_ALARM1_PERIOD, ATTR_FLOW_ALARM1_OPTION, ATTR_DR_PROTEC_STATUS, ATTR_LEG_PROTEC_STATUS, ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
                  ATTR_COLD_LOAD_PICKUP_TEMP, ATTR_TEMP_ACTION_LOW, ATTR_BATT_ACTION_LOW, ATTR_NAME_1, ATTR_NAME_2, ATTR_OUTPUT_NAME_1, ATTR_OUTPUT_NAME_2, ATTR_WATER_TANK_ON, ATTR_HEAT_LOCK_TEMP, ATTR_COOL_LOCK_TEMP, ATTR_AVAIL_MODE, ATTR_FAN_SPEED, ATTR_FAN_CAP,
                  ATTR_FAN_SWING_VERT, ATTR_FAN_SWING_HORIZ, ATTR_FAN_SWING_CAP, ATTR_FAN_SWING_CAP_HORIZ, ATTR_FAN_SWING_CAP_VERT, ATTR_DISPLAY_CONF, ATTR_DISPLAY_CAP, ATTR_MODEL, ATTR_SOUND_CONF, ATTR_SOUND_CAP, ATTR_LANGUAGE, ATTR_MODE, ATTR_HC_DEV, ATTR_BALANCE_PT,
                  ATTR_BALANCE_PT_TEMP_LOW, ATTR_BALANCE_PT_TEMP_HIGH, ATTR_BATT_PERCENT_NORMAL, ATTR_BATT_STATUS_NORMAL, ATTR_BATT_INFO, ATTR_INPUT_1_ON_DELAY, ATTR_INPUT_2_ON_DELAY, ATTR_INPUT_1_OFF_DELAY, ATTR_INPUT_2_OFF_DELAY, ATTR_VALUE, ATTR_ACTIVE,
                  ATTR_ONOFF_NUM, ATTR_CLOSE_VALVE, ATTR_TRIGGER_ALARM, ATTR_DELAY, ATTR_INPUT_NUMBER, ATTR_COLD_LOAD_PICKUP, ATTR_HEAT_LOCKOUT_TEMP, ATTR_OCCUPANCY_SENSOR_DELAY, ATTR_LEAK_CLOSURE_CONFIG, ATTR_HUMID_DISPLAY, ATTR_HUMID_SETPOINT, ATTR_DUAL_STATUS,
                  ATTR_HEAT_SOURCE_TYPE, ATTR_AUX_HEAT_SOURCE_TYPE, ATTR_COOL_SETPOINT_AWAY, ATTR_FAN_FILTER_REMAIN, ATTR_AUX_HEAT_TIMEON, ATTR_AUX_HEAT_START_DELAY, ATTR_HEAT_INTERSTAGE_MIN_DELAY, ATTR_COOL_INTERSTAGE_MIN_DELAY, ATTR_BACK_LIGHT, ATTR_HEAT_COOL,
                  ATTR_VALVE_POLARITY, ATTR_HUMIDIFIER_TYPE, ATTR_COOL_CYCLE_LENGTH, ATTR_HEATCOOL_SETPOINT_MIN_DELTA, ATTR_TEMP_OFFSET_HEAT, ATTR_COOL_MIN_TIME_ON, ATTR_COOL_MIN_TIME_OFF, ATTR_WATER_TEMP_PROTEC, ATTR_OUTPUT_CONNECT_STATE, ATTR_HEAT_INSTALL_TYPE,
                  ATTR_HUMIDITY, ATTR_ACCESSORY_TYPE, ATTR_HUMID_SETPOINT_OFFSET, ATTR_HUMID_SETPOINT_MODE, ATTR_AIR_EX_MIN_TIME_ON, ATTR_HC_LOCK_STATUS, ATTR_DRAUXCONF, ATTR_DRFANCONF, ATTR_DRACCESORYCONF, ATTR_DRAIR_CURT_CONF, ATTR_INTERLOCK_ID, ATTR_HEAT_PURGE_TIME,
                  ATTR_COOL_PURGE_TIME, ATTR_AIR_CONFIG, ATTR_AIR_ACTIVATION_TEMP, ATTR_AIR_MAX_POWER_TEMP, ATTR_AUX_HEAT_MIN_TIMEOFF, ATTR_HEAT_MIN_TIME_ON, ATTR_HEAT_MIN_TIME_OFF]


class NeviwebTemperature:

    def __init__(
            self,
            hass=None,
            username=NEVIWEB_EMAIL,
            password=NEVIWEB_PASSWORD,
            network=None,
            network2=None,
            network3=None,
            ignore_miwi=None,
            timeout=REQUESTS_TIMEOUT
    ):
        log.info('      ----------------------- Starting NeviwebTemperature -----------------------')
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

    def get_device_hourly_stats(self, device_id) -> list[dict[str, int]] | None:
        """Get device power consumption (in Wh) for the last 24 hours."""
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
        # log.info(f'get_device_hourly_stats: {data}')
        if "history" in data:
            return data["history"]
        else:
            log.error(f"Hourly stat error: {data}")
            return None

    def load_neviweb(self, result_queue: Queue):
        log.info("  ----------------------- Start load_neviweb -----------------------")
        result: dict = {}
        try:
            log.info(f'login={self.login()}')

            self.get_network()
            # log.info(f'get_network: {self._network_name}')
            self.get_gateway_data()
            # log.info(f'gateway_data: {self.gateway_data}')
            self.get_groups()
            # log.info(f"get_groups: {self.groups}")

            for device in self.gateway_data:
                columns = WATT_ATTRIBUTES
                data: dict[str, Any] = self.get_device_attributes(device["id"], columns)
                for name in columns:
                    device[name] = data.get(name)['value'] if data.get(name) and type(data.get(name)) == dict and data.get(name).get('value') else None

            kwh_total = 0.0
            for device in self.gateway_data:
                device_hourly_stats_list: list[dict[str, int]] | None = self.get_device_hourly_stats(device['id'])
                for group in self.groups:
                    if group['id'] == device['group$id']:
                        kwh: float = round(device_hourly_stats_list[len(device_hourly_stats_list) - 1]["period"] / 1000, 3)
                        kwh_total += kwh
                        result[f'kwh_{str(group['name']).replace(' ', '-').lower()}'] = kwh
            log.info(f'kwh_neviweb: {kwh_total}')
            result['kwh_neviweb'] = kwh_total

            room_temperature_display_list: list = [float(gateway_data2['roomTemperature']) for gateway_data2 in self.gateway_data]
            int_temp: float = round(sum(room_temperature_display_list) / len(room_temperature_display_list), 1)
            log.info(f'int_temp={int_temp}, data={room_temperature_display_list}')

            for device in self.gateway_data:
                for group in self.groups:
                    if group['id'] == device['group$id']:
                        result[f'int_temp_{str(group['name']).replace(' ', '-').lower()}'] = device['roomTemperature']
                        log.info(f'{group['name']}: {device["roomTemperature"]}°C, {round(device_hourly_stats_list[len(device_hourly_stats_list) - 1]["period"] / 1000, 3)}KWh')
            result.update({'int_temp': int_temp})
            result.update({'room_temperature_display_list': room_temperature_display_list})
            log.info(f'result={result}')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        finally:
            log.info(f'logout={self.logout()}')
            result_queue.put(result)

    def login(self):
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
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

        if raw_res and raw_res.status_code != 200:
            log.info("Login status: %s", raw_res.json())
            raise Exception("Cannot log in")

            # Update session
        self._cookies = raw_res.cookies
        data: any = raw_res.json()
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
            log.error("Account ID is empty check your username and passord to log into Neviweb...")
        else:
            try:
                raw_res = requests.get(
                    f'https://neviweb.com/api/groups?location$id={self.gateway_data[0]["location$id"]}',
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                self.groups = raw_res.json()
                # log.info(f'Groups: {self.groups}')
                # log.info("Number of groups found on Neviweb: %s", len(self.groups))
                # log.info("Updated groups data: %s", json.dumps(self.groups, indent=4))
            except OSError:
                raise Exception("Cannot get Neviweb's groups")

    def get_network(self):
        """Get gateway id associated to the desired network."""
        # Http requests
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
                log.info("Number of networks found on Neviweb: %s", len(networks))
                # log.info("networks: %s", networks)
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
                        log.info(f"Selecting {self._network_name2} as second network")
                        if len(networks) > 2:
                            self._gateway_id3 = networks[2]["id"]
                            self._network_name3 = networks[2]["name"]
                            log.info(f"Selecting {self._network_name3} as third network")
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
        except OSError:
            raise Exception("Cannot get gateway data")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        self.gateway_data = raw_res.json()
        # log.info(f"Received gateway data:\n{json.dumps(self.gateway_data, indent=4, sort_keys=True, default=str)}")
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

        # for i in range(len(self.gateway_data)):
        #     data = self.groups[i]
        #     self.gateway_data[i]['displayName'] = self.groups[i]['name']

        # for device in self.gateway_data:
        #     columns = WATT_ATTRIBUTES
        #     data: dict[str, Any] = self.get_device_attributes(device["id"], columns)
        #     for name in columns:
        #         device[name] = data.get(name)['value'] if data.get(name) and type(data.get(name)) == dict and data.get(name).get('value') else None
        #     log.info(f"Received '{device['displayName']}': {data}")
        # log.info(f"Received '{device['displayName']}': {json.dumps(data, indent=4, sort_keys=True, default=str)}")
        # if self._gateway_id2 is not None:
        #     for device in self.gateway_data2:
        #         data2 = self.get_device_attributes(device["id"], ALL)
        #         if ATTR_ROOM_TEMP_DISPLAY in data2:
        #             device[ATTR_ROOM_TEMP_DISPLAY] = data2[ATTR_ROOM_TEMP_DISPLAY]
        #         log.info("Received signature data: %s", data2)
        #
        # if self._gateway_id3 is not None:
        #     for device in self.gateway_data3:
        #         data3 = self.get_device_attributes(device["id"], ALL)
        #         if ATTR_ROOM_TEMP_DISPLAY in data3:
        #             device[ATTR_ROOM_TEMP_DISPLAY] = data3[ATTR_ROOM_TEMP_DISPLAY]
        #         log.info("Received signature data: %s", data3)

    def get_device_attributes(self, device_id, attributes):
        """Get device attributes."""
        # Prepare return
        data = {}
        # Http requests
        try:
            # log.info(attributes)
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
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        # log.info(f"Received devices data: \n{json.dumps(data, indent=4, sort_keys=True, default=str)}")
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                log.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
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

    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    neviweb_temperature: NeviwebTemperature = NeviwebTemperature()
    neviweb_temperature.load_neviweb(result_queue)
    while not result_queue.empty():
        print(result_queue.get())
