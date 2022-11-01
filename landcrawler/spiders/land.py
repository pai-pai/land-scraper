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

LISTING_LINKS_FILE = pathlib.Path('listing_links.csv')
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


def _script_string_to_json_prep(script_string: str, page_url: str):
    prep = re.findall('window.serverState = "(.*)";', script_string)
    if not prep:
        logging.warning(
            "Can not find 'window.serverState' inside passed script text at the page %s.",
            page_url
        )
        return None
    prep = prep[0]
    prep = re.sub(r'([:,\[\{])\\+"', r'\1"', prep)
    prep = re.sub(r'\\+"([:,\]\}])', r'"\1', prep)
    prep = re.sub(r'\\+"', r'\"', prep)
    prep = re.sub(r'(encodedBoundaryPoints":)(".*?")', r'\1""', prep)
    prep = prep.replace('"{', '{').replace('}"', '}')
    return prep


class ListingPagesSpider(scrapy.Spider):
    """Spider which collects start urls for LandsForSaleSpider.

    """
    name = "listing-pages-spider"
    domain = DOMAIN
    allowed_domains = [domain]
    filter_order = {
        "Region": "County",
        "County": "City",
        "City": "Price",
    }
    custom_settings = {
        'FEEDS': {
            LISTING_LINKS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': ['start_link', 'count', 'root_page'],
            }
        }
    }
    start_urls = ['https://www.landwatch.com/land']

    def parse(self, response, **kwargs):
        state_urls = response.css('a.e6625').xpath('@href').getall()
        for state_url in state_urls:
            yield scrapy.Request(
                url=f'https://{self.domain}{state_url}',
                callback=self.parse_page,
                meta={'filter_section_name': 'Region'}
            )

    def parse_page(self, response):
        page_url = response.url
        filter_section_name = response.meta['filter_section_name']
        next_filter_section_name = self.filter_order.get(filter_section_name)
        script_text = response.xpath(
            '//script[contains(text(), "filterSections")]/text()').get()
        page_data_prep = _script_string_to_json_prep(script_text, page_url)
        try:
            filter_section = re.findall(
                r'"filterSections":(.*?),"footer"', page_data_prep)[0]
            filters = json.loads(filter_section)
        except (IndexError, ValueError):
            logging.error(
                "Something is wrong with 'window.serverState' content of broker page %s.",
                page_url
            )
            filters = None
        if not filters:
            return
        for filter_section in filters:
            if filter_section.get("section") == filter_section_name:
                region_filter = filter_section["filterLinks"]
                for region in region_filter:
                    if not region.get("count"):
                        continue
                    if region["count"] <= 10_000:
                        yield {
                            "start_link": region["relativeUrlPath"],
                            "count": region["count"],
                            "root_page": response.url,
                        }
                    else:
                        if next_filter_section_name:
                            yield scrapy.Request(
                                url=f'https://{self.domain}{region["relativeUrlPath"]}',
                                callback=self.parse_page,
                                meta={'filter_section_name': next_filter_section_name}
                            )
                break


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
                'fields': ['profile_link', 'root_page'],
            },
            PROPERTY_LINKS_FILE: {
                'format': 'csv',
                'overwrite': True,
                'fields': ['link', 'root_page'],
            },
        }
    }

    def start_requests(self):
        with open(LISTING_LINKS_FILE, 'r', encoding='utf-8') as links_file:
            for index, row in enumerate(links_file):
                if index == 0:
                    continue
                row = row.replace("\n", "")
                if row:
                    url = row.split(',')[0]
                    yield scrapy.Request(f'https://{self.domain}{url}', callback=self.parse)

    def parse(self, response, **kwargs):
        item_containers = response.css('div._51c43')
        for item_container in item_containers:
            yield {
                "link": item_container.css('div._12a2b').xpath('a/@href').get(),
                "profile_link": item_container.css('div.dc7c2').xpath('a/@href').get(),
                "root_page": response.url,
            }
        next_page_url = response.css('a.d72c6:last-child').xpath('@href').get()
        if next_page_url is not None:
            yield scrapy.Request(url=f'https://{self.domain}{next_page_url}')


class BaseDetailsSpider(scrapy.Spider):
    """The spider which is used as a base for collecting broker and property details.

    """
    domain = DOMAIN
    allowed_domains = [domain]
    links_file = None

    def start_requests(self):
        with open(self.links_file, 'r', encoding='utf-8') as links_file:
            for index, row in enumerate(links_file):
                if index == 0:
                    continue
                row = row.replace("\n", "")
                if row:
                    url = row.split(',')[0]
                    yield scrapy.Request(f'https://{self.domain}{url}', callback=self.parse)

    def parse(self, response, **kwargs):
        """Implementation of 'parse' method should be specified in its child class.

        """
        raise NotImplementedError(f'{self.__class__.__name__}.parse callback is not defined')


class BrokerProfileSpider(BaseDetailsSpider):
    """Spider which collects broker profile details.

    """
    name = "broker-details-spider"
    links_file = BROKER_LINKS_FILE
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

    def parse(self, response, **kwargs):
        page_url = response.url
        item = {
            'link': page_url,
        }
        script_text = response.xpath(
            '//script[contains(text(), "brokerDetails")]/text()').get()
        page_data_prep = _script_string_to_json_prep(script_text, page_url)
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
                page_url
            )
        yield item


class PropertyDetailsSpider(BaseDetailsSpider):
    """Spider which collects property details.

    """
    name = "property-details-spider"
    links_file = PROPERTY_LINKS_FILE
    address_fields = dict(zip(
        ADDRESS_FIELDS,
        ['address1', 'address2', 'city', 'stateAbbreviation', 'zip']
    ))
    home_fields = ['homesqft', 'beds', 'baths', 'halfBaths']
    custom_settings = {
        'FEEDS': {
            PROPERTY_DETAILS_FILE: {
                'format': 'csv',
                'overwrite': False,
                'fields': [
                    'link', 'brokerLink', 'status', 'title', 'price', 'acres',
                ] + ADDRESS_FIELDS + home_fields + [
                    'type', 'propertyWebsite',
                ],
            },
        }
    }

    def parse(self, response, **kwargs):
        page_url = response.url
        item = {
            'link': page_url,
            'brokerLink': response.css('a.d51ec').xpath('@href').get(),
        }
        script_text = response.xpath(
            '//script[contains(text(), "propertyDetailPage")]/text()').get()
        page_data_prep = _script_string_to_json_prep(script_text, page_url)
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
                page_url
            )
        yield item
