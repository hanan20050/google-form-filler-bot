#!/usr/bin/env python3
import re
import sys
import time
import random
import argparse
import requests

# ==============================================================================
# CONFIGURATION FOR YOUR SPECIFIC GOOGLE FORM
# ==============================================================================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScxrgkZSczQo_I7-tYIXjarPnG2vtSCReDhlqd8HlHzXePEPA/viewform"
ENTRY_ID_NAME = "entry.129147722"  # Field name: "Name" (Multiple Choice)

# List of common User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def generate_random_ip():
    """Generates a random public IPv4 address."""
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def fetch_free_proxies():
    """Fetches a list of free HTTP proxies from public APIs."""
    urls = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    proxies = []
    print("[*] Fetching free public proxies...")
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                found = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b", resp.text)
                proxies.extend(found)
                if proxies:
                    break  # Stop if we got proxies successfully
        except Exception as e:
            print(f"[-] Failed to fetch proxies from {url}: {e}")
    
    # Deduplicate
    proxies = list(set(proxies))
    print(f"[+] Loaded {len(proxies)} free proxies.")
    return proxies

def load_proxies_from_file(file_path):
    """Loads proxies from a text file, one per line."""
    proxies = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Extract ip:port pattern if present
                match = re.search(r"(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b)", line)
                if match:
                    proxies.append(match.group(1))
                else:
                    proxies.append(line)
        print(f"[+] Loaded {len(proxies)} proxies from {file_path}")
    except Exception as e:
        print(f"[-] Error reading proxy file {file_path}: {e}")
    return proxies

def fill_and_submit(option_value, count=5, delay=1.0, proxies_list=None):
    session = requests.Session()
    
    success_count = 0
    # The loop runs 'count' times to submit the entry that many times
    i = 1
    while i <= count:
        random_ip = generate_random_ip()
        user_agent = random.choice(USER_AGENTS)
        
        headers = {
            "User-Agent": user_agent,
            "X-Forwarded-For": random_ip,
            "X-Real-IP": random_ip,
            "Client-IP": random_ip,
            "Referer": FORM_URL,
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        # Configure proxy if available
        current_proxy = None
        if proxies_list:
            current_proxy = random.choice(proxies_list)
            # Format proxy as dict
            proxy_url = current_proxy
            if not proxy_url.startswith("http"):
                proxy_url = f"http://{proxy_url}"
            session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            proxy_display = f"Proxy: {current_proxy}"
        else:
            session.proxies = {}
            proxy_display = f"Spoofed IP: {random_ip}"

        fbzx = None
        # Periodically or on proxy change, fetch new page to update fbzx tokens
        print(f"[*] Submission {i}/{count}: Fetching form page using {proxy_display}...")
        try:
            r = session.get(FORM_URL, headers=headers, timeout=10)
            if r.status_code != 200:
                print(f"[-] Failed to retrieve form: status code {r.status_code}")
                if proxies_list and len(proxies_list) > 1:
                    print("[-] Retrying with a different proxy...")
                continue
            html = r.text
            fbzx_match = re.search(r'name="fbzx"\s+value="([^"]+)"', html)
            fbzx = fbzx_match.group(1) if fbzx_match else None
        except Exception as e:
            print(f"[-] Network error retrieving form: {e}")
            if proxies_list and len(proxies_list) > 1:
                print("[-] Retrying with a different proxy...")
            continue

        submit_url = FORM_URL.replace("/viewform", "/formResponse")
        
        payload = {
            ENTRY_ID_NAME: option_value,
            "fvv": "1",
            "pageHistory": "0",
        }
        if fbzx:
            payload["fbzx"] = fbzx
            
        submit_headers = headers.copy()
        submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        print(f"[*] Submitting '{option_value}'...")
        try:
            resp = session.post(submit_url, data=payload, headers=submit_headers, timeout=10)
            if resp.status_code == 200:
                print(f"[+] Submission {i} successful!")
                success_count += 1
                i += 1
            else:
                print(f"[-] Submission {i} failed with status code: {resp.status_code}")
                if proxies_list and len(proxies_list) > 1:
                    print("[-] Retrying with a different proxy...")
                else:
                    i += 1
        except Exception as e:
            print(f"[-] Network/Timeout error on submission {i}: {e}")
            if proxies_list and len(proxies_list) > 1:
                print("[-] Retrying with a different proxy...")
            else:
                i += 1
        
        if i <= count and delay > 0:
            time.sleep(delay)
            
    print(f"\n[+] Completed! Successful submissions: {success_count}/{count}")
    return success_count > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-fill the Google Form with spoofed IP headers or real proxies.")
    parser.add_argument("--value", type=str, default="Option 1",
                        help="The choice to submit (e.g., 'Option 1').")
    # The --count command-line argument specifies how many times to submit
    parser.add_argument("--count", type=int, default=5,
                        help="Number of times to submit.")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay in seconds between submissions.")
    parser.add_argument("--proxy-file", type=str, default=None,
                        help="Path to a text file containing proxies (one per line, format: ip:port).")
    parser.add_argument("--fetch-proxies", action="store_true",
                        help="Fetch free public proxies automatically for rotation.")
    args = parser.parse_args()
    
    proxies = None
    if args.proxy_file:
        proxies = load_proxies_from_file(args.proxy_file)
    elif args.fetch_proxies:
        proxies = fetch_free_proxies()
        
    fill_and_submit(args.value, args.count, args.delay, proxies)

