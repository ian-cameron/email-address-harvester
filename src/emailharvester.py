import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import csv
import time
import re
import os

# Require a URL as an argument
if not len(sys.argv) == 2:
    print(f'Missing required argument.  Provide a URL.\nUsage example: python {sys.argv[0]} https://site-to-crawl.com/contact/')
    exit(2)
base_url = sys.argv[1]
request_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

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

# Don't visit urls that end with common file extensions, you'd have to download them and they very likely aren't text/html
excluded =['doc','docx','docm','ppt','ppsx','pptx','xls','xlsx','xlsm','accdb','png','jpg','jpeg','mov','mp4','wmv','gif','bmp','dgn','pdf','eps','ai','zip','dll','exe','rss','csv','txt']

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

# Recursive function definition
def scrape_email_addresses(url):
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
    for link in soup.find_all('a', href=True):
        # Save mailto: links and continue on
        if link.has_attr('href') and link['href'].startswith('mailto:'):
            email = link['href'][7:].split('?')[0].strip()            
            if email.lower() not in email_set:
                email_links += 1
                text = link.text.strip()
                found_email(email, text, find_context(link, soup.title.text), url)
            else:
                prior_emails += 1
                continue
        # Ignore URL fragments
        next_url = link.get('href').split('#')[0]
        # Skip external sites and known file types
        if next_url.split('.')[-1].split('?')[0].split('#')[0].lower() in excluded or not next_url.startswith('/') and not next_url.startswith(base_url):
            skipped_links += 1
            continue
        next_url = re.sub(r'(?<!:)//','/',base_url + next_url.replace(base_url,'/'))
        # Skip visited URLs
        if next_url.lower() in visited_urls:
            prior_links += 1
            continue
        visited_url(next_url)
        time.sleep(0.2)
        print(f'Now crawling {next_url}') 
        new_links += 1    
        scrape_email_addresses(next_url)
    # Check for any remaining emails not from mailto.
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())
    for email in emails:
        if email.lower() not in email_set:
            found_email(email, email, soup.title.text, url)

    # Print a summary after all links from a page have been checked
    print(f'Completed crawling {url.replace(base_url,'')}:\n\t{total_links}\ttotal links.\n\t{new_links}\tnewly discovered.\n\t{prior_links}\talready crawled.\n\t{skipped_links}\texcluded.\n\t{email_links}\tnew emails found.\n\t{prior_emails}\texisting emails skipped.')          

def visited_url(url):
    global visited_urls
    visited_urls.add(url.lower())
    row = [datetime.now().isoformat(), url]
    with open(history_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row)

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
        context = clean_txt(link.next_sibling.text) if link.next_sibling else ''
        if context == '':
            context = clean_txt(link.previous_sibling.text) if link.previous_sibling else ''
        if context == '':
            context = clean_txt(clean_txt(link.parent.text.replace(link.text,'')))
        parents = link.find_parents() if context == '' else []
        if context == '':
            context = clean_txt(parents[1].find(re.compile('^h[1-6]$')).text) if len(parents) >= 2 and parents[1].find(re.compile('^h[1-6]$')) else ''
        if context == '':
            context = clean_txt(parents[2].find(re.compile('^h[1-6]$')).text) if len(parents) >= 3 and parents[2].find(re.compile('^h[1-6]$')) else ''
        if context == '':
            context = clean_txt(parents[3].find(re.compile('^h[1-6]$')).text) if len(parents) >= 4 and parents[3].find(re.compile('^h[1-6]$')) else ''         
        if context == '':
            context = clean_txt(parents[4].find(re.compile('^h[1-6]$')).text) if len(parents) >= 5 and parents[4].find(re.compile('^h[1-6]$')) else ''
        if context == '':
            context = clean_txt(parents[5].find(re.compile('^h[1-6]$')).text) if len(parents) >= 6 and parents[5].find(re.compile('^h[1-6]$')) else ''
        if context == '':
            context = clean_txt(link.find_parent('tr').find('td').text) if link.find_parent('tr') and link.find_parent('tr').find('td') else ''
        if context == '':
            context = clean_txt(fallback)
    except Exception as e:
        print(f'DEBUG: ERROR in find_context(link, fallback): {link}\n{getattr(e, 'message', repr(e))}')
        context = 'Error'
    return context

def clean_txt(str):
    result = str.strip().split('\n')[0]
    result = re.sub(r"['\",|.;`~#$%^&*]","",result)
    result = re.sub(re.compile(r'email:?', re.IGNORECASE),"",result).strip()
    return result if len(result) > 3 and len(result) < 60 else ''

def print_time_delta(start_ts, end_ts):
    ts_diff = end_ts - start_ts
    secs = ts_diff.total_seconds()
    days, secs = divmod(secs, secs_per_day := 60*60*24)
    hrs, secs = divmod(secs, secs_per_hr := 60*60)
    mins, secs = divmod(secs, secs_per_min := 60)
    secs = round(secs, 2)
    print(f'Duration: {int(days)} days, {int(hrs)} hrs, {int(mins)} mins and {int(secs)} secs')

starting = datetime.now()
starting_urls = len(visited_urls)
starting_emails = len(email_set)
print(f'Starting with {starting_urls} URLs and {starting_emails} emails.')
visited_url(base_url)
scrape_email_addresses(base_url)
ending = datetime.now()
total_emails = sum(1 for line in open(results_file, encoding='utf-8'))-1
print(f'Done. Visited {len(visited_urls)-starting_urls} new URLs and skipped {starting_urls} existing.\nFound {total_emails} total email addresses, {len(email_set)-starting_emails} new.')
print_time_delta(starting, ending)
