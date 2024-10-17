from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
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

    async def process_queries(self, lines_per_file: int):
        if not os.path.exists('queries.txt'):
            raise FileNotFoundError("File 'queries.txt' Not Found. Please Ensure It Exists")

        queries = [line.strip() for line in open('queries.txt', 'r') if line.strip()]
        if not queries:
            raise ValueError("File 'queries.txt' Is Empty")

        account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
        account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0])) if account_files else []

        existing_accounts = {}
        for account_file in account_files:
            accounts_data = json.load(open(account_file, 'r'))
            accounts = accounts_data.get('accounts', [])
            for account in accounts:
                existing_accounts[account['first_name']] = account['token']

        for account_file in account_files:
            accounts_data = json.load(open(account_file, 'r'))
            accounts = accounts_data.get('accounts', [])

            new_accounts = []
            token_data_list = await self.generate_tokens(queries)
            for token_data in token_data_list:
                first_name = token_data['first_name']
                if first_name in existing_accounts:
                    for account in accounts:
                        if account['first_name'] == first_name:
                            account['token'] = token_data['token']
                else:
                    new_accounts.append(token_data)
                    existing_accounts[first_name] = token_data['token']

            accounts.extend(new_accounts)
            accounts = accounts[:lines_per_file]
            accounts_data['accounts'] = accounts

            if new_accounts:
                json.dump(accounts_data, open(account_file, 'w'), indent=4)
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Updated '{account_file}' With {len(new_accounts)} New Token And Name ]{Style.RESET_ALL}")

            queries = queries[len(new_accounts):]
            if len(queries) == 0:
                break

        last_file_number = int(re.findall(r'\d+', account_files[-1])[0]) if account_files else 0

        for i in range(0, len(queries), lines_per_file):
            chunk = queries[i:i + lines_per_file]
            new_accounts = await self.generate_tokens(chunk)
            new_accounts = [acc for acc in new_accounts if acc['first_name'] not in existing_accounts]

            if new_accounts:
                last_file_number += 1
                accounts_file = f"accounts-{last_file_number}.json"

                for account in new_accounts:
                    existing_accounts[account['first_name']] = account['token']

                json.dump({'accounts': new_accounts}, open(accounts_file, 'w'), indent=4)
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Generated Tokens In '{accounts_file}' ]{Style.RESET_ALL}")

    async def load_from_json(self, file_path):
        try:
            return [(account['token'], account['first_name']) for account in json.load(open(file_path, 'r'))['accounts']]
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Error Occurred While Loading JSON: {str(e)} ]{Style.RESET_ALL}")
            return []

    async def generate_token(self, query: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/login'
        data = json.dumps({'init_data':query,'invite_code':'0000cYQe','from':'','is_bot':False})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        await asyncio.sleep(3)
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    generate_token = await response.json()
                    access_token = generate_token['data']['access_token']
                    first_name = generate_token['data']['fn'] or self.faker.first_name()
                    return {'token': access_token, 'first_name': first_name}
        except (Exception, ClientResponseError) as e:
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

    async def daily_claim(self, token: str):
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
                    daily_claim = await response.json()
                    if daily_claim['status'] == 0:
                        return self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Daily Claimed ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ {daily_claim['data']['today_points']} $TOMA ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Day {daily_claim['data']['today_game']} ]{Style.RESET_ALL}"
                        )
                    elif daily_claim['status'] == 400 and daily_claim['message'] == 'already_check':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")

    async def rank_data(self, token: str):
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
                    rank_data = await response.json()
                    if rank_data['status'] == 0:
                        if rank_data['data']['isCreated']:
                            return await self.rank_upgrade(token=token, stars=rank_data['data']['unusedStars'])
                        return await self.rank_evaluate(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Rank Data: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Rank Data: {str(e)} ]{Style.RESET_ALL}")

    async def rank_evaluate(self, token: str):
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
                    rank_evaluate = await response.json()
                    if rank_evaluate['status'] == 0:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Rank Evaluated ]{Style.RESET_ALL}")
                        return await self.rank_create(token=token)
                    elif rank_evaluate['status'] == 500 and rank_evaluate['message'] == 'User has a rank':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ User Has A Rank ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Rank Evaluate: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Rank Evaluate: {str(e)} ]{Style.RESET_ALL}")

    async def rank_create(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/rank/create'
        headers = {
            **self.headers,
            'Authorization': token,
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    rank_create = await response.json()
                    if rank_create['status'] == 0:
                        if rank_create['data']['isCreated']:
                            self.print_timestamp(
                                f"{Fore.GREEN + Style.BRIGHT}[ Rank Created ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.BLUE + Style.BRIGHT}[ Current Rank {rank_create['data']['currentRank']['name']} ]{Style.RESET_ALL}"
                            )
                            return await self.rank_upgrade(token=token, stars=rank_create['data']['unusedStars'])
                    elif rank_create['status'] == 427 and rank_create['message'] == 'Rank value has already been initialized':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Rank Value Has Already Been Initialized ]{Style.RESET_ALL}")
                    elif rank_create['status'] == 500 and rank_create['message'] == 'Need to evaluate stars first':
                        return await self.rank_evaluate(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Rank Create: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Rank Create: {str(e)} ]{Style.RESET_ALL}")

    async def rank_upgrade(self, token: str, stars: int):
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
                    rank_upgrade = await response.json()
                    if rank_upgrade['status'] == 0:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Rank With {stars} Stars ]{Style.RESET_ALL}")
                    elif rank_upgrade['status'] == 500 and rank_upgrade['message'] == 'You dose not have a rank':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Doesn\'t Have A Rank ]{Style.RESET_ALL}")
                    elif rank_upgrade['status'] == 500 and rank_upgrade['message'] == f'You dose not have enough stars {stars}':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Doesn\'t Have Enough {stars} Stars ]{Style.RESET_ALL}")
                    elif rank_upgrade['status'] == 500 and rank_upgrade['message'] == 'Star must be greater than zero':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Stars Must Be Greater Than Zero ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Rank Upgrade: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Rank Upgrade: {str(e)} ]{Style.RESET_ALL}")

    async def user_balance(self, token: str):
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
                    return await response.json()
        except ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching User Balance: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching User Balance: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def farm_start(self, token: str):
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
                    farm_start = await response.json()
                    if farm_start['status'] == 0:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farm Started, And Can Be Claim At {datetime.fromtimestamp(farm_start['data']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                    elif farm_start['status'] == 500 and farm_start['message'] == 'game already started':
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {datetime.fromtimestamp(farm_start['data']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                    elif farm_start['status'] == 500 and farm_start['message'] == 'game end need claim':
                        return await self.farm_claim(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Farm Start: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Farm Start: {str(e)} ]{Style.RESET_ALL}")

    async def farm_claim(self, token: str):
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
                    farm_claim = await response.json()
                    if farm_claim['status'] == 0:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {farm_claim['data']['points']} $TOMA From Farm ]{Style.RESET_ALL}")
                        return await self.farm_start(token=token)
                    elif farm_claim['status'] == 500 and farm_claim['message'] == 'farm not started or claimed':
                        return await self.farm_start(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Farm Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Farm Claim: {str(e)} ]{Style.RESET_ALL}")

    async def game_play(self, token: str):
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
                        game_play = await response.json()
                        if game_play['status'] == 0:
                            self.print_timestamp(
                                f"{Fore.BLUE + Style.BRIGHT}[ Game Started ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}[ Please Wait ~30 Seconds ]{Style.RESET_ALL}"
                            )
                            await asyncio.sleep(33)
                            await self.game_claim(token=token, points=random.randint(6000, 6001))
                        elif game_play['status'] == 500 and game_play['message'] == 'no chance':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Chance To Start Game ]{Style.RESET_ALL}")
            except ClientResponseError as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Game Play: {str(e)} ]{Style.RESET_ALL}")
            except Exception as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Game Play: {str(e)} ]{Style.RESET_ALL}")

    async def game_claim(self, token: str, points: int):
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
                    game_claim = await response.json()
                    if game_claim['status'] == 0:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {game_claim['data']['points']} $TOMA From Game Play ]{Style.RESET_ALL}")
                    elif game_claim['status'] == 500 and game_claim['message'] == 'game not start':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}")
                        return await self.play_game(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Game Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Game Claim: {str(e)} ]{Style.RESET_ALL}")

    async def tasks_list(self, token: str):
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
                    tasks_list = await response.json()
                    await self.process_category(tasks_list['data'], token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def process_category(self, category_data, token):
        for category in category_data:
            if isinstance(category_data[category], list):
                for task in category_data[category]:
                    await self.process_task(task, token)
            elif isinstance(category_data[category], dict):
                await self.process_category(category_data[category], token)

    async def process_task(self, task, token):
        if (
            ('walletAddress' in task['handleFunc'] or 'boost' in task['handleFunc'] or 'checkInvite' in task['handleFunc']) or
            ('classmate' in task['tag']) or
            ('classmate' in task['type'].lower())
        ): return
        wait_second = task.get('waitSecond', 0)
        if task['status'] == 0:
            await self.tasks_start(
                token=token,
                task_id=task['taskId'],
                task_title=task['title'],
                task_score=task['score'],
                task_waitsecond=wait_second
            )
        elif task['status'] == 1:
            await self.tasks_check(
                token=token,
                task_id=task['taskId'],
                task_title=task['title'],
                task_score=task['score']
            )
        elif task['status'] == 2:
            await self.tasks_claim(
                token=token,
                task_id=task['taskId'],
                task_title=task['title'],
                task_score=task['score']
            )

    async def tasks_start(
        self,
        token: str,
        task_id: int,
        task_title: str,
        task_score: int,
        task_waitsecond: int
    ):
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
                    tasks_start = await response.json()
                    if tasks_start['status'] == 0:
                        if tasks_start['data']['status'] == 1:
                            self.print_timestamp(
                                f"{Fore.BLUE + Style.BRIGHT}[ {task_title} Started ]{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}[ Please Wait ~{task_waitsecond} ]{Style.RESET_ALL}"
                            )
                            await asyncio.sleep(task_waitsecond + random.randint(3, 5))
                            return await self.tasks_check(
                                token=token,
                                task_id=task_id,
                                task_title=task_title,
                                task_score=task_score
                            )
                        elif tasks_start['data']['status'] == 2:
                            return await self.tasks_claim(
                                token=token,
                                task_id=task_id,
                                task_title=task_title,
                                task_score=task_score
                            )
                    elif tasks_start['status'] == 500 and tasks_start['message'] == 'Handle user\'s task error':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Finish {task_title} By Itself ]{Style.RESET_ALL}")
                    elif tasks_start['status'] == 500 and tasks_start['message'] == 'Task handle is not exist':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Exist ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tasks Start: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tasks Start: {str(e)} ]{Style.RESET_ALL}")

    async def tasks_check(
        self,
        token: str,
        task_id: int,
        task_title: str,
        task_score: int
    ):
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
                    tasks_check = await response.json()
                    if tasks_check['status'] == 0:
                        if tasks_check['data']['status'] == 2:
                            return await self.tasks_claim(
                                token=token,
                                task_id=task_id,
                                task_title=task_title,
                                task_score=task_score
                            )
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def tasks_claim(
        self,
        token: str,
        task_id: int,
        task_title: str,
        task_score: int
    ):
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
                    tasks_claim = await response.json()
                    if 'status' in tasks_claim:
                        if tasks_claim['status'] == 0:
                            return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {task_score} $TOMA From {task_title} ]{Style.RESET_ALL}")
                        elif tasks_claim['status'] == 500 and tasks_claim['message'] == 'You haven\'t start this task':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Haven\'t Start {task_title} ]{Style.RESET_ALL}")
                        elif tasks_claim['status'] == 500 and tasks_claim['message'] == 'You haven\'t finished this task':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Haven\'t Finished {task_title} ]{Style.RESET_ALL}")
                        elif tasks_claim['status'] == 500 and tasks_claim['message'] == 'Task is not within the valid time':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Isn\'t Within The Valid Time ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Tasks Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Tasks Claim: {str(e)} ]{Style.RESET_ALL}")

    async def answer(self):
        url = 'https://raw.githubusercontent.com/Shyzg/answer/refs/heads/main/answer.json'
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, ssl=False) as response:
                    response.raise_for_status()
                    return json.loads(await response.text())
        except ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Answer: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Answer: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def tasks_puzzle(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/puzzle'
        data = json.dumps({'language_code':'en'})
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
                    tasks_puzzle = await response.json()
                    answer = await self.answer()
                    if answer is not None:
                        if tasks_puzzle['status'] == 0:
                            for puzzle in tasks_puzzle['data']:
                                if puzzle['status'] == 0:
                                    return await self.tasks_puzzle_claim(
                                        token=token,
                                        puzzle_id=puzzle['taskId'],
                                        puzzle_name=puzzle['name'],
                                        puzzle_star=puzzle['star'],
                                        puzzle_games=puzzle['games'],
                                        puzzle_score=puzzle['score'],
                                        answer=answer['tomarket']['answer']
                                    )
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def tasks_puzzle_claim(
        self,
        token: str,
        puzzle_id: int,
        puzzle_name: str,
        puzzle_star: int,
        puzzle_games: int,
        puzzle_score: int,
        answer: str
    ):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/puzzleClaim'
        data = json.dumps({'task_id':puzzle_id,'code':answer})
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
                    tasks_puzzle_claim = await response.json()
                    if tasks_puzzle_claim['status'] == 0:
                        if tasks_puzzle_claim['data']['status'] == 1 and tasks_puzzle_claim['data']['message'] == 'Must complement relation task':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You\'re Missing A Step, Look At The Task Page! ]{Style.RESET_ALL}")
                        if tasks_puzzle_claim['data']['status'] == 2 and tasks_puzzle_claim['data']['message'] == 'The result is incorrect':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Oh No, That\'s Incorrect. Watch The Video Carefully ]{Style.RESET_ALL}")
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {puzzle_star} Tomarket Stars, {puzzle_games} Ticket, And {puzzle_score} $TOMA From {puzzle_name} ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def spin_assets(self, token: str):
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
                    spin_assets = await response.json()
                    if spin_assets['status'] == 0:
                        for category in ['tomarket', 'ticket_spin_1']:
                            await self.spin_raffle(token=token, category=category)
                            await asyncio.sleep(3)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Spin Assets: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Spin Assets: {str(e)} ]{Style.RESET_ALL}")

    async def spin_raffle(self, token: str, category: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/spin/raffle'
        data = json.dumps({'category':category})
        headers = {
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        spin_raffle = await response.json()
                        if spin_raffle['status'] == 0:
                            if 'isPassed' in spin_raffle['data']:
                                if not spin_raffle['data']['isPassed']: return None
                            for result in spin_raffle['data']['results']:
                                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {result['amount']} {result['type']} From Raffle Spin ]{Style.RESET_ALL}")
                        elif spin_raffle['status'] == 400 and spin_raffle['message'] == 'Please wait 2 seconds before spinning again.':
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Please Wait 2 Seconds Before Spinning Again ]{Style.RESET_ALL}")
                        elif spin_raffle['status'] == 400 and spin_raffle['message'] == 'Max 3 spins per day using Tomarket Stars.':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Max 3 Spins Per Day Using Tomarket Stars ]{Style.RESET_ALL}")
                        elif spin_raffle['status'] == 500 and spin_raffle['message'] == 'Not enough ticket_spin_1 ticket':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Free Spin Tickets ]{Style.RESET_ALL}")
            except ClientResponseError as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Spin Raffle: {str(e)} ]{Style.RESET_ALL}")
            except Exception as e:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Spin Raffle: {str(e)} ]{Style.RESET_ALL}")

    async def main(self, accounts):
        while True:
            try:
                farming_times = []
                total_balance = 0

                for (token, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.daily_claim(token=token)
                    await asyncio.sleep(3)
                    balance = await self.user_balance(token=token)
                    await asyncio.sleep(3)
                    if balance is not None:
                        self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ {int(float(balance['data']['available_balance']))} $TOMA ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {balance['data']['play_passes']} ]{Style.RESET_ALL}"
                        )
                        if 'farming' in balance['data']:
                            if datetime.now().astimezone() >= datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone():
                                await self.farm_claim(token=token)
                            else:
                                farming_times.append(datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone().timestamp())
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farm Can Be Claim At {datetime.fromtimestamp(balance['data']['farming']['end_at']).astimezone().strftime('%X %Z')} ]{Style.RESET_ALL}")
                        else:
                            await self.farm_start(token=token)
                        total_balance += int(float(balance['data']['available_balance']))

                for (token, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Spin ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.spin_assets(token=token)
                    await asyncio.sleep(3)

                for (token, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home/Rank ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.rank_data(token=token)
                    await asyncio.sleep(3)

                for (token, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home/Play Passes ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.game_play(token=token)
                    await asyncio.sleep(3)

                for (token, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.tasks_list(token=token)
                    await self.tasks_puzzle(token=token)
                    await asyncio.sleep(3)

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
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} $TOMA ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=sleep_time)).strftime('%X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(sleep_time)
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
        tomarket.print_timestamp(
            f"{Fore.GREEN + Style.BRIGHT}[ 1 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT}[ Generate Tokens ]{Style.RESET_ALL}"
        )
        tomarket.print_timestamp(
            f"{Fore.GREEN + Style.BRIGHT}[ 2 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT}[ Use Existing accounts-*.json ]{Style.RESET_ALL}"
        )

        initial_choice = int(input(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}[ Select Option ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        ))
        if initial_choice == 1:
            lines_per_file = int(input(
                f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT}[ How Much Accounts In 'accounts-*.json'? ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            ))
            if lines_per_file <= 0:
                raise ValueError("The Number Must Be Greater Than Zero.")
            asyncio.run(tomarket.process_queries(lines_per_file=lines_per_file))

            account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
            account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
            if not account_files:
                raise FileNotFoundError("No 'accounts-*.json' Files Found In The Directory. Please Generate Tokens First By Selecting Option 1.")
        elif initial_choice == 2:
            account_files = [f for f in os.listdir() if f.startswith('accounts-') and f.endswith('.json')]
            account_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
            if not account_files:
                raise FileNotFoundError("No 'accounts-*.json' Files Found In The Directory. Please Generate Tokens First By Selecting Option 1.")
        else:
            raise ValueError("Invalid Initial Choice. Please Run The Script Again And Choose A Valid Option")

        for i, accounts_file in enumerate(account_files, start=1):
            tomarket.print_timestamp(
                f"{Fore.GREEN + Style.BRIGHT}[ {i} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}[ {accounts_file} ]{Style.RESET_ALL}"
            )

        choice = int(input(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}[ Select File You Want To Use ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        )) - 1
        if choice < 0 or choice >= len(account_files):
            raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

        selected_accounts_file = account_files[choice]
        accounts = asyncio.run(tomarket.load_from_json(selected_accounts_file))

        asyncio.run(tomarket.main(accounts))
    except (ValueError, IndexError, FileNotFoundError) as e:
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)