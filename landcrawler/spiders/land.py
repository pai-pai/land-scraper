"""Module contains next spiders:

LandsForSaleSpider -- to find them all,
BrokerProfileSpider and PropertyDetailsSpider -- to bring them all.

"""
import json
import logging
import re
import pathlib
import scrapy


DOMAIN = "www.landwatch.com"
BROKER_LINKS_FILE = pathlib.Path('broker_links.csv')
BROKER_DETAILS_FILE = pathlib.Path('broker_details.csv')
PROPERTY_LINKS_FILE = pathlib.Path('property_links.csv')
PROPERTY_DETAILS_FILE = pathlib.Path('property_details.csv')

STATUSES = {
    1: "Available",
    2: "Under Contract",
    3: "Off Market",
    4: "Sold",
}
ADDRESS_FIELDS = ['address1', 'address2', 'city', 'state', 'zip']


def _script_string_to_json_prep(script_string: str, link: str):
    prep = re.findall('window.serverState = "(.*)";', script_string)
    if not prep:
        logging.warning(
            "Can not find 'window.serverState' inside passed script text at the page %s.",
            link
        )
        return None
    prep = prep[0]
    prep = re.sub(r'([:,\[\{])\\+"', r'\1"', prep)
    prep = re.sub(r'\\+"([:,\]\}])', r'"\1', prep)
    prep = re.sub(r'\\+"', r'\"', prep)
    prep = re.sub(r'(encodedBoundaryPoints":)(".*?")', r'\1""', prep)
    prep = prep.replace('"{', '{').replace('}"', '}')
    return prep


class LandsForSaleSpider(scrapy.Spider):
    """Spider which collects item and broker profile links for every listing.

    """
    name = "landwatch-spider"
    domain = DOMAIN
    allowed_domains = [domain]
    custom_settings = {
        'FEEDS': {
            BROKER_LINKS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': ['profile_link'],
            },
            PROPERTY_LINKS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': ['link'],
            },
        }
    }

    def start_requests(self):
        urls = [
            'https://www.landwatch.com/land',
            'https://www.landwatch.com/farms-ranches',
            'https://www.landwatch.com/hunting-property',
            'https://www.landwatch.com/homesites',
            'https://www.landwatch.com/homes',
            'https://www.landwatch.com/undeveloped-land',
            'https://www.landwatch.com/waterfront-property',
            'https://www.landwatch.com/lakefront-property',
            'https://www.landwatch.com/commercial-property',
            'https://www.landwatch.com/recreational-property',
            'https://www.landwatch.com/land/owner-financing',
            'https://www.landwatch.com/timberland-property',
            'https://www.landwatch.com/horse-property',
            'https://www.landwatch.com/riverfront-property',
            'https://www.landwatch.com/land/auctions',
            'https://www.landwatch.com/oceanfront-property',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        item_containers = response.css('div._51c43')
        for item_container in item_containers:
            yield {
                "link": item_container.css('div._12a2b').xpath('a/@href').get(),
                "profile_link": item_container.css('div.dc7c2').xpath('a/@href').get(),
            }
        next_page_url = response.css('a.d72c6:last-child').xpath('@href').get()
        if next_page_url is not None:
            yield scrapy.Request(url=f'https://{self.domain}/{next_page_url}')


class BrokerProfileSpider(scrapy.Spider):
    """Spider which collects broker profile details.

    """
    name = "broker-details-spider"
    domain = DOMAIN
    allowed_domains = [domain]
    address_fields = dict(zip(
        ADDRESS_FIELDS,
        ['companyAddress1', 'companyAddress2', 'companyCity', 'companyState', 'companyZip']
    ))
    custom_settings = {
        'FEEDS': {
            BROKER_DETAILS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': [
                    'link', 'contactName', 'companyName', 'phoneCell',
                    'phoneOffice', 'email', 'companyWebsite',
                ] + ADDRESS_FIELDS,
            },
        }
    }

    def start_requests(self):
        with open(BROKER_LINKS_FILE, 'r', encoding='utf-8') as links_file:
            for index, link in enumerate(links_file):
                if index == 0:
                    continue
                link = link.replace("\n", "")
                if link:
                    yield scrapy.Request(f'https://{self.domain}{link}', callback=self.parse)

    def parse(self, response, **kwargs):
        link = response.url
        item = {
            'link': link,
        }
        script_text = response.xpath(
            '//script[contains(text(), "brokerDetails")]/text()').get()
        page_data_prep = _script_string_to_json_prep(script_text, link)
        try:
            broker_details = re.findall(
                r'"breadCrumbSchema":.+?,"brokerDetails":(.*),"carouselCounts"', page_data_prep)[0]
            broker_details = re.sub(
                r'"description":((?:(?!"description":).)*?),"email"',
                r'"description":"","email"',
                broker_details
            )
            broker_details = json.loads(broker_details)
            if broker_details:
                item['contactName'] = broker_details.get('contactName', '')
                item['companyName'] = broker_details.get('companyName', '')
                item['phoneCell'] = broker_details.get('phoneCell', '')
                item['phoneOffice'] = broker_details.get('phoneOffice', '')
                item['email'] = broker_details.get('email', '')
                item['companyWebsite'] = broker_details.get('url', '')
                for item_field, field in self.address_fields.items():
                    item[item_field] = broker_details.get(field, '')
            else:
                logging.info("Broker page %s is empty.", response.url)
        except (IndexError, ValueError):
            logging.error(
                "Something is wrong with 'window.serverState' content of broker page %s.",
                link
            )
        yield item


class PropertyDetailsSpider(scrapy.Spider):
    """Spider which collects property details.

    """
    name = "property-details-spider"
    domain = DOMAIN
    allowed_domains = [domain]
    address_fields = dict(zip(
        ADDRESS_FIELDS,
        ['address1', 'address2', 'city', 'stateAbbreviation', 'zip']
    ))
    home_fields = ['homesqft', 'beds', 'baths', 'halfBaths']
    custom_settings = {
        'FEEDS': {
            PROPERTY_DETAILS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': [
                    'link', 'brokerLink', 'status', 'title', 'price', 'acres',
                ] + ADDRESS_FIELDS + home_fields + [
                    'type', 'propertyWebsite',
                ],
            },
        }
    }

    def start_requests(self):
        with open(PROPERTY_LINKS_FILE, 'r', encoding='utf-8') as links_file:
            for index, link in enumerate(links_file):
                if index == 0:
                    continue
                link = link.replace("\n", "")
                if link:
                    yield scrapy.Request(f'https://{self.domain}{link}', callback=self.parse)

    def parse(self, response, **kwargs):
        link = response.url
        item = {
            'link': link,
            'brokerLink': response.css('a.d51ec').xpath('@href').get(),
        }
        script_text = response.xpath(
            '//script[contains(text(), "propertyDetailPage")]/text()').get()
        page_data_prep = _script_string_to_json_prep(script_text, link)
        try:
            property_details = re.findall(
                r'"propertyData":(.*),"propertyEvents"', page_data_prep)[0]
            property_details = re.sub(
                r'"description":((?:(?!"description":).)*?),"directions"',
                r'"description":"","directions"',
                property_details
            )
            property_details = re.sub(
                r'"breadcrumbSchema.*smallMapUrl',
                r'"smallMapUrl',
                property_details
            )
            property_details = json.loads(property_details)
            if property_details:
                item['status'] = STATUSES.get(property_details.get('status', ''))
                item['title'] = property_details.get('title', '')
                item['price'] = property_details.get('price', '')
                item['acres'] = property_details.get('acres', '')
                if property_details.get('address'):
                    for item_field, field in self.address_fields.items():
                        item[item_field] = property_details['address'].get(field, '')
                for field in self.home_fields:
                    item[field] = property_details.get(field, '')
                item['type'] = ', '.join(property_details.get('types', []))
                item['propertyWebsite'] = property_details.get('externalLink', '')
        except (IndexError, ValueError):
            logging.error(
                "Something is wrong with 'window.serverState' content of property page %s.",
                link
            )
        yield item
