from colorama import *
from datetime import datetime
from fake_useragent import FakeUserAgent
from time import sleep
import gc
import json
import os
import pytz
import random
import requests
import sys


class Tomarket:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'api-web.tomarket.ai',
            'Origin': 'https://mini-app.tomarket.ai',
            'Referer': 'https://mini-app.tomarket.ai/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message, timezone='Asia/Jakarta'):
        local_tz = pytz.timezone(timezone)
        now = datetime.now(local_tz)
        timestamp = now.strftime(f'%x %X %Z')
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {timestamp} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    def daily_claim(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        data = json.dumps({'game_id': 'fa873d13-d831-4d6f-8aee-9cff7a1d0db1'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        daily_claim = response.json()
        if 'status' in daily_claim:
            if daily_claim['status'] in [0, 200]:
                self.print_timestamp(
                    f"{Fore.GREEN + Style.BRIGHT}[ Daily Claimed ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}[ Points {daily_claim['data']['today_points']} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Day {daily_claim['data']['today_game']} ]{Style.RESET_ALL}"
                )
            elif daily_claim['status'] == 400 or daily_claim['message'] == 'already_check':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Daily Claim ]{Style.RESET_ALL}")
        elif 'code' in daily_claim:
            if daily_claim['code'] == 400 or daily_claim['message'] == 'claim throttle':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Daily Claim Throttle ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Daily Claim ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Daily Claim ]{Style.RESET_ALL}")

    def user_balance(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        self.headers.update({
            'Authorization': token,
            'Content-Length': '0'
        })
        response = self.session.post(url=url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def farm_start(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        data = json.dumps({'game_id': '53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        farm_start = response.json()
        if 'status' in farm_start:
            if farm_start['status'] == 0:
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Started ]{Style.RESET_ALL}")
                farm_end_at = datetime.fromtimestamp(farm_start['data']['end_at'], pytz.timezone('Asia/Jakarta'))
                timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
            elif farm_start['status'] == 500 or farm_start['message'] == 'game already started':
                self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Farm Already Started ]{Style.RESET_ALL}")
                farm_end_at = datetime.fromtimestamp(farm_start['data']['end_at'], pytz.timezone('Asia/Jakarta'))
                timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Farm Start ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Farm Start ]{Style.RESET_ALL}")

    def farm_claim(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        data = json.dumps({'game_id': '53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        farm_claim = response.json()
        if 'status' in farm_claim:
            if farm_claim['status'] == 0:
                self.print_timestamp(
                    f"{Fore.GREEN + Style.BRIGHT}[ Farm Claimed {farm_claim['data']['points']} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Starting Farm ]{Style.RESET_ALL}"
                )
                self.farm_start(token=token)
            elif farm_claim['status'] == 500 or farm_claim['message'] == 'farm not started or claimed':
                self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Farm Not Started ]{Style.RESET_ALL}")
                self.farm_start(token=token)
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Farm Claim ]{Style.RESET_ALL}")
        elif 'code' in farm_claim:
            if farm_claim['code'] == 400 or farm_claim['message'] == 'claim throttle':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Claim Throttle ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Farm Claim ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Farm Claim ]{Style.RESET_ALL}")

    def game_play(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        data = json.dumps({'game_id': '59bcd12e-04e2-404c-a172-311a0084587d'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        game_play = response.json()
        if 'status' in game_play:
            if game_play['status'] == 0:
                self.print_timestamp(
                    f"{Fore.GREEN + Style.BRIGHT}[ Game Started ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Please Wait 30 Seconds ]{Style.RESET_ALL}"
                )
                sleep(33)
                self.game_claim(token=token, points=random.randint(6000, 6001))
            elif game_play['status'] == 500 or game_play['message'] == 'no chance':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No Chance To Start Game ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Game Play ]{Style.RESET_ALL}")

    def game_claim(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        data = json.dumps({
            'game_id': '59bcd12e-04e2-404c-a172-311a0084587d',
            'points': points
        })
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        game_claim = response.json()
        if 'status' in game_claim:
            if game_claim['status'] == 0:
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {game_claim['data']['points']} ]{Style.RESET_ALL}")
            elif game_claim['status'] == 500 or game_claim['message'] == 'game not start':
                self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Game Not Started ]{Style.RESET_ALL}")
                self.game_play(token=token)
        elif 'code' in game_claim:
            if game_claim['code'] == 400 or game_claim['message'] == 'claim throttle':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Claim Throttle ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Game Claim ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Game Claim ]{Style.RESET_ALL}")

    def tasks_list(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        data = json.dumps({'language_code': 'en'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        tasks_list = response.json()
        for category in tasks_list['data']:
            for task in tasks_list['data'][category]:
                if 'endTime' in task and task['endTime']:
                        end_time = datetime.strptime(task['endTime'], '%Y-%m-%d %H:%M:%S')
                        if end_time < datetime.now():
                            continue
                if task['status'] == 0 and task['type'] == "mysterious":
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                    self.tasks_claim(token=token, task_id=task['taskId'])
                elif task['status'] == 0:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting {task['title']} ]{Style.RESET_ALL}")
                    start_task = self.tasks_start(token=token, task_id=task['taskId'])
                    if start_task['status'] == 0:
                        if start_task['data']['status'] == 1:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Checking {task['title']} ]{Style.RESET_ALL}")
                            sleep(task['waitSecond'] + 3)
                            self.tasks_check(token=token, task_id=task['taskId'])
                        elif start_task['data']['status'] == 2:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                            self.tasks_check(token=token, task_id=task['taskId'])
                    elif start_task['status'] == 500 and start_task['message'] == 'Handle user\'s task error':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Finish This Task By Itself ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Start ]{Style.RESET_ALL}")
                elif task['status'] == 1:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Finish Or Start {task['title']} ]{Style.RESET_ALL}")
                    self.tasks_check(token=token, task_id=task['taskId'])
                elif task['status'] == 2:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                    self.tasks_check(token=token, task_id=task['taskId'])

    def tasks_start(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        data = json.dumps({'task_id': task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()

    def tasks_check(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/check'
        data = json.dumps({'task_id': task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        tasks_check = response.json()
        if 'status' in tasks_check:
            if 'status' in tasks_check['data']:
                if tasks_check['data']['status'] == 0:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting Task ]{Style.RESET_ALL}")
                    self.tasks_start(token=token, task_id=task_id)
                elif tasks_check['data']['status'] == 1:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ This Task Still Haven't Finished ]{Style.RESET_ALL}")
                elif tasks_check['data']['status'] == 2:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming Task ]{Style.RESET_ALL}")
                    self.tasks_claim(token=token, task_id=task_id)
                elif tasks_check['data']['status'] == 3:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ This Task Already Claimed ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Check ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Check ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Check ]{Style.RESET_ALL}")

    def tasks_claim(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        data = json.dumps({'task_id': task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        tasks_claim = response.json()
        if 'status' in tasks_claim:
            if tasks_claim['status'] == 0:
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Claimed ]{Style.RESET_ALL}")
            elif tasks_claim['status'] == 500 and tasks_claim['message'] == 'You haven\'t start this task':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Start This Task ]{Style.RESET_ALL}")
                self.tasks_start(token=token, task_id=task_id)
            elif tasks_claim['status'] == 500 and tasks_claim['message'] == 'You haven\'t finished this task':
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Finished This Task ]{Style.RESET_ALL}")
                self.tasks_check(token=token, task_id=task_id)
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Claim ]{Style.RESET_ALL}")
        else:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error Tasks Claim ]{Style.RESET_ALL}")

    def main(self):
        accounts = json.load(open('data.json', 'r'))['accounts']
        for account in accounts:
            self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['name']} ]{Style.RESET_ALL}")
            # Daily
            self.daily_claim(token=account['token'])
            # Info
            balance = self.user_balance(token=account['token'])
            self.print_timestamp(
                f"{Fore.YELLOW + Style.BRIGHT}[ Balance {balance['data']['available_balance']} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {balance['data']['play_passes']} ]{Style.RESET_ALL}"
            )
            # Farm
            if 'farming' in balance['data']:
                now = datetime.now(pytz.timezone('Asia/Jakarta'))
                farm_end_at = datetime.fromtimestamp(balance['data']['farming']['end_at'], pytz.timezone('Asia/Jakarta'))
                if now >= farm_end_at:
                    self.farm_claim(token=account['token'])
                else:
                    timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
            else:
                self.farm_start(token=account['token'])
            # Play
            while balance['data']['play_passes'] > 0:
                self.game_play(token=account['token'])
                balance['data']['play_passes'] -= 1
            # Tasks
            self.tasks_list(token=account['token'])
        self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting Soon ]{Style.RESET_ALL}")
        sleep((3 * 3600) + 10)
        self.clear_terminal()


if __name__ == '__main__':
    while True:
        try:
            init(autoreset=True)
            tomarket = Tomarket()
            tomarket.main()
            gc.collect()
        except (Exception, requests.ConnectionError, requests.JSONDecodeError) as e:
            tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
            pass
        except KeyboardInterrupt:
            tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ See You 👋🏻 ]{Style.RESET_ALL}")
            sys.exit(0)