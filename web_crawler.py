""" Trystan Kaes
    Web Crawler
    March 25, 2020 """

import threading
import queue
import time
import re

from urllib.parse import urljoin, urlparse

import requests


URL = input("Enter webpage to crawl: ")

class WebPage:
    """ Class that handles all tasks related to the webpage """
    def __init__(self, url):
        self.url = url
        self.data = ""
        self.links = []
        self.status = ""
        self.error = False
        self.outbound = []

        response = ""

        try:
            response = requests.get(url=url, headers={'User-Agent': 'Trystans-crawler'})
        except requests.exceptions.RequestException as error:
            self.status = error
            self.error = True
        else:
            self.status = response.status_code

        self.data = response

    def parse_links(self):
        """ Searches through the webpage text and returns a list of href links """
        hrefs = list(set(re.findall(r'(?<=<a href=")(.*?)(?=\")', self.data.text)))
        self.links = list(map(lambda link: urljoin(self.url, link), hrefs))
        self.outbound = filter(lambda c: c[0] == 'h', hrefs) #log external links
        return self.links


URL_POOL = queue.Queue()
URL_UNIQUE = set()
NUM_THREADS = 8 #spideys got 8 legs
LOCK = threading.Lock()

URL_POOL.put(URL)
URL_UNIQUE.add(URL)


OUTPUT = open(urlparse(URL).hostname + ".csv", "w")

def now_crawl():
    """ This function loads the page, checks if the page is valid, logs the
        information, and adds links to the pool if they are inside the  page. """
    while True:

        new_page = WebPage(url=URL_POOL.get())

        with LOCK:
            OUTPUT.write('{:>120}    {}\n'.format(new_page.url, str(new_page.status)))
            print('{} is crawling {}'.format(threading.currentThread().getName(), new_page.url))

        if not new_page.error:
            latest_list = new_page.parse_links()
            #check base of the url to avoid crawling out to the internet
            if urlparse(new_page.url)[1] == urlparse(URL)[1]:
                for link in latest_list:
                    if link not in URL_UNIQUE:
                        with LOCK:
                            URL_POOL.put(link)
                            URL_UNIQUE.add(link)

        URL_POOL.task_done()
        if URL_POOL.empty(): #if the pool is empty
            time.sleep(1)
            if URL_POOL.empty():
                return

if __name__ == '__main__':
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=now_crawl)
        thread.start()

    URL_POOL.join()
    OUTPUT.close()

    print("\n[ The url:{} has been crawled. ]\n".format(URL))
