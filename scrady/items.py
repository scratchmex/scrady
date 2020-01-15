# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ScradyItem(Item):
    # define the fields for your item here like:
    # name = Field()
    pass

class BaseAd(Item):
    '''Base ad class.
    
    Fields:
        url:the url parsed from
        id:hashed by url
        type:estate,vehicles,media,fashion,services,employment 
    '''
    url=Field()
    id=Field()
    type=Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.type:
            raise NotImplementedError('type of ad must be set')
        #use url hash as id to avoid duplicates
        self.id=hash(self.url)

class PropertyAd(BaseAd):
    '''Property class for ads about real estate.

    Fields:
        type:estate. Real estate type of ad. Do not change!.
        category:rent,vacational_rent,buy
        estate_type:house,department,terrain,building
        title:str
        price:
            amount:float
            currency:float. Must follow ISO4217. Example MXN
        geocoordinates:
            latitude:float
            longitude:float
        description:str
        phone:int. With country code and no spaces. Example 529841234455
        seller:
            name:str
            url:full url to profile
            type:agency,partiular
        attributes:
            numberBathrooms:int
            numberBedrooms:int
            areaInMeters:int
            parking:int. Number of cars that fit on parking slot.
            numberFloors:int

    '''
    type='estate'
    category=Field()
    estate_type=Field()
    title=Field()
    price=Field({
        'amount': Field(),
        'currency': Field()
    })
    geocoordinates={
        'latitude': Field(),
        'longitude': Field()
    }
    description=Field()
    phone=Field()
    seller={
        'name': Field(),
        'url': Field(),
        'type': Field,
    }
    attributes=Field({
        'numberBathrooms': Field(),
        'numberBedrooms': Field(),
        'areaInMeters': Field(),
        'parking': Field(),
        'numberFloors': Field(),
    })

    