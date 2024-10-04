from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from time import sleep
import asyncio, json, os, random, re, sys

class Tomarket:
    def __init__(self) -> None:
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
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def process_queries(self, lines_per_file=10):
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
                new_accounts = await self.generate_tokens(chunk)
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
            accounts = await self.generate_tokens(chunk)

            with open(accounts_file, 'w') as outfile:
                json.dump({'accounts': accounts}, outfile, indent=4)

            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Generated Tokens In '{accounts_file}' ]{Style.RESET_ALL}")
            last_file_number += 1

    def load_accounts_from_file(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)['accounts']

    async def generate_token(self, query: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/login'
        data = json.dumps({'init_data':query,'invite_code':'0000cYQe','from':'','is_bot':False})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    generate_token = await response.json()
                    access_token = generate_token['data']['access_token']
                    first_name = generate_token['data']['fn'] or self.faker.first_name()
                    return ({'token': access_token, 'first_name': first_name})
        except (ClientResponseError, Exception) as e:
            self.print_timestamp(
                f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}"
            )
            return None

    async def generate_tokens(self, queries):
        tasks = [self.generate_token(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def claim_daily(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        data = json.dumps({'game_id':'fa873d13-d831-4d6f-8aee-9cff7a1d0db1'})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    claim_daily = await response.json()
                    if 'status' in claim_daily:
                        if claim_daily['status'] == 0:
                            return self.print_timestamp(
                                f"{Fore.GREEN + Style.BRIGHT}[ Daily Claimed ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.BLUE + Style.BRIGHT}[ Points {claim_daily['data']['today_points']} ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}[ Day {claim_daily['data']['today_game']} ]{Style.RESET_ALL}"
                            )
                        elif claim_daily['status'] == 400 and claim_daily['message'] == 'already_check':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")

    async def data_rank(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/rank/data'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    data_rank = await response.json()
                    if 'status' in data_rank:
                        if data_rank['status'] == 0:
                            if data_rank['data']['isCreated']:
                                if data_rank['data']['unusedStars'] == 0:
                                    return self.print_timestamp(f"{Fore.BLUE + Style.BRIGHT}[ Rank {data_rank['data']['currentRank']['name']} ]{Style.RESET_ALL}")
                                return await self.upgrade_rank(token=token, stars=(data_rank['data']['unusedStars'] - 3))
                            return await self.evaluate_rank(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Data Rank: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Data Rank: {str(e)} ]{Style.RESET_ALL}")

    async def evaluate_rank(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/rank/evaluate'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    evaluate_rank = await response.json()
                    if 'status' in evaluate_rank:
                        if evaluate_rank['status'] == 0:
                            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Rank Evaluated ]{Style.RESET_ALL}")
                            return await self.create_rank(token=token)
                        elif evaluate_rank['status'] == 500 and evaluate_rank['message'] == 'User has a rank':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ User Has A Rank ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Evaluate Rank: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Evaluate Rank: {str(e)} ]{Style.RESET_ALL}")

    async def create_rank(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/rank/create'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    create_rank = await response.json()
                    if 'status' in create_rank:
                        if create_rank['status'] == 0:
                            if create_rank['data']['isCreated']:
                                if create_rank['data']['unusedStars'] == 0:
                                    return self.print_timestamp(
                                        f"{Fore.GREEN + Style.BRIGHT}[ Rank Created ]{Style.RESET_ALL}"
                                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                        f"{Fore.BLUE + Style.BRIGHT}[ Rank {create_rank['data']['currentRank']['name']} ]{Style.RESET_ALL}"
                                    )
                                return await self.upgrade_rank(token=token, stars=(create_rank['data']['unusedStars'] - 3))
                        elif create_rank['status'] == 427 and create_rank['message'] == 'Rank value has already been initialized':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Rank Value Has Already Been Initialized ]{Style.RESET_ALL}")
                        elif create_rank['status'] == 500 and create_rank['message'] == 'Need to evaluate stars first':
                            return await self.evaluate_rank(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Create Rank: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Create Rank: {str(e)} ]{Style.RESET_ALL}")

    async def upgrade_rank(self, token: str, stars: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/rank/upgrade'
        data = json.dumps({'stars':stars})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    upgrade_rank = await response.json()
                    if 'status' in upgrade_rank:
                        if upgrade_rank['status'] == 0:
                            return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Rank With {stars} Stars ]{Style.RESET_ALL}")
                        elif upgrade_rank['status'] == 500 and upgrade_rank['message'] == 'You dose not have a rank':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Does Not Have A Rank ]{Style.RESET_ALL}")
                        elif upgrade_rank['status'] == 500 and upgrade_rank['message'] == f'You dose not have enough stars {stars}':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Does Not Have Enough {stars} Stars ]{Style.RESET_ALL}")
                        elif upgrade_rank['status'] == 500 and upgrade_rank['message'] == f'Star must be greater than zero':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Your Stars Must Be Greater Than Three ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Rank: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Rank: {str(e)} ]{Style.RESET_ALL}")

    async def balance_user(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    balance_user = await response.json()
                    return balance_user
        except ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Balance User: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Balance User: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def start_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    start_farm = await response.json()
                    if 'status' in start_farm:
                        if start_farm['status'] == 0:
                            return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Started, And Can Be Claim At {datetime.fromtimestamp(start_farm['data']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                        elif start_farm['status'] == 500 and start_farm['message'] == 'game already started':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {datetime.fromtimestamp(start_farm['data']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                        elif start_farm['status'] == 500 and start_farm['message'] == 'game end need claim':
                            return await self.claim_farm(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Farm: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Farm: {str(e)} ]{Style.RESET_ALL}")

    async def claim_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    claim_farm = await response.json()
                    if 'status' in claim_farm:
                        if claim_farm['status'] == 0:
                            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {claim_farm['data']['points']} From Farm ]{Style.RESET_ALL}")
                            return await self.start_farm(token=token)
                        elif claim_farm['status'] == 500 and claim_farm['message'] == 'farm not started or claimed':
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Not Started ]{Style.RESET_ALL}")
                            return await self.start_farm(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Farm: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Farm: {str(e)} ]{Style.RESET_ALL}")

    async def play_game(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d'})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        play_game = await response.json()
                        if 'status' in play_game:
                            if play_game['status'] == 0:
                                self.print_timestamp(
                                    f"{Fore.BLUE + Style.BRIGHT}[ Game Started ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Please Wait ~30 Seconds ]{Style.RESET_ALL}"
                                )
                                sleep(30 + random.randint(3, 5))
                                await self.claim_game(token=token, points=random.randint(6000, 6001))
                            elif play_game['status'] == 500 and play_game['message'] == 'no chance':
                                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Chance To Start Game ]{Style.RESET_ALL}")
            except ClientResponseError as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
            except Exception as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")

    async def claim_game(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d','points':points})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    claim_game = await response.json()
                    if 'status' in claim_game:
                        if claim_game['status'] == 0:
                            return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {claim_game['data']['points']} From Game ]{Style.RESET_ALL}")
                        elif claim_game['status'] == 500 and claim_game['message'] == 'game not start':
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}")
                            return await self.play_game(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")

    async def list_tasks(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        data = json.dumps({'language_code':'en'})
        headers = {
            **self.headers,
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    list_tasks = await response.json()
                    current_time = datetime.now().astimezone()
                    await self.process_category(list_tasks['data'], token, current_time)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def process_task(self, task, token, current_time):
        end_time = datetime.strptime(task['endTime'], '%Y-%m-%d %H:%M:%S').astimezone() if task.get('endTime') else None
        if (
            (end_time and end_time < current_time) or
            ('walletAddress' in task['handleFunc'] or 'boost' in task['handleFunc'] or 'checkInvite' in task['handleFunc']) or
            ('classmate' in task['tag']) or
            ('classmate' in task['type'].lower())
        ): return

        wait_second = task.get('waitSecond', 0)
        if task['status'] == 0 and task['type'] == "mysterious":
            await self.claim_tasks(token, task['taskId'], task['title'], task['score'])
            sleep(random.randint(3, 5))
        elif task['status'] == 0:
            await self.start_tasks(token, task['taskId'], task['title'], wait_second, task['score'])
            sleep(random.randint(3, 5))
        elif task['status'] == 1:
            await self.check_tasks(token, task['taskId'], task['title'], task['score'])
            sleep(random.randint(3, 5))
        elif task['status'] == 2:
            await self.claim_tasks(token, task['taskId'], task['title'], task['score'])
            sleep(random.randint(3, 5))

    async def process_category(self, category_data, token, current_time):
        for category in category_data:
            if isinstance(category_data[category], list):
                for task in category_data[category]:
                    await self.process_task(task, token, current_time)
            elif isinstance(category_data[category], dict):
                await self.process_category(category_data[category], token, current_time)

    async def start_tasks(self, token: str, task_id: int, task_title: str, task_waitsecond: int, task_score: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    start_tasks = await response.json()
                    if 'status' in start_tasks:
                        if start_tasks['status'] == 0:
                            if start_tasks['data']['status'] == 1:
                                self.print_timestamp(
                                    f"{Fore.BLUE + Style.BRIGHT}[ {task_title} Started ]{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}[ Please Wait ~{task_waitsecond} ]{Style.RESET_ALL}"
                                )
                                sleep(task_waitsecond + random.randint(3, 5))
                                return await self.check_tasks(token=token, task_id=task_id, task_title=task_title, task_score=task_score)
                            elif start_tasks['data']['status'] == 2:
                                sleep(random.randint(3, 5))
                                return await self.claim_tasks(token=token, task_id=task_id, task_title=task_title, task_score=task_score)
                        elif start_tasks['status'] == 500 and start_tasks['message'] == 'Handle user\'s task error':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Finish {task_title} By Itself ]{Style.RESET_ALL}")
                        elif start_tasks['status'] == 500 and start_tasks['message'] == 'Task handle is not exist':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Exist ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def check_tasks(self, token: str, task_id: int, task_title: str, task_score: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/check'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    check_tasks = await response.json()
                    if 'status' in check_tasks:
                        if check_tasks['status'] == 0:
                            if check_tasks['data']['status'] == 2:
                                sleep(random.randint(3, 5))
                                return await self.claim_tasks(token=token, task_id=task_id, task_title=task_title, task_score=task_score)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def claim_tasks(self, token: str, task_id: int, task_title: str, task_score: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    claim_tasks = await response.json()
                    if 'status' in claim_tasks:
                        if claim_tasks['status'] == 0:
                            return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {task_score} From {task_title} ]{Style.RESET_ALL}")
                        elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t start this task':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Haven\'t Start {task_title} ]{Style.RESET_ALL}")
                        elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t finished this task':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Haven\'t Finished {task_title} ]{Style.RESET_ALL}")
                        elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'Task is not within the valid time':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Isn\'t Within The Valid Time ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def assets_spin(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/spin/assets'
        data = json.dumps({'language_code':'en'})
        headers = {
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    assets_spin = await response.json()
                    if 'status' in assets_spin:
                        if assets_spin['status'] == 0:
                            for balance in assets_spin['data']['balances']:
                                if balance['balance_type'] == 'Star':
                                    if balance['balance'] == 0:
                                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ You Didn\'t Have Tomarket Star ]{Style.RESET_ALL}")
                                    return await self.raffle_spin(token=token, category='tomarket')
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Assets Spin: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Assets Spin: {str(e)} ]{Style.RESET_ALL}")

    async def tickets_user(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/tickets'
        data = json.dumps({'language_code':'en'})
        headers = {
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    tickets_user = await response.json()
                    if 'status' in tickets_user:
                        if tickets_user['status'] == 0:
                            while tickets_user['data']['ticket_spin_1'] > 0:
                                await self.raffle_spin(token=token, category='ticket_spin_1')
                                sleep(random.randint(3, 5))
                                tickets_user['data']['ticket_spin_1'] -= 1
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tickets User: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tickets User: {str(e)} ]{Style.RESET_ALL}")

    async def raffle_spin(self, token: str, category: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/spin/raffle'
        data = json.dumps({'category':category})
        headers = {
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    raffle_spin = await response.json()
                    if 'status' in raffle_spin:
                        if raffle_spin['status'] == 0:
                            for result in raffle_spin['data']['results']:
                                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {result['amount']} {result['type']} From Raffle Spin ]{Style.RESET_ALL}")
                        elif raffle_spin['status'] == 400 and raffle_spin['message'] == 'Max 3 spins per day using Tomarket Stars.':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Max 3 Spins Per Day Using Tomarket Stars ]{Style.RESET_ALL}")
                        elif raffle_spin['status'] == 500 and raffle_spin['message'] == 'Not enough ticket_spin_1 ticket':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Free Spin Tickets ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Raffle Spin: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Raffle Spin: {str(e)} ]{Style.RESET_ALL}")

    async def main(self, accounts):
        while True:
            try:
                farming_times = []
                total_balance = 0

                for account in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                    )
                    await self.claim_daily(token=account['token'])
                    sleep(random.randint(3, 5))
                    balance = await self.balance_user(token=account['token'])
                    sleep(random.randint(3, 5))
                    if balance is not None:
                        self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Balance {balance['data']['available_balance']} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {balance['data']['play_passes']} ]{Style.RESET_ALL}"
                        )
                        if 'farming' in balance['data']:
                            if datetime.now().astimezone() >= datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone():
                                await self.claim_farm(token=account['token'])
                                sleep(random.randint(3, 5))
                            else:
                                farming_times.append(datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone().timestamp())
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                        else:
                            await self.start_farm(token=account['token'])
                            sleep(random.randint(3, 5))
                        total_balance += int(float(balance['data']['available_balance']))

                sleep(random.randint(5, 7))
                for account in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home/Rank ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                    )
                    await self.data_rank(token=account['token'])
                    sleep(random.randint(3, 5))

                sleep(random.randint(5, 7))
                for account in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home/Play Passes ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                    )
                    await self.play_game(token=account['token'])
                    sleep(random.randint(3, 5))

                sleep(random.randint(5, 7))
                for account in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                    )
                    await self.list_tasks(token=account['token'])
                    sleep(random.randint(3, 5))

                sleep(random.randint(5, 7))
                for account in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Spin ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                    )
                    await self.assets_spin(token=account['token'])
                    sleep(random.randint(3, 5))
                    await self.tickets_user(token=account['token'])
                    sleep(random.randint(3, 5))

                if farming_times:
                    wait_times = [farm_end_time - datetime.now().astimezone().timestamp() for farm_end_time in farming_times if farm_end_time > datetime.now().astimezone().timestamp()]
                    if wait_times:
                        sleep_time = min(wait_times) + 30
                    else:
                        sleep_time = 15 * 60
                else:
                    sleep_time = 15 * 60

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=sleep_time)).strftime('%X %Z')} ]{Style.RESET_ALL}")

                sleep(sleep_time)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
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
            asyncio.run(tomarket.process_queries())
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

        asyncio.run(tomarket.main(accounts))
    except (ValueError, IndexError, FileNotFoundError) as e:
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)