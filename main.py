import requests
import threading
from datetime import datetime, timezone
from queue import Queue
import random
import os

print("\033[38;5;88m" + r"""
                    ▓█████▄  ▄▄▄       ███▄ ▄███▓▓█████  ███▄    █
                    ▒██▀ ██▌▒████▄    ▓██▒▀█▀ ██▒▓█   ▀  ██ ▀█   █
                    ░██   █▌▒██  ▀█▄  ▓██    ▓██░▒███   ▓██  ▀█ ██▒
                    ░▓█▄   ▌░██▄▄▄▄██ ▒██    ▒██ ▒▓█  ▄ ▓██▒  ▐▌██▒
                    ░▒████▓  ▓█   ▓██▒▒██▒   ░██▒░▒████▒▒██░   ▓██░
                     ▒▒▓  ▒  ▒▒   ▓▒█░░ ▒░   ░  ░░░ ▒░ ░░ ▒░   ▒ ▒ 
                     ░ ▒  ▒   ▒   ▒▒ ░░  ░      ░ ░ ░  ░░ ░░   ░ ▒░
                     ░ ░  ░   ░   ▒   ░      ░      ░      ░   ░ ░ 
                       ░          ░  ░       ░      ░  ░         ░ 
                     ░                                             
""")


def read_tokens(filename):
    lines = []
    with open(filename, "r") as f:
        for line in f:
            if line.strip():
                lines.append(line.strip())
    return lines

input_lines = read_tokens("tokens.txt")
proxies = [p.strip() for p in open("proxies.txt") if p.strip()]
num_threads = int(input("Enter number of threads: "))

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_dir = f"Output/{timestamp}"
os.makedirs(output_dir, exist_ok=True)

url = "https://discord.com/api/v9/users/@me/billing/subscriptions?sync_level=1"
lock = threading.Lock()
q = Queue()
for line in input_lines:
    q.put(line)  # Keep full line: mail:pass:token

def get_headers(token):
    return {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Referer": "https://discord.com/channels/@me",
    }

def check_token(full_line):
    max_retries = 3
    token = full_line.split(":")[-1]  
    for attempt in range(max_retries):
        now = datetime.now().strftime("%H:%M:%S")
        proxy = {
            "http": "http://" + random.choice(proxies),
            "https": "http://" + random.choice(proxies),
        } if proxies else None

        try:
            response = requests.get(url, headers=get_headers(token), proxies=proxy, timeout=10)

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            data = response.json()
            if not data:
                with lock:
                    print(f"\033[1;90m{now} » \033[1;91mNO SUB • No Nitro ➔ [{token}]\033[0m")
                with open(f"{output_dir}/no_resub_period.txt", "a") as f:
                    f.write(full_line + "\n")
                return

            sub = data[0]
            metadata = sub.get("metadata", {})
            grace_date = metadata.get("grace_period_expires_date")
            current_end = sub.get("current_period_end")
            payment_source = sub.get("payment_source_id")

            if grace_date:
              grace_ends = datetime.fromisoformat(grace_date.replace("Z", "+00:00"))
              if datetime.now(timezone.utc) < grace_ends:
       

                expires_at = datetime.fromisoformat(grace_date.replace("Z", "+00:00"))
                days_left = (expires_at - datetime.now(timezone.utc)).days
                fname = f"{output_dir}/resub_period_ending_in_{days_left}_days.txt"
                with lock:
                    print(f"\033[1;90m{now} » \033[1;92mRESUB ACTIVE • Ends in {days_left}d ➔ [{token}]\033[0m TOKEN WILL NOT RESUBSCRIBE AGAIN")
                    with open(fname, "a") as f:
                        f.write(full_line + "\n")
                return

            elif payment_source and current_end:
                end_time = datetime.fromisoformat(current_end.replace("Z", "+00:00"))
                days_until = (end_time - datetime.now(timezone.utc)).days
                if days_until >= 0:
                    fname = f"{output_dir}/resub_period_will_start_in_{days_until}_days.txt"
                    with lock:
                        print(f"\033[1;90m{now} » \033[1;96mPENDING • Will enter resub period in {days_until}d ➔ [{token}]\033[0m")
                        with open(fname, "a") as f:
                            f.write(full_line + "\n")
                    return
                else:
                    raise Exception("Past grace or incomplete")

            else:
                raise Exception("No grace or payment source")

        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as proxy_error:
            if attempt < max_retries - 1:
                continue
            else:
                with lock:
                    print(f"\033[1;90m{now} » \033[1;91mRETRY FAIL • Proxy issue ➔ [{token}] ({proxy_error})\033[0m")
                with open(f"{output_dir}/no_resub_period.txt", "a") as f:
                    f.write(full_line + "\n")
                return

        except Exception as e:
            with lock:
                print(f"\033[1;90m{now} » \033[1;91mNON • No grace/resub ➔ [{token}] ({e})\033[0m")
            with open(f"{output_dir}/no_resub_period.txt", "a") as f:
                f.write(full_line + "\n")
            return

def worker():
    while not q.empty():
        line = q.get()
        check_token(line)
        q.task_done()

threads = []
for _ in range(num_threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
