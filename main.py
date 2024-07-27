from colorama import Fore, Style, init
from time import sleep
from tomarket import Tomarket, print_timestamp
import sys


def main():
    init(autoreset=True)

    tom = Tomarket()

    with open('tokens.txt', 'r') as file:
        tokens = [line.strip() for line in file.readlines()]

    for index, token in enumerate(tokens):
        print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Account {index + 1} ]{Style.RESET_ALL}")
        balance = tom.balance(token=token)
        tom.tasks(token=token)
        tom.claim_daily(token=token)
        tom.start_farm(token=token)
        while balance['data']['play_passes'] > 0:
            tom.play_game(token=token)
            balance['data']['play_passes'] -= 1

    for _ in range(3 * 3600, 0, -1):
        hours, remainder = divmod(_, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"{Fore.YELLOW + Style.BRIGHT}[ {int(hours)} Hours {int(minutes)} Minutes {int(seconds)} Seconds Remaining To Process All Account ]{Style.RESET_ALL}", end="\r", flush=True)
        sleep(1)

    print('')


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {e} ]{Style.RESET_ALL}")
            pass
        except KeyboardInterrupt:
            sys.exit(0)