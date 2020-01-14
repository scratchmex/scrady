from pymongo import MongoClient


class scrapMongoClient(MongoClient):
    #Database name
    db_name = 'vivanuncios'
    #Table to save scraped data
    scrap_table = 'scraped-data'
    
    def __init__(self, *args, **kwargs):
        #Config host here
        kwargs['host'] = '10.0.0.5'
        #Config port here
        kwargs['port'] = None
        super().__init__(*args, **kwargs)
        
    def getTable(self):
        db = self[self.db_name]
        table = db[self.scrap_table]
        
        return table
    
    def getDB(self):
        db = self[self.db_name]
        
        return db
    
    def isAdCaptured(self, ad_url):
        #Verify existant ad
        pass