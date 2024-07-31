from colorama import Fore, Style
from datetime import datetime
from fake_useragent import FakeUserAgent
from urllib.parse import parse_qs, unquote
import aiohttp
import asyncio
import json
import pytz
import random


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
            'Content-Type': 'application/json',
            'Host': 'api-web.tomarket.ai',
            'Origin': 'https://mini-app.tomarket.ai',
            'Referer': 'https://mini-app.tomarket.ai/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def parse_query(self, query: str):
        parsed_query = parse_qs(query)
        parsed_query = {k: v[0] for k, v in parsed_query.items()}
        user_data = json.loads(unquote(parsed_query['user']))
        parsed_query['user'] = user_data
        return parsed_query

    async def request(self, session, method, url, **kwargs):
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    async def user_login(self):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/login'
        tokens = set()
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                queries = [line.strip() for line in open('queries.txt', 'r').readlines()]

                for query in queries:
                    parsed_query = self.parse_query(query)
                    payload = {
                        'init_data': query,
                        'invite_code': '',
                        'is_bot': False
                    }
                    data = await self.request(session, 'POST', url, json=payload)
                    token = data['data']['access_token'].strip()
                    tokens.add((token, parsed_query['user']['username']))

                return tokens
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def user_balance(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        headers = {**self.headers, 'Authorization': token}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url)
                print_timestamp(
                    f"{Fore.YELLOW + Style.BRIGHT}[ Available Balance {data['data']['available_balance']} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {data['data']['play_passes']} ]{Style.RESET_ALL}"
                )

                while data['data']['play_passes'] > 0:
                    await self.play_game(token)
                    data['data']['play_passes'] -= 1
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def play_game(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        headers = {**self.headers, 'Authorization': token}
        payload = {'game_id': '59bcd12e-04e2-404c-a172-311a0084587d'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Started Please Wait ]{Style.RESET_ALL}")
                    await asyncio.sleep(33)
                    await self.claim_game(token, random.randint(6000, 6001))
                elif data['status'] == 500:
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No Chance To Play Game ]{Style.RESET_ALL}")
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def claim_game(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        headers = {**self.headers, 'Authorization': token}
        payload = {'game_id': '59bcd12e-04e2-404c-a172-311a0084587d', 'points': points}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {data['data']['points']} ]{Style.RESET_ALL}")
                elif data['status'] == 500:
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}")
                    await self.play_game(token)
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def claim_daily(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        headers = {**self.headers, 'Authorization': token}
        payload = {'game_id': 'fa873d13-d831-4d6f-8aee-9cff7a1d0db1'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Daily Claim ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Day {data['data']['today_game']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Points {data['data']['today_points']} ]{Style.RESET_ALL}"
                    )
                elif data['status'] == 400 and data['message'] == "already_check":
                    print_timestamp(
                        f"{Fore.MAGENTA + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Day {data['data']['today_game']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Points {data['data']['today_points']} ]{Style.RESET_ALL}"
                    )
                elif data['status'] == 400 and data['message'] == "claim throttle":
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Throttle ]{Style.RESET_ALL}")
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def start_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        headers = {**self.headers, 'Authorization': token}
        payload = {'game_id': '53b22103-c7ff-413d-bc63-20f6fb806a07'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Started ]{Style.RESET_ALL}")
                elif data['status'] == 500:
                    print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Farm Already Started ]{Style.RESET_ALL}")
                    if data['data']['need_time'] > 0:
                        hours, remainder = divmod(data['data']['need_time'], 3600)
                        minutes, seconds = divmod(remainder, 60)
                        print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {int(hours)} Hours {int(minutes)} Minutes {int(seconds)} Seconds To Claim Farm ]{Style.RESET_ALL}")
                    else:
                        await self.claim_farm(token=token)
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def claim_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        headers = {**self.headers, 'Authorization': token}
        payload = {'game_id': '53b22103-c7ff-413d-bc63-20f6fb806a07'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Claimed {data['data']['points']} From Farm ]{Style.RESET_ALL}")
                    await self.start_farm(token=token)
                elif data['status'] == 400:
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Throttle ]{Style.RESET_ALL}")
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def list_tasks(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        headers = {**self.headers, 'Authorization': token}
        payload = {'language_code': 'en'}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                for category in data['data']:
                    for task in data['data'][category]:
                        if 'endTime' in task and task['endTime']:
                            end_time = datetime.strptime(task['endTime'], '%Y-%m-%d %H:%M:%S')
                            if end_time < datetime.now():
                                continue
                        if not 'special' in task['tag']:
                            if task['status'] == 0 and task['type'] == "mysterious":
                                print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                                await self.claim_tasks(token=token, task_id=task['taskId'])
                            elif task['status'] == 0:
                                print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting {task['title']} ]{Style.RESET_ALL}")
                                start_task = await self.start_tasks(token=token, task_id=task['taskId'])
                                if start_task['data']['status'] == 1:
                                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Checking {task['title']} ]{Style.RESET_ALL}")
                                    await asyncio.sleep(task['waitSecond'] + 3)
                                    await self.check_tasks(token=token, task_id=task['taskId'])
                                elif start_task['data']['status'] == 2:
                                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                                    await self.claim_tasks(token=token, task_id=task['taskId'])
                            elif task['status'] == 1:
                                print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Finish Or Start This {task['title']} Task ]{Style.RESET_ALL}")
                                await self.check_tasks(token=token, task_id=task['taskId'])
                            elif task['status'] == 2:
                                print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                                await self.claim_tasks(token=token, task_id=task['taskId'])
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def start_tasks(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        headers = {**self.headers, 'Authorization': token}
        payload = {'task_id': task_id}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                return await self.request(session, 'POST', url, json=payload)
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def check_tasks(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/check'
        headers = {**self.headers, 'Authorization': token}
        payload = {'task_id': task_id}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['data']['status'] == 0:
                    await self.start_tasks(token=token, task_id=task_id)
                elif data['data']['status'] == 1:
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ This Task Still Haven't Finished Or Started ]{Style.RESET_ALL}")
                elif data['data']['status'] == 2:
                    await self.claim_tasks(token=token, task_id=task_id)
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")

    async def claim_tasks(self, token: str, task_id: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        headers = {**self.headers, 'Authorization': token}
        payload = {'task_id': task_id}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                data = await self.request(session, 'POST', url, json=payload)
                if data['status'] == 0:
                    print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Claimed ]{Style.RESET_ALL}")
                elif data['status'] == 500:
                    print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Finish Or Start This Task ]{Style.RESET_ALL}")
                elif data['status'] == 401:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Invalid Task ]{Style.RESET_ALL}")
                else:
                    print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {data['message']} ]{Style.RESET_ALL}")
            except (Exception, aiohttp.ClientResponseError) as e:
                print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")