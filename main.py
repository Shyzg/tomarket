from colorama import Fore, Style, init
from tomarket import Tomarket, print_timestamp
import sys
import asyncio


async def main():
    init(autoreset=True)

    tom = Tomarket()
    tokens = await tom.user_login()

    for (token, username) in tokens:
        print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {username} ]{Style.RESET_ALL}")
        await tom.claim_daily(token=token)
        await tom.user_balance(token=token)
        await tom.start_farm(token=token)
        await tom.list_tasks(token=token)

    print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting Soon ]{Style.RESET_ALL}")
    await asyncio.sleep(2 * 3600)


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
        except KeyboardInterrupt:
            sys.exit(0)
