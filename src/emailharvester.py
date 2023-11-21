import requests
from bs4 import BeautifulSoup
from datetime import datetime
import queue
import sys
import csv
import time
import re
import os

# Require a URL as an argument
if not len(sys.argv) == 2:
    print(f'Missing required argument.  Provide a URL.\nUsage example: python {sys.argv[0]} https://site-to-crawl.com/contact/')
    exit(2)
base_url = sys.argv[1].lower()

# Set crawler user agent string
request_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
# Set max requests per second
crawl_rate = 5
# Set max depth of crawl
max_depth = 10
# Set common extentions to ignore that likely aren't text/html
excluded =['doc','docx','docm','ppt','ppsx','pptx','xls','xlsx','xlsm','accdb','png','jpg','jpeg','mov','mp4','wmv','gif','bmp','dgn','pdf','eps','ai','zip','dll','exe','rss','csv','txt']


# Verify the URL
try: response = requests.get(base_url, headers=request_headers)
except Exception as e:
    print(getattr(e, 'message', repr(e)))
    exit()
if not response.ok:
    print(f'Unable to crawl {base_url} - {response.status_code} {response.reason}')
    exit()

# Generate a filesystem-friendly name from the URL for results and log
filename = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", base_url.replace("http://", "").replace("https://", ""))
history_file = f'{filename}-history.log'
results_file = f'{filename}-emails.csv'

visited_urls = set()
email_set = set()

# Initialize results file if it doesn't exist
if not os.path.isfile(results_file):
    with open(results_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Email', 'Link Text', 'Context', 'URL'])

# Read existing results file for already-discovered emails
with open(results_file, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        email_set.add(row['Email'].lower())

# Initialize history file if it doesn't exist
if not os.path.isfile(history_file):
    with open(history_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp','URL'])

# Read existing history file for already-visited URLs
with open(history_file, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        visited_urls.add(row['URL'].lower())

# Breadth-first site crawling function definition (main loop)
def scrape_email_addresses(queue):
    while not queue.empty():
        work_item = queue.get()
        url = work_item[0]
        depth = work_item[1]
        try: response = requests.get(url, headers=request_headers)
        except Exception as e:
            print(f'REQUEST ERROR: {url}\n{getattr(e, 'message', repr(e))}')
            return
        # Confirm content type is html
        rtype = response.headers.get('content-type')
        if not rtype.startswith('text/html'):
            print(f'Not html content: {rtype}')
            return
        soup = BeautifulSoup(response.content, 'html.parser')
        total_links = len(soup.find_all('a', href=True))
        skipped_links = prior_links = new_links = email_links = prior_emails = 0
        # Find non-js and non-anchor links
        for link in soup.find_all("a", href=re.compile(r"^(?!javascript|#|tel|data|ftp)")):
            # Save mailto: links and continue
            if link.has_attr('href') and link['href'].startswith('mailto:'):
                email = link['href'][7:].split('?')[0].strip()            
                if email.lower() not in email_set:
                    email_links += 1
                    text = link.text.strip()
                    found_email(email, text, find_context(link, soup.title.text), url)
                    continue
                else:
                    prior_emails += 1
                    continue
            # Crawl non-mailto: links
            next_url = normalize_url(link.get('href'), url)
            # Skip visited URLs
            if next_url.lower() in visited_urls:
                prior_links += 1
                continue
            # Don't go deeper than max_depth
            if depth < 0:
                print(f'Crawling depth limit reached, skipping {next_url} from {url}')
                skipped_links += 1
                continue
            # Skip external sites and known file types
            if skip_url(next_url):
                skipped_links += 1
                continue
            # Rate limit crawler
            time.sleep(1/crawl_rate)
            visited_url(next_url)
            queue.put((next_url, depth-1))
            new_links += 1    

        # Check for any remaining emails not in a mailto:
        emails = reduce_generator(soup.stripped_strings)
        for email in emails:
            if email.lower() not in email_set:
                found_email(email, email, soup.title.text, url)

        # Print a summary after all links from a page have been checked
        print(f'Completed crawling {url.replace(base_url,'')} ({abs(-max_depth + depth)} levels from root):\n \
              \t{total_links}\ttotal links.\n \
              \t{new_links}\tnewly discovered.\n \
              \t{prior_links}\talready crawled.\n \
              \t{skipped_links}\texcluded.\n \
              \t{email_links}\tnew emails found.\n \
              \t{prior_emails}\texisting emails skipped.')

def normalize_url(url, referer):
    # Remove fragments
    url = url.split('#')[0].lower()
    # Remove extra directory slashes
    url = re.sub(r'(?<!:)//+','/', url)
    # Add base URL host to site relative URLs
    if url.startswith('/'):
        return re.match(r"https?://[^/]+",base_url).group(0) + url
    # Add referer to page relative URL without querystring params
    if not url.startswith('http'):
        return re.sub(r"(?<!/)$", "/", referer.split('?')[0]) + url
    return url  

# Determine if a URL should not be crawled
def skip_url(url):
     # Skip urls that are probably files eg /docs/service_terms.pdf?Page=1
     if url.split('.')[-1].split('?')[0].split('#')[0].lower() in excluded:
         return True
     # Consider optional www in URLs to be same base URL
     if not "://www." in base_url:
        url = url.replace("://www.", "://")
     # Skip external urls
     if not url.startswith(base_url):
        return True
     return False

# Write visited URL to log file and save in the global list
def visited_url(url):
    global visited_urls
    visited_urls.add(url.lower())
    row = [datetime.now().isoformat(), url]
    with open(history_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row)

# Write email to CSV file and save in the global list
def found_email(email, text, context, url):
    global email_set
    email_set.add(email.lower())
    print(f'Found new email address: {email}')
    row = [email, text, context, url]
    with open(results_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row)

# Find some text closest to the link
def find_context(link, fallback): 
    try:
        text = clean_txt(link.text)
        # Any adjacent text
        context = clean_txt(link.next_sibling.text) if link.next_sibling else ''
        if context in ['', text]:
            context = clean_txt(link.previous_sibling.text) if link.previous_sibling else ''
        parents = link.find_parents() if context == '' else []
        if context == '':
        # Any text in the next 5 ancestor elements
            context = parent_search(parents, 5)
        if context == '':
            context = clean_txt(fallback)
    except Exception as e:
        print(f'DEBUG: ERROR in find_context(link, fallback): {link}\n{getattr(e, 'message', repr(e))}')
        context = 'Error'
    return context

# Find short text sections without special punctuation or common words
def clean_txt(str):
    result = str.strip().split('\n')[0]
    result = re.sub(r"['\"|.;:`~#$%^&*]","",result)
    result = re.sub(re.compile(r'\b(Send|Email|Contact)\b', re.IGNORECASE),"",result).strip()
    return result if len(result) > 3 and len(result) < 60 else ''

# Locate short text content in the next N parent elements
def parent_search(parents, depth, i = None):
    if i is None:
        i = 0
    if not len(parents) > i:
        return ''
    text = clean_txt(parents[i].text)
    if not text == '' or i == depth:
        return text
    # Look only in headings if the full text didn't match
    text = clean_txt(parents[i].find(re.compile('^h[1-6]$')).text) if parents[i].find(re.compile('^h[1-6]$')) else ''
    return parent_search(parents, depth, i+1)

# Find all emails contained in text snippets
def reduce_generator(generator):
    hits = [re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',text) \
            for text in generator \
            if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)]
    unique_elements = set()
    for array in hits:
        for element in array:
            unique_elements.add(element)
    return list(unique_elements)

# Display difference between start and end timestamps
def print_time_delta(start_ts, end_ts):
    ts_diff = end_ts - start_ts
    secs = ts_diff.total_seconds()
    days, secs = divmod(secs, secs_per_day := 60*60*24)
    hrs, secs = divmod(secs, secs_per_hr := 60*60)
    mins, secs = divmod(secs, secs_per_min := 60)
    secs = round(secs, 2)
    print(f'Duration: {int(days)} days, {int(hrs)} hrs, {int(mins)} mins and {int(secs)} secs')

# Record starting performance statistics 
starting = datetime.now()
starting_urls = len(visited_urls)
starting_emails = len(email_set)
print(f'Starting with {starting_urls} URLs and {starting_emails} emails.')
visited_url(base_url)

# Enter the main program loop
queue = queue.Queue()
queue.put((base_url, max_depth))
scrape_email_addresses(queue)
                       
# Record ending performance statistics
ending = datetime.now()
total_emails = sum(1 for line in open(results_file, encoding='utf-8'))-1
print(f'Done. Visited {len(visited_urls)-starting_urls} new URLs and skipped {starting_urls} existing.\nFound {total_emails} total email addresses, {len(email_set)-starting_emails} new.')
print_time_delta(starting, ending)
