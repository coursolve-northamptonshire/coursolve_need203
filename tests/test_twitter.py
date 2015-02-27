import unittest
import logging
import logging.config
import json

from analysis.datafetch import twitter_fetch as twitter


D_LOG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
        'analysis.datafetch.twitter_fetch': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
    }
}

logging.config.dictConfig(D_LOG)

LOG = logging.getLogger(__name__)


class TwitterTester(unittest.TestCase):
    ''' Test code for testing twitter data collection
    '''

    def setUp(self):
        self.northants_box = '-1.386293,51.985165,-0.282167,52.650010'
        self.northants_geo = ','.join(['(52.240477000000000000',
                                       '-0.902655999999979000,50mi)'])
        self.northants_radius = (52.240477000000000000,
                                 -0.902655999999979000,
                                 '50mi')
        # track='india'
        twitter_cred_file = "/home/anshuman/.twitter_api_keys.json"
        self.fetcher = twitter.create_datafetcher(twitter_cred_file)

    def test_stream_filter(self):
        ''' Test simple curl command line generation for streamign filter
        '''
        cmd = twitter.DataFetcher.Cmd.stream_filter
        loc = self.northants_box
        # Run this command to stream the search results.
        twcurl_cmd = self.fetcher.generate_curl_cmdline(command=cmd,
                                                        verbose=False,
                                                        timeout=None,
                                                        locations=loc,
                                                        track=None,
                                                        include_entities=1)
        LOG.info("cURL command line:")
        LOG.info(' '.join(twcurl_cmd))


    def test_search(self):
        ''' Test simple curl command line generation for simple search
        '''
        # Run this command to stream the search results.
        twcurl_cmd = self.fetcher.generate_curl_cmdline(command=twitter.DataFetcher.Cmd.search,
                                                        verbose=False,
                                                        timeout=None,
                                                        since_id=565686632033300481,
                                                        geocode=self.northants_geo,
                                                        track=None,
                                                        include_entities=1,
                                                        count=25)
        LOG.info("cURL command line:")
        LOG.info(' '.join(twcurl_cmd))

    def test_simple_search(self):
        ''' Test simple curl command line generation for simple search
        '''
        # Run this command to stream the search results.
        twcurl_cmd = self.fetcher.generate_curl_cmdline(command=twitter.DataFetcher.Cmd.search,
                                                        verbose=False,
                                                        timeout=None,
                                                        track="india",
                                                        include_entities=1,
                                                        count=25)
        LOG.info("cURL command line:")
        LOG.info(' '.join(twcurl_cmd))

    def test_data_fetch(self):
        ''' Test data fetch
        '''

        result = self.fetcher.fetch_data(command=twitter.DataFetcher.Cmd.search,
                                         verbose=False,
                                         timeout=None,
                                         q="",
                                         geocode=self.northants_geo,
                                         count=100,
                                         result_type="recent",
                                         include_entities=1)

        LOG.info("Received First Response:")
        LOG.info(result[0])
        d_result = json.loads(result[0])


        count = d_result['search_metadata']['count']
        max_id = d_result['search_metadata']['max_id']
        since_id = d_result['search_metadata']['since_id']


        LOG.info("since_id = %d", since_id)
        LOG.info("count = %d", count)
        LOG.info("max_id = %d or %d", max_id, d_result['search_metadata']['max_id'])
        pages = 0
        max_pages = 5
        while pages < max_pages:
            result = self.fetcher.fetch_data(command=twitter.DataFetcher.Cmd.search,
                                             verbose=True,
                                             timeout=None,
                                             q="",
                                             geocode=self.northants_geo,
                                             since_id=since_id,
                                             count=count,
                                             max_id=max_id,
                                             include_entities=1)

            count = d_result['search_metadata']['count']
            max_id = d_result['search_metadata']['max_id']
            since_id = d_result['search_metadata']['since_id']
            pages += 1
            LOG.info("Received Page: %d", pages)
            LOG.info(result[0])
        #LOG.info("Errors:")
        #LOG.info(result[1])


    def test_data_download(self):
        """ Test data downloads
        """
        out_file = open("twitter_data.json", "w")
        err_file = open("twitter_data.err", "w")
        max_time = 30
        status = self.fetcher.download_data(out_file,
                                            err_file,
                                            command=\
                                            twitter.DataFetcher.Cmd.stream_filter,
                                            verbose=True,
                                            timeout=max_time,
                                            locations=self.northants_box,
                                            track=None,
                                            include_entities=1)

        out_file.close()
        err_file.close()
        LOG.info(status)

    def test_api_search(self):
        """ Call the python-twitter api to search
        """
        max_count = 100
        results = self.fetcher.search(geocode=self.northants_radius,
                                      count=max_count,
                                      include_entities=1)
        for result in results:
            LOG.info(result)

