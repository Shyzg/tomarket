from colorama import Fore, Style
from datetime import datetime
from time import sleep
import pytz
import random
import requests


def print_timestamp(message, timezone='Asia/Jakarta'):
    local_tz = pytz.timezone(timezone)
    now = datetime.now(local_tz)
    timestamp = now.strftime(f'%x %X %Z')
    print(
        f"{Fore.BLUE + Style.BRIGHT}[ {timestamp} ]{Style.RESET_ALL}"
        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        f"{message}"
    )

class Tomarket:
    def __init__(self):
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
            'Host': 'api-web.tomarket.ai',
            'Origin': 'https://mini-app.tomarket.ai',
            'Referer': 'https://mini-app.tomarket.ai/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        }

    def balance(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        try:
            self.headers.update({
                'Authorization': token
            })
            response = requests.post(url=url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            print_timestamp(
                f"{Fore.YELLOW + Style.BRIGHT}[ Available Balance {data['data']['available_balance']} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {data['data']['play_passes']} ]{Style.RESET_ALL}"
            )
            return data
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def claim_daily(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                "game_id": "fa873d13-d831-4d6f-8aee-9cff7a1d0db1"
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return print_timestamp(
                f"{Fore.MAGENTA + Style.BRIGHT}[ Daily Claim ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}[ Day {data['data']['today_game']} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT}[ Points {data['data']['today_points']} ]{Style.RESET_ALL}"
            )
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def start_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                "game_id": "53b22103-c7ff-413d-bc63-20f6fb806a07"
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            end_time = datetime.fromtimestamp(data['data']['end_at'])
            now = datetime.now()
            remaining_time = end_time - now
            if remaining_time.total_seconds() > 0:
                hours, remainder = divmod(remaining_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                return print_timestamp(f"{Fore.BLUE + Style.BRIGHT}[ {int(hours)} Hours {int(minutes)} Minutes {int(seconds)} Seconds Remaining To Claim Farm ]{Style.RESET_ALL}")
            else:
                print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Claiming Farm ]")
                sleep(3)
                return self.claim_farm(token=token)
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def claim_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                "game_id": "53b22103-c7ff-413d-bc63-20f6fb806a07"
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Claimed {(data['data']['points'] + data['data']['claim_this_time'])} ]")
            sleep(3)
            print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Starting Farm ]")
            return self.start_farm(token=token)
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def play_game(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                "game_id": "59bcd12e-04e2-404c-a172-311a0084587d"
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            start_time = datetime.fromtimestamp(data['data']['start_at'])
            end_time = datetime.fromtimestamp(data['data']['end_at'])
            total_time = end_time - start_time
            total_seconds = total_time.total_seconds()
            print_timestamp(f"{Fore.BLUE + Style.BRIGHT}[ Game Started Please Wait {int(total_seconds)} Seconds ]{Style.RESET_ALL}")
            sleep(33)
            return self.claim_game(token=token, point=random.randint(1, 600))
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def claim_game(self, token: str, point: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                "game_id": "59bcd12e-04e2-404c-a172-311a0084587d",
                "points": point
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {data['data']['points']} ]")
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def tasks(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                'language_code': 'en'
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            for task in data['data']:
                start = self.start_tasks(token=token, task_id=task['taskId'])
                if start['message'] == "You haven't finished this task":
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task['title']} Not Finished ]{Style.RESET_ALL}")
                elif start['message'] == "Task handle is not exist":
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task['title']} {start['message']} ]{Style.RESET_ALL}")
                else:
                    claim = self.claim_tasks(token=token, task_id=task['taskId'])
                    if claim['message'] == "You haven't start this task":
                        self.start_tasks(token=token, task_id=task['id'])
                    elif claim['message'] == "You haven't finished this task":
                        print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task['title']} Not Finished ]{Style.RESET_ALL}")
                    else:
                        print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ {task['title']} Finished ]{Style.RESET_ALL}")
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def start_tasks(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                'task_id': task_id
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")

    def claim_tasks(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        try:
            self.headers.update({
                'Authorization': token
            })
            payload = {
                'task_id': task_id
            }
            response = requests.post(url=url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except (Exception, requests.JSONDecodeError, requests.RequestException) as e:
            return print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")