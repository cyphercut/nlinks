import os
import sys
import time
import json
import random
import requests
import argparse
import contextlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Add a scheme to a URL if it's missing
def add_scheme_if_missing(url, scheme="https"):
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        return f"{scheme}://{url}"
    return url

# Generate random user agent headers
def get_random_headers():
    with open("user-agents.txt", "r") as f:
        user_agents = [line.strip() for line in f.readlines()]

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "close",
        "Upgrade-Insecure-Requests": "1",
    }

    return headers

# Get all links from a URL
def get_links(url):
    try:
        response = requests.get(url, headers=get_random_headers())
        soup = BeautifulSoup(response.content, "html.parser")
        links = set()

        # Find all anchor tags and extract the href attribute
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href:
                parsed_url = urljoin(url, href) # Combine the URL with the href to get the full URL
                links.add(parsed_url)
        return links
    except Exception as e:
        print(f"Error: {e}")
        return set()

# Process a URL and add all its links to the queue
def process_url(url, domain, visited_links, queue, output_file, links_set):
    # If the URL hasn't been visited before, process it
    if url not in visited_links:
        visited_links.add(url)
        links = get_links(url)
        for link in links:
            # Only add links with the same domain to the queue
            if urlparse(link).netloc == urlparse(domain).netloc and link not in visited_links:
                queue.append(link)
                visited_links.add(link)
                if link not in links_set:
                    links_set.add(link)
                    # Write the new link to the output file
                    with open(output_file, "a") as f:
                        f.write(f"{link}\n")

def main(domain, output_file, concurrency):
    try:
        domain_with_scheme = add_scheme_if_missing(domain, "https")
        visited_links = set()
        queue = [domain_with_scheme]
        links_set = set()

        # Load progress from a temporary file, if it exists
        tmp_dir = "tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        domain_without_scheme = domain_with_scheme.replace("https://", "").replace("http://", "")
        tmp_file = os.path.join(tmp_dir, f"{domain_without_scheme}.json")
        if os.path.exists(tmp_file):
            with open(tmp_file, "r") as f:
                data = json.load(f)
                visited_links = set(data["visited_links"])
                queue = data["queue"]
                links_set = set(data["links_set"])

        start_time = time.time()
        while queue:
            with contextlib.suppress(requests.exceptions.RequestException):
                with requests.Session() as session:
                    session.headers = get_random_headers()
                    url = queue.pop(0)
                    process_url(url, domain_with_scheme, visited_links, queue, output_file, links_set)
                    links = get_links(url)
                    for link in links:
                        if urlparse(link).netloc == urlparse(domain_with_scheme).netloc and link not in visited_links:
                            queue.append(link)
                            visited_links.add(link)
                            if link not in links_set:
                                links_set.add(link)
                                with open(output_file, "a") as f:
                                    f.write(f"{link}\n")

            # Clear the console and print some information about progress
            os.system('clear')
            print(f"\033[95mLast 10 links found:\033[0m\n{'-'*25}")
            unique_links = list(set(links_set))
            print("\n".join(unique_links[-10:]))
            print('-' * 80)
            print(f"\033[95mTotal unique URLs found:\033[0m {len(unique_links)}")
            end_time = time.time()
            print(f"\033[95mTime taken:\033[0m {end_time - start_time:.2f} seconds")
            time.sleep(1)

            # Save progress to tmp file
            with open(tmp_file, "w") as f:
                data = {
                    "visited_links": list(visited_links),
                    "queue": queue,
                    "links_set": list(links_set),
                }
                json.dump(data, f)
    # Handle the case where the user interrupts the program with Ctrl+C
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Interrupted by user. Exiting...{Style.RESET_ALL}")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect URLs from a domain.")
    parser.add_argument("-d", "--domain", required=True, help="Domain to collect URLs from.")
    parser.add_argument("-o", "--output", required=False, help="Output file to save the URLs.")
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent threads to use for processing URLs.",
    )
    args = parser.parse_args()

    # Call the main function with the command line arguments
    try:
        main(args.domain, args.output, args.concurrency)
    # Handle the case where the user interrupts the program with Ctrl+C
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(0)
