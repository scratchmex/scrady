from selenium import webdriver
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import logging
import re
from db import scrapMongoClient


class scrapWebdriverChrome(webdriver.Chrome):
    def __init__(self, *args, **kwargs):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1280x720")
        executable_path = '/usr/lib/chromium-browser/chromedriver'
        kwargs['chrome_options'] = chrome_options
        kwargs['executable_path'] = executable_path
        super().__init__(*args, **kwargs)  
        
    def getSoup(self):
        soup = BeautifulSoup(self.page_source, 'lxml')
        
        return soup
    
class scrapWebdriverPhantomJS(webdriver.PhantomJS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_window_size(1280, 720)
        
    def getSoup(self):
        soup = BeautifulSoup(self.page_source, 'lxml')
        
        return soup

    
class error_handler:
    r_if_e = None
    def_except = Exception
    def __init__(self, r_if_e=None, def_except=Exception):
        self.r_if_e = r_if_e
        self.def_except = def_except
        
    def __call__(self, f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except self.def_except as e:
                logging.exception('error_handler class catch up an error:')
                e_txt = '"{}" func had an error with args #####{}##### and kwargs: #####{}#####'
                logging.debug(e_txt.format(f, args, kwargs))
                
                return self.r_if_e
        return wrapper

def get_html(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'lxml')
                    
    return soup

@error_handler(r_if_e={}, def_except=AttributeError)
def get_ads(soup):
    links = soup.find('div', {'id':'tileRedesign'}).find_all('meta', {'itemprop':'url'})
    ads = {i.get('content') for i in links}

    return ads

@error_handler(r_if_e=str(), def_except=AttributeError)
def get_next_page(soup):
    nxt_p = soup.find('div', {'class':'desktop-pagination'})
    nxt_p = nxt_p.find(re.compile(r'(a|span)'), {'class':re.compile(r'pag-box current-page')})
    nxt_p = nxt_p.find_next('a', {'class':'pag-box'}).get('href')

    return nxt_p

@error_handler
def save_json(data, filename):
    import json
    with open(filename, 'w') as f:
        json.dump(data, f)
        logging.info('Saving to {}...'.format(filename))
        
#@error_handler(r_if_e=set())
def get_all_ads(url, limit=30):
    ads = set()
    
    for i in range(limit):                    
        logging.info('{} - link: {}'.format(i+1, url))       
        if not url:
            logging.info('URL empty. Exiting loop...')
            break
            
        soup = get_html(url)
        ads.update(get_ads(soup))
        #next url
        next_url = get_next_page(soup)
        url = urljoin(url, next_url) if next_url else None
        
    #save_json({'ads':list(ads), 'urls':list(visited)}, date+'.data')
    return ads

@error_handler(r_if_e={}, def_except=AttributeError)
def parse_ad_soup(ad_url, soup):
    logging.info('Parsing ad.. {}'.format(ad_url))
    data = {}

    #useful funcs
    parse_cat = lambda soup: re.search(r'icon-(\w+)', soup.find('i')['class'][1]).group(1)

    #get ad content
    ad_content = soup.find('div', {'class':'revip-content'})

    ## Start getting data
    data['link'] = ad_url
    data['title'] = ad_content.find('div', {'class':'title'}).text
    data['profile'] = ad_content.find('div', {'class':'profile-username'}).text
    data['profile-link'] = urljoin(ad_url, ad_content.find('a').get('href'))
    data['description'] = ad_content.find('div', {'class':'description-content'}).get_text('\n')

    #parse price
    price = ad_content.find('span', {'class':'ad-price'}).text
    currency = re.search(r'[A-Z]{3}', price)
    price_p = re.search(r'\d+(,\d{3})+', price)
    price_p = price_p.group() if price_p else ''
    price_p = price_p.replace(',', '')
    data['price'] = {'value':price_p, 'currency':currency.group() if currency else 'MXN'}

    #extract categories
    categories = ad_content.find('div', {'class':'category-container'}).find_all('div', {'class':'category'})

    ad_type = categories.pop(0)
    data['type-link'] = ad_type.find('a').get('href')
    data['type'] = parse_cat(ad_type)

    for cat in categories:
        attr = parse_cat(cat)
        val = cat.find('span', {'class':'pri-props-value'}).text
        data[attr] = val
        
    #extract map coords
    map_url = ad_content.find('img', {'class':'signed-map-image'}).get('src')
    data['coords'] = re.search(r'center=(.*?)&', map_url).group(1)
    
    #get phone number
    data['phone'] = soup.find('span', {'class':'real-phone'}).text
    
    return data

def parse_ad_url(ad_url, save_to_db=False):
    logging.debug('Initializing webdriver..')
    wb = scrapWebdriverPhantomJS()
    try:
        wb.get(ad_url)
        #reveal phone number
        wb.find_element_by_xpath('//span[@class="display-phone"]').click()
        #get soup
        soup = wb.getSoup()
    except Exception as e:
        logging.exception('Fatal error in WebDriver:')
        return 
    finally:
        #closing webdriver
        wb.quit()
    
    ad_data = parse_ad_soup(ad_url, soup)
    
    if save_to_db and ad_data:
        try:
            logging.info('Saving parsed ad to db')
            mongo_conn = scrapMongoClient()
            mongo_table = mongo_conn.getTable()
            mongo_table.insert_one(ad_data)
        except Exception as e:
            logging.exception('Fatal error, ad_data={}'.format(ad_data))
    
    return ad_data if not save_to_db else None
