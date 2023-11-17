# Email Harvester
 Script to crawl a website and harvest email addresses. Email addresses are identified from `<a href="mailto:...">` tags, or text that matches common email format of `user@domain.tld` 
 
 It will crawl a site by following internal links recursively.  Logs the URL it visits in a .log file.  URLs that end with a common file extension like .jpg, .mov, .zip, etc are ignored, because they are most likely not text/html content and will not have any mailto: links. Results are saved to a .csv file with the columns: 
 
 * Email - The email address found
 * Text - The text content of the mailto: link
 * Context - The nearest or most likely descriptive text or heading in relation the the email address
 * URL  - The URL it was extracted from

 Usage example: `python .\src\emailharvester.py https://example.com/`

An existing .log file for a domain will inform the script of pages it has already completely crawled, so you can restart a crawl in progress.  To completely restart a crawl, delete or rename the .log and .csv files.

Progress will be printed to the console when a page crawl begins, when an email is found, and a summary table is displayed when a page crawl completes:

        ...
        Now crawling https://www.example.com/about/economicdevelopment.asp
        Found new address public-outreach@example.com
        Found a text string that looks like an email address: Manager@example.com
        Completed crawling about/economicdevelopment.asp:
                146     total links.
                0       newly discovered.
                104     already crawled.
                42      excluded.
                1       new emails found.
                1       existing emails skipped.
        Now crawling https://www.example.com/about/contact
        Completed crawling /about/contact:
                144     total links.
                0       newly discovered.
                104     already crawled.
                40      excluded.
                0       new emails found.
                0       existing emails skipped.
        Done. Visited 134 new URLs and skipped 322 existing.
        Found 92 total email addresses, 34 new.
        Duration: 0 days, 0 hrs, 2 mins and 30 secs