from dotenv import load_dotenv


load_dotenv()

BOT_NAME = 'landcrawler'

SPIDER_MODULES = ['landcrawler.spiders']
NEWSPIDER_MODULE = 'landcrawler.spiders'

ROBOTSTXT_OBEY = False

DEFAULT_REQUEST_HEADERS = {
   'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
              'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'),
   'Accept-Encoding': 'gzip, deflate, br',
   'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
   'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/605.1.15 '
                  '(KHTML, like Gecko) Version/15.6 Safari/605.1.15'),
   'Upgrade-Insecure-Requests': '1',
}
USER_AGENTS = [
   ('Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/15.6 Safari/605.1.15'),
]

#DNS_TIMEOUT = 60 * 3
#DOWNLOAD_DELAY = 0.5
#DOWNLOAD_FAIL_ON_DATALOSS = False
#DOWNLOAD_TIMEOUT = 60 * 5
#RANDOMIZE_DOWNLOAD_DELAY = True
#RETRY_TIMES = 3

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 100,
    'landcrawler.middlewares.LandcrawlerDownloaderMiddleware': 950,
#    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': None,
#    'scrapy.contrib.downloadermiddleware.redirect.RedirectMiddleware': None,
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'wa_animation.middlewares.WaAnimationSpiderMiddleware': 950,
#}

LOG_ENABLED = True
LOG_FILE = 'logs.log'
LOG_FILE_APPEND = 'False'
LOG_LEVEL = 'DEBUG'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'landcrawler.middlewares.LandcrawlerSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'landcrawler.middlewares.LandcrawlerDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'landcrawler.pipelines.LandcrawlerPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
