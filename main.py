from colorama import Fore, Style, init
from time import sleep
from tomarket import Tomarket, print_timestamp
import sys


def main():
    init(autoreset=True)

    tom = Tomarket()
    tokens = tom.user_login()

    for (token, username) in tokens:
        print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {username} ]{Style.RESET_ALL}")
        tom.claim_daily(token=token)
        tom.user_balance(token=token)
        tom.start_farm(token=token)
        tom.list_tasks(token=token)

    delay = int(4 * 3600)
    hours, remainder = divmod(delay, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"{Fore.YELLOW + Style.BRIGHT}[ Restarting In {int(hours)} Hours {int(minutes)} Minutes {int(seconds)} Seconds ]{Style.RESET_ALL}")
    sleep(delay)


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")
        except KeyboardInterrupt:
            sys.exit(0)