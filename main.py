import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def main(domain, output_file):
    # Create a set to store unique links found
    links = set()

    # Parse the domain to get the base URL
    base_url = urlparse(domain).scheme + '://' + urlparse(domain).netloc

    # Start with the domain URL and find all links on the page
    page_links = find_links(domain, base_url)
    links.update(page_links)

    # For each link found on the page, find all links on the page and add to the set
    for link in page_links:
        link_links = find_links(link, base_url)
        links.update(link_links)

    # Write the links to the output file and print them to the screen
    with open(output_file, 'w') as f:
        for link in links:
            f.write(link + '\n')
            print(link)

def find_links(url, base_url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links on the page
    page_links = set()
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            # Join the URL with the base URL to handle relative links
            absolute_url = urljoin(base_url, href)
            # Only add links from the same domain
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                page_links.add(absolute_url)

    return page_links

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain', required=True, help='Domain to search')
    parser.add_argument('-o', '--output', required=False, help='Output file')
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.domain, args.output)
