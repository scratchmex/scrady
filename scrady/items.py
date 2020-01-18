# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.exceptions import DropItem
from warnings import warn
from hashlib import sha1


class ScradyItem(Item):
    # define the fields for your item here like:
    # name = Field()
    pass

class BaseAd(Item):
    '''Base ad class.
    
    Fields:
        url:the url parsed from
        id:sha1 hash of url
        type:estate,vehicles,media,fashion,services,employment 
    
    The subclasses must override is_valid method while calling it from super. See the is_valid method for details.
    Example:
        def is_valid(self):
            super().validate()
            # Your validations here
    '''
    # Set fields and required here
    url=Field()
    id=Field()
    type=Field()

    required_fields=[
        'url',
        'id',
        'type'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self['type']:
            raise NotImplementedError('type of ad must be set as static class variable')
        #use url hash as id to avoid duplicates
        self['id']=sha1(self.get('url').encode()).hexdigest()

    def validate_variables(self, obj, objname, required_vars):
        '''Function to validate if a variable is set on a class. 
        
        If the variable not in object scrapy.DropItem is raised.
        See implementations for details.

        Example:
            validate_variables(self, self.__class__.__name__, required_fields)
            validate_variables(price, 'price', ('amount', 'currency'))
        '''
        for var in required_vars:
            if not obj.get(var):
                DropItem(f'<{objname}> is missing <{var}>. URL: <{self.get("url", "empty")}>')

    def is_valid(self):
        # Please call super validate function in subclasses
        # super().validate()
        my_name=self.__class__.__name__ # get the actual classname of children
        if not self.get('id'):
            warn(f'<{my_name}> missing id. Setting it myself', RuntimeWarning)
            self['id']=sha1(self['url'].encode()).hexdigest()

        self.validate_variables(self, my_name, self.required_fields)

class PropertyAd(BaseAd):
    '''Property class for ads about real estate.

    Fields:
        type:estate. Real estate type of ad. Do not change!.
        category:rent,vacational_rent,sell
        estate_type:house,department,land,building
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
            type:agency,particular
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
    geocoordinates=Field({
        'latitude': Field(),
        'longitude': Field()
    })
    description=Field()
    phone=Field()
    seller=Field({
        'name': Field(),
        'url': Field(),
        'type': Field,
    })
    attributes=Field({
        'numberBathrooms': Field(),
        'numberBedrooms': Field(),
        'areaInMeters': Field(),
        'parking': Field(),
        'numberFloors': Field(),
    })

    required_fields=[
            'type',
            'category',
            'estate_type',
            'title',
            'price',
            'description'
        ]
    
    def is_valid(self):
        super().is_valid()
        my_name=self.__class__.__name__
        
        self.validate_variables(self, my_name, self.required_fields)
        self.validate_variables(self['price'], 'price', (
            'amount',
            'currency'
        ))
        self.validate_variables(self['geocoordinates'], 'geocoordinates', (
            'latitude',
            'longitude'
        ))