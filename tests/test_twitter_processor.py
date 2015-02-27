
import unittest
import logging
import logging.config

from analysis.twitter_processor import Processor
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
            'propagate': True,
        },
        'analysis.datafetch.twitter_fetch': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

logging.config.dictConfig(D_LOG)


class TestTwitterProcessor(unittest.TestCase):

    def setUp(self):
        self.results_file_name = "/home/anshuman/northants/twitter_data/001/twout/twitter_data.json"
        self.processor = Processor()

    def test_make_df(self):
        with open(self.results_file_name, "r") as results_file:
            dataframe = self.processor.make_df(results_file, 1000)
            print(dataframe)
            user_frame = dataframe.groupby("user")
            print(user_frame.groups)
