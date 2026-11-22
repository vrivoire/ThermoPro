# https://services-cl.solutions.hydroquebec.com/lsw/portail/fr/group/clientele/portrait-de-consommation/resourceObtenirDonneesConsommationHoraires?date=2025-09-24&_=1758820938310
import asyncio
import email
import imaplib
import json
import math
import traceback
from collections.abc import Iterator
from datetime import datetime, timedelta, date
from email.message import Message
from io import StringIO
from queue import Queue
from time import sleep
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta
from hydroqc.consts import LoginStatus
from hydroqc.contract.common import Contract
from hydroqc.error import HydroQcHTTPError, HydroQcMFAInvalidCodeError
from hydroqc.types import ConsumpHourlyTyping
from hydroqc.types.consump import ConsumpHourlyResultTyping, ConsumpHourlyResultsTyping
from hydroqc.webuser import WebUser
from pandas import DataFrame
from pandas.io.parsers import TextFileReader

import thermopro
from constants import HYDRO_EMAIL, HYDRO_PASSWORD, GMAIL_SESSION_PATH, GOOGLE_EMAIL, GOOGLE_APP_PWD
from thermopro import log


class HydroQuébec:

    def __init__(self):
        log.info(' Starting HydroQuébec '.center(100, '*'))

    async def __get_kwh_list(self,
                             result_queue: Queue,
                             weeks=4
                             ) -> None:
        log.info(' Start get_kwh_list '.center(100, '*'))
        # https://pypi.org/project/Hydro-Quebec-API-Wrapper/
        web_user: WebUser = WebUser(HYDRO_EMAIL, HYDRO_PASSWORD, verify_ssl=False, log_level="ERROR", http_log_level="ERROR")
        kwh_dict: dict[str, float | None] = {}
        try:
            check_hq_portal_status: bool = await web_user.check_hq_portal_status()
            log.info(f'check_hq_portal_status: {check_hq_portal_status}')
            if check_hq_portal_status:
                status: LoginStatus = await self.__login(web_user)
                if status is LoginStatus.SUCCESS:
                    await web_user.get_info()
                    customer = web_user.customers[0]
                    await customer.get_info()
                    contract: Contract = web_user.customers[0].accounts[0].contracts[0]

                    try:
                        log.info(' get_hourly_energy '.center(100, '*'))

                        log.info(f'1 Date range: from: {(date.today() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}, to: {(date.today() - timedelta(days=1 + weeks * 7)).strftime('%Y-%m-%d %H:%M')}')
                        for days in range(1, weeks * 7):
                            try:
                                today_hourly_consumption = await contract.get_hourly_consumption(date.today() - timedelta(days=days))
                                if today_hourly_consumption.get('success'):
                                    await self.fill_kwh_dict(kwh_dict, today_hourly_consumption)
                            except HydroQcHTTPError as hqhe:
                                log.error(f'days: {days}, {hqhe}')
                            except Exception as ex:
                                log.error(ex)
                                log.error(traceback.format_exc())
                        log.info(f'Found {len(kwh_dict)} rows')

                        if len(kwh_dict) == 0:
                            log.warning('Retrying with get_hourly_energy')
                            start_date = datetime.now() - relativedelta(weeks=0)
                            end_date = datetime.now() - relativedelta(weeks=weeks)
                            log.info(f'2 Date range: from: {start_date.strftime('%Y-%m-%d %H:%M')}, to: {end_date.strftime('%Y-%m-%d %H:%M')}')
                            string: Iterator[list[str | int | float]] | StringIO = await contract.get_hourly_energy(start_date, end_date, raw_output=True)
                            df: DataFrame | TextFileReader = pd.read_csv(string, sep=";")
                            if len(df) == 0:
                                log.error('get_hourly_energy is empty.')
                            else:
                                log.info(f'Data parsed, from: {df.iloc[-1]['Date et heure']}, to: {df.iloc[0]['Date et heure']}, rows: {len(df)}')
                                df['Date et heure'].astype('datetime64[ns]')
                                df.set_index('Date et heure')
                                df_reversed = df[::-1].reset_index(drop=True)
                                df_reversed['Date et heure'].astype('datetime64[ns]')
                                df_reversed.set_index('Date et heure')
                                df_reversed = df_reversed.sort_values(by='Date et heure', ascending=True)

                                log.info('Creating kwh_dict...')
                                for index, row in df_reversed.iterrows():
                                    split = row['Date et heure'].split(' ')
                                    kwh: float = 0.0
                                    if type(row['kWh']) == str:
                                        kwh = float(str(row['kWh']).replace(',', '.'))
                                    elif type(row['kWh']) == float:
                                        kwh = float(row['kWh'])
                                    kwh_dict[f'{split[0]} {split[1][0:2]}'] = kwh if not math.isnan(kwh) else 0.0
                    except HydroQcHTTPError as hqhe:
                        log.error(hqhe)
                    except Exception as ex:
                        log.error(ex)
                        log.error(traceback.format_exc())

                    try:
                        log.info(' get_today_hourly_consumption '.center(100, '*'))
                        try:
                            today_hourly_consumption: ConsumpHourlyTyping = await contract.get_today_hourly_consumption()
                            await self.fill_kwh_dict(kwh_dict, today_hourly_consumption)
                        except HydroQcHTTPError as hqhe:
                            log.error(f'ERROR with contract.get_today_hourly_consumption(), using get_hourly_consumption, {hqhe}')
                    except HydroQcHTTPError as hqhe:
                        log.error(hqhe)
                        log.error(traceback.format_exc())
                    except Exception as ex:
                        log.error(ex)
                        log.error(traceback.format_exc())

                    kwh_dict = dict(sorted({key: value for key, value in kwh_dict.items() if value != 0.0}.items()))
                    log.info(f'Created kwh_dict, size: {len(kwh_dict)} from: {next(iter(kwh_dict))}, to: {next(reversed(kwh_dict.keys()))}') if len(kwh_dict) > 0 else None
                else:
                    log.error(f'Not ready, status: {status}')
            else:
                log.error(f'Not ready, check_hq_portal_status: {check_hq_portal_status}')
        except Exception as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            if web_user:
                await web_user.close_session()
                log.info('Session closed')
            result_queue.put({'kwh_dict': kwh_dict})
        log.info(' End get_kwh_list '.center(100, '*'))

    async def __login(self, web_user: WebUser) -> LoginStatus:
        log.info('Trying to login...')
        status: str = LoginStatus.FAILED
        try:
            with open(GMAIL_SESSION_PATH, "r", encoding="utf-8") as file:
                session = json.load(file)
                web_user.import_session_state(session)
                status = await web_user.try_silent_login()
                log.info(f'Logged in with session: {status}')
        except FileNotFoundError:
            log.info(f"The file '{GMAIL_SESSION_PATH}' does not exist.")
        except json.JSONDecodeError as e:
            log.error(f"The file '{GMAIL_SESSION_PATH}' is a invalid JSON format at line {e.lineno}, column {e.colno}: {e.msg}")

        log.info(f'Login status: {status}')
        if status is not LoginStatus.SUCCESS:
            try:
                log.warning('Logging in with MFA....')
                status = await web_user.login()
                while status is LoginStatus.MFA_REQUIRED:
                    code: str | None = self.__check_mfa_email()
                    # code = input("Verification code (empty = send a new one): ")
                    if code is not None and not code.strip():
                        await web_user.request_mfa_code()
                        continue
                    if code is not None:
                        try:
                            status = await web_user.submit_mfa_code(code)
                        except HydroQcMFAInvalidCodeError:
                            log.error("Code refused, try again.")
            except BaseException as exp:
                log.error(exp)
                log.error(traceback.format_exc())
                thermopro.send_email('HydroQuébecPower ERROR', f'{exp}\n{traceback.format_exc()}')
                raise exp

        if status is not LoginStatus.SUCCESS:
            raise RuntimeError("Login failed")

        state = web_user.export_session_state()
        with open(GMAIL_SESSION_PATH, 'w') as f:
            json.dump(state, f)

        log.info(f'state: {state}')
        log.info(f'Login: {status}')
        return status

    def __check_mfa_email(self) -> str | None:

        sleep(10)

        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        try:
            # Connect to Gmail's IMAP server
            imap.login(GOOGLE_EMAIL, GOOGLE_APP_PWD)
            imap.select("INBOX")

            # Search for all unread emails
            status, messages = imap.search(None, "UNSEEN")
            email_ids = messages[0].split()

            for email_id in email_ids:
                # Fetch the email by ID (Use '(BODY.PEEK[])' instead of '(RFC822)' to keep it unread)
                _, msg_data = imap.fetch(email_id, "(BODY.PEEK[])")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg: Message[str, str] = email.message_from_bytes(response_part[1])
                        sender: str | None = msg.get("From")
                        if sender is not None and 'hydro-quebec@communications.hydro.qc.ca' in sender:
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        parts = part.get_payload(decode=True).decode(errors="ignore").split("*")
                                        if len(parts) > 2:
                                            result = parts[1].replace("Code de vérification : ", "")
                                            log.info(f"Code de vérification : {result}")
                                            imap.store(email_id, "+FLAGS", "\\Seen")
                                            imap.store(email_id, "+FLAGS", "\\Deleted")
                                            imap.expunge()
                                            return result

        except BaseException as exp:
            log.error(exp)
            log.error(traceback.format_exc())
            raise exp
        finally:
            imap.close()
            imap.logout()

    async def fill_kwh_dict(self, kwh_dict: dict[str, float | int | None], today_hourly_consumption: ConsumpHourlyTyping | dict[str, bool | dict[Any, Any]]):
        if today_hourly_consumption.get('success'):
            crt: ConsumpHourlyResultsTyping = today_hourly_consumption.get('results')
            date_jour: str = crt.get('dateJour')
            liste_donnees_conso_energie_horaire: list[ConsumpHourlyResultTyping] = crt.get('listeDonneesConsoEnergieHoraire')
            # log.info(f'Got liste_donnees_conso_energie_horaire ({len(liste_donnees_conso_energie_horaire)} rows)')
            for ldceh in liste_donnees_conso_energie_horaire:
                kwh_dict[f'{date_jour} {ldceh.get('heure')[0:2]}'] = float(ldceh.get('consoTotal') if not math.isnan(ldceh.get('consoTotal')) else 0.0)
        else:

            log.error(f'today_hourly_consumption: {thermopro.ppretty(today_hourly_consumption)}')

    def start(self, result_queue: Queue):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.__get_kwh_list(result_queue))
        except BaseException as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            loop.close()


if __name__ == "__main__":
    thermopro.set_up(__file__)

    result_queue: Queue = Queue()
    HydroQuébec().start(result_queue)

    while not result_queue.empty():
        kwh_list: dict[str, dict[str, float | None]] = result_queue.get()
        # print(thermopro.ppretty(kwh_list))
        print(f'kwh_list: {len(kwh_list.get('kwh_dict'))}')
