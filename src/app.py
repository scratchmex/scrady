import time
import logging
from scrapper import parse_ad_url, get_all_ads
from multiprocessing import Pool, cpu_count
from functools import partial


if __name__ == "__main__":
    date = time.strftime('%d-%m-%Y-%H_%M_%S')
    logging.basicConfig(filename='logs/{}.log'.format(date), level=logging.DEBUG)
    logInst = logging.getLogger()
    logInst.addHandler(logging.StreamHandler())
    logInst.setLevel(logging.INFO)
    
    url = 'https://www.vivanuncios.com.mx/s-renta-inmuebles/solidaridad/v1c1098l11804p1'
    
    ads_url = get_all_ads(url, limit=99)
    datalist = list(ads_url)
    logging.info('Got {} ads to parse'.format(len(datalist)))
    parse_multi = partial(parse_ad_url, save_to_db=True)
    
    #start pool
    threads_num=cpu_count()-1
    pool = Pool(threads_num)
    logging.info('starting {} pool..'.format(threads_num))
    pool.map(parse_multi, datalist)
