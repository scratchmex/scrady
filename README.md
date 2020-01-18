# scrAdy
A Python module intended for scraping ad webpages. Coded for Python 3.7.

## Uses the scrapy framework to parse and some modules like:
- phonenumbers
- scrapy-user-agents
- python-dotenv
- pipenv

## The info gathered is saved to a MongoDB via pipelines. See scrady/pipelines.py for setup details.
Some fields are:
- Price and currency
- Title
- Coordinates
- Description
- Phone Number
- Attributes
- Publisher profile

## The current implemented webpages are:
- vivanuncios.com.mx

You can view the current models in scrady/items.py

## Example
```
pipenv run scrapy vivanuncios
```