from colorama import *
from datetime import datetime
from fake_useragent import FakeUserAgent
from faker import Faker
from time import sleep
import json
import os
import random
import re
import requests
import sys
import tzlocal

class Tomarket:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.faker = Faker()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'api-web.tomarket.ai',
            'Origin': 'https://mini-app.tomarket.ai',
            'Pragma': 'no-cache',
            'Referer': 'https://mini-app.tomarket.ai/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now(tzlocal.get_localzone()).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    def user_login(self, queries):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/login'
        accounts = []
        for query in queries:
            if not query:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Empty Query Found, Skipping... ]{Style.RESET_ALL}")
                continue
            data = json.dumps({'init_data':query,'invite_code':'0000cYQe','from':'','is_bot':False})
            self.headers.update({
                'Content-Length': str(len(data)),
                'Content-Type': 'application/json'
            })
            try:
                response = self.session.post(url=url, headers=self.headers, data=data)
                response.raise_for_status()
                data = response.json()
                access_token = data['data']['access_token']
                first_name = data['data']['fn']
                if not first_name:
                    first_name = self.faker.first_name()
                accounts.append({
                    'first_name': first_name,
                    'token': access_token
                })
            except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
                self.print_timestamp(
                    f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}"
                )
        return accounts

    def process_queries(self, lines_per_file=10):
        if not os.path.exists('queries.txt'):
            raise FileNotFoundError(f"File 'queries.txt' Not Found. Please Ensure It Exists")

        with open('queries.txt', 'r') as f:
            queries = [line.strip() for line in f if line.strip()]

        if not queries:
            raise ValueError("File 'queries.txt' Is Empty")

        account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
        if account_files:
            account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
        else:
            account_files = []

        for account_file in account_files:
            with open(account_file, 'r') as file:
                accounts_data = json.load(file)
                accounts = accounts_data.get('accounts', [])

            if len(accounts) < 10:
                remaining_slots = 10 - len(accounts)
                chunk = queries[:remaining_slots]
                new_accounts = self.user_login(chunk)
                accounts.extend(new_accounts)
                accounts_data['accounts'] = accounts

                with open(account_file, 'w') as outfile:
                    json.dump(accounts_data, outfile, indent=4)

                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Updated '{account_file}' With {len(new_accounts)} New Token And Name ]{Style.RESET_ALL}")

                queries = queries[remaining_slots:]

                if len(queries) == 0:
                    break

        last_file_number = int(re.findall(r'\d+', account_files[-1])[0]) if account_files else 0

        for i in range(0, len(queries), lines_per_file):
            chunk = queries[i:i + lines_per_file]
            file_index = last_file_number + 1
            accounts_file = f"accounts-{file_index}.json"

            accounts = self.user_login(chunk)

            with open(accounts_file, 'w') as outfile:
                json.dump({'accounts': accounts}, outfile, indent=4)

            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Generated Tokens In '{accounts_file}' ]{Style.RESET_ALL}")
            last_file_number += 1

    def load_accounts_from_file(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)['accounts']

    def claim_daily(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        data = json.dumps({'game_id':'fa873d13-d831-4d6f-8aee-9cff7a1d0db1'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_daily = response.json()
            if 'status' in claim_daily:
                if claim_daily['status'] == 0:
                    self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Daily Claimed ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Points {claim_daily['data']['today_points']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Day {claim_daily['data']['today_game']} ]{Style.RESET_ALL}"
                    )
                elif claim_daily['status'] == 400 and claim_daily['message'] == 'already_check':
                    self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_daily['message']}' Status '{claim_daily['status']}' In Daily Claim ]{Style.RESET_ALL}")
            elif 'code' in claim_daily:
                if claim_daily['code'] == 400 and claim_daily['message'] == 'claim throttle':
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Daily Claim Throttle ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_daily['message']}' Code '{claim_daily['status']}' In Daily Claim ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Daily Claim ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")

    def balance_user(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        self.headers.update({
            'Authorization': token,
            'Content-Length': '0'
        })
        response = self.session.post(url=url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def start_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            start_farm = response.json()
            if start_farm['status'] == 0:
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Started ]{Style.RESET_ALL}")
                now = datetime.now(tzlocal.get_localzone())
                farm_end_at = datetime.fromtimestamp(start_farm['data']['end_at'], tzlocal.get_localzone())
                if now >= farm_end_at:
                    self.claim_farm(token=token)
                else:
                    timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
            elif start_farm['status'] == 500 and start_farm['message'] == 'game already started':
                now = datetime.now(tzlocal.get_localzone())
                farm_end_at = datetime.fromtimestamp(start_farm['data']['end_at'], tzlocal.get_localzone())
                if now >= farm_end_at:
                    self.claim_farm(token=token)
                else:
                    timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
            elif start_farm['status'] == 500 and start_farm['message'] == 'game end need claim':
                self.claim_farm(token=token)
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{start_farm['message']}' Status '{start_farm['status']}' In Start Farm ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Farm: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Start Farm: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Farm: {str(e)} ]{Style.RESET_ALL}")

    def claim_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_farm = response.json()
            if 'status' in claim_farm:
                if claim_farm['status'] == 0:
                    self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Farm Claimed {claim_farm['data']['points']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Starting Farm ]{Style.RESET_ALL}"
                    )
                    self.start_farm(token=token)
                elif claim_farm['status'] == 500 and claim_farm['message'] == 'farm not started or claimed':
                    self.print_timestamp(
                        f"{Fore.RED + Style.BRIGHT}[ Farm Not Started ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Starting Farm ]{Style.RESET_ALL}"
                    )
                    self.start_farm(token=token)
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_farm['message']}' Status '{claim_farm['status']}' In Claim Farm Data ]{Style.RESET_ALL}")
            elif 'code' in claim_farm:
                if claim_farm['code'] == 400 and claim_farm['message'] == 'claim throttle':
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Farm Throttle ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_farm['message']}' Code '{claim_farm['status']}' In Claim Farm ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Claim Farm ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Farm: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Farm: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Farm: {str(e)} ]{Style.RESET_ALL}")

    def play_game(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        while True:
            try:
                response = self.session.post(url=url, headers=self.headers, data=data)
                response.raise_for_status()
                play_game = response.json()
                if play_game['status'] == 0:
                    self.print_timestamp(
                        f"{Fore.YELLOW + Style.BRIGHT}[ Game Started ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Please Wait 30 Seconds ]{Style.RESET_ALL}"
                    )
                    sleep(30 + random.randint(3, 5))
                    self.claim_game(token=token, points=random.randint(6000, 6001))
                elif play_game['status'] == 500 and play_game['message'] == 'no chance':
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No Chance To Start Game ]{Style.RESET_ALL}")
                    break
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{play_game['message']}' Status '{play_game['status']}' In Play Game ]{Style.RESET_ALL}")
                    break
            except requests.HTTPError as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
                break
            except requests.RequestException as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
                break
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
                break

    def claim_game(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d','points':points})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_game = response.json()
            if 'status' in claim_game:
                if claim_game['status'] == 0:
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {claim_game['data']['points']} ]{Style.RESET_ALL}")
                elif claim_game['status'] == 500 and claim_game['message'] == 'game not start':
                    self.print_timestamp(
                        f"{Fore.RED + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Starting Game ]{Style.RESET_ALL}"
                    )
                    self.play_game(token=token)
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Status '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
            elif 'code' in claim_game:
                if claim_game['code'] == 400 and claim_game['message'] == 'claim throttle':
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Game Throttle ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Code '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Claim Game ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")

    def list_tasks(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        data = json.dumps({'language_code':'en'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            list_tasks = response.json()
            current_time = datetime.now()
            for category in list_tasks['data']:
                for task in list_tasks['data'][category]:
                    end_time = datetime.strptime(task.get('endTime'), '%Y-%m-%d %H:%M:%S') if task.get('endTime') else None
                    if (
                        (end_time and end_time < current_time) or
                        ('walletAddress' in task['handleFunc'] or 'boost' in task['handleFunc'] or 'checkInvite' in task['handleFunc']) or
                        ('classmate' in task['tag']) or
                        ('classmate' in task['type'].lower())
                    ): continue
                    wait_second = task.get('waitSecond', 0)
                    if task['status'] == 0 and task['type'] == "mysterious":
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                        self.claim_tasks(token=token, task_id=task['taskId'], task_title=task['title'])
                    elif task['status'] == 0:
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting {task['title']} ]{Style.RESET_ALL}")
                        self.start_tasks(token=token, task_id=task['taskId'], task_title=task['title'], task_waitsecond=wait_second)
                    elif task['status'] == 1:
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Checking {task['title']} ]{Style.RESET_ALL}")
                        self.check_tasks(token=token, task_id=task['taskId'], task_title=task['title'])
                    elif task['status'] == 2:
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                        self.claim_tasks(token=token, task_id=task['taskId'], task_title=task['title'])
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")

    def start_tasks(self, token: str, task_id: int, task_title: str, task_waitsecond: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            start_tasks = response.json()
            if start_tasks['status'] == 0:
                if start_tasks['data']['status'] == 1:
                    sleep(task_waitsecond + random.randint(3, 5))
                    self.check_tasks(token=token, task_id=task_id, task_title=task_title)
                elif start_tasks['data']['status'] == 2:
                    self.claim_tasks(token=token, task_id=task_id, task_title=task_title)
            elif start_tasks['status'] == 500 and start_tasks['message'] == 'Handle user\'s task error':
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Finish {task_title} By Itself ]{Style.RESET_ALL}")
            elif start_tasks['status'] == 500 and start_tasks['message'] == 'Task handle is not exist':
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Exist ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{start_tasks['message']}' Status '{start_tasks['status']}' In Start Tasks ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")

    def check_tasks(self, token: str, task_id: int, task_title: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/check'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            check_tasks = response.json()
            if check_tasks['status'] == 0:
                if check_tasks['data']['status'] == 1:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Still Have Not Finished ]{Style.RESET_ALL}")
                elif check_tasks['data']['status'] == 2:
                    self.claim_tasks(token=token, task_id=task_id, task_title=task_title)
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{check_tasks['message']}' Status '{check_tasks['status']}' In Check Tasks ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")

    def claim_tasks(self, token: str, task_id: int, task_title: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_tasks = response.json()
            if claim_tasks['status'] == 0:
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ {task_title} Claimed ]{Style.RESET_ALL}")
            elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t start this task':
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Have Not Start {task_title} ]{Style.RESET_ALL}")
            elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t finished this task':
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Have Not Finished {task_title} ]{Style.RESET_ALL}")
            elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'Task is not within the valid time':
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Within The Valid Time ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_tasks['message']}' Status '{claim_tasks['status']}' In Claim Tasks ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    def main(self, accounts):
        while True:
            try:
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}")
                for account in accounts:
                    self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}")
                    self.claim_daily(token=account['token'])
                    balance = self.balance_user(token=account['token'])
                    self.print_timestamp(
                        f"{Fore.YELLOW + Style.BRIGHT}[ Balance {balance['data']['available_balance']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {balance['data']['play_passes']} ]{Style.RESET_ALL}"
                    )
                    if 'farming' in balance['data']:
                        now = datetime.now(tzlocal.get_localzone())
                        farm_end_at = datetime.fromtimestamp(balance['data']['farming']['end_at'], tzlocal.get_localzone())
                        if now >= farm_end_at:
                            self.claim_farm(token=account['token'])
                        else:
                            timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
                    else:
                        self.start_farm(token=account['token'])
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Home/Play Passes ]{Style.RESET_ALL}")
                for account in accounts:
                    self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}")
                    self.play_game(token=account['token'])
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}")
                for account in accounts:
                    self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}")
                    self.list_tasks(token=account['token'])
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting Soon ]{Style.RESET_ALL}")
                sleep(3 * 3600)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        init(autoreset=True)

        tomarket = Tomarket()

        account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
        account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

        tomarket.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Select an option ]{Style.RESET_ALL}")
        tomarket.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 1 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Generate Tokens ]{Style.RESET_ALL}"
        )
        tomarket.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 2 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Use Existing accounts-*.json ]{Style.RESET_ALL}"
        )

        initial_choice = int(input(
            f"{Fore.CYAN + Style.BRIGHT}[ Enter The Number Corresponding To Your Choice ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        ))
        if initial_choice == 1:
            tomarket.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Processing Queries to Generate Tokens ]{Style.RESET_ALL}")
            tomarket.process_queries()
            tomarket.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Token Generation Completed ]{Style.RESET_ALL}")

            account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
            account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

            if not account_files:
                raise FileNotFoundError("No 'accounts-*.json' Files Found In The Directory. Please Generate Tokens First By Selecting Option 1.")
        elif initial_choice == 2:
            if not account_files:
                raise FileNotFoundError("No 'accounts-*.json' Files Found In The Directory. Please Generate Tokens First By Selecting Option 1.")
        else:
            raise ValueError("Invalid Initial Choice. Please Run The Script Again And Choose A Valid Option")

        tomarket.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Select The Accounts File To Use ]{Style.RESET_ALL}")
        for i, accounts_file in enumerate(account_files, start=1):
            tomarket.print_timestamp(
                f"{Fore.MAGENTA + Style.BRIGHT}[ {i} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.CYAN + Style.BRIGHT}[ {accounts_file} ]{Style.RESET_ALL}"
            )

        choice = int(input(
            f"{Fore.CYAN + Style.BRIGHT}[ Enter The Number Corresponding To The File You Want To Use ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        )) - 1
        if choice < 0 or choice >= len(account_files):
            raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

        selected_accounts_file = account_files[choice]
        accounts = tomarket.load_accounts_from_file(selected_accounts_file)

        tomarket.main(accounts)
    except (ValueError, IndexError, FileNotFoundError) as e:
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ See You ]{Style.RESET_ALL}")
        sys.exit(0)