import json
import urllib
from hashlib import sha1
import hmac
import random
import time
import base64
import re, string 
from enum import Enum
import subprocess
import twitter as tw
import logging

log = logging.getLogger(__name__)

class OAuthSigner(object):
    """ Generates OAuth signatures for HTTP requests
    """
    def __init__(self):    
        random.seed()

        self.re_nonword = re.compile(r'[\W_]+')
        self.re_28 = re.compile(r'(\%28)')
        self.re_2C = re.compile(r'(\%2C)')
        self.re_29 = re.compile(r'(\%29)')

    def get_nonword(self, orig):
        """ Remove non-word characters from orig
        """
        return self.re_nonword.sub('', orig)

    def get_nonce(self): 
        """ Generate a Nonce for use in a client request
        """
        return self.get_nonword(base64.b64encode(str(random.getrandbits(32))))

    @classmethod
    def get_timestamp(cls):
        """ Get the current time as a timestamp
        """
        return int(time.time())

    def sub_escchars(self, orig):
        ''' No idea why, but the Twitter signature generator 
        encodes brackets, comma etc. as %25XX instead of %XX, where XX
        is the normal escape code for that non-word character.
        This method replicates the same thing.
        '''
        return self.re_29.sub('%2529', self.re_2C.sub('%252C', self.re_28.sub('%2528', orig)))

    def sign_request(self,
                     consumer_secret, 
                     token_secret,
                     req_type,
                     url,
                     argmap):
        '''
        Steps for generating the signature:
        1. Sort the keys in argmap alphabetically and join the key/value pairs in the format:
            base_string <- key1=value1&key2=value2...&keyN=valueN
        2. This is the 'base string', percent-encode this string.
            base_string <- percent-encode(base_string)
        3. percent-encode the URL, and prepend it to the above base string with 
        the '&' separator as:
            base_string <- enc_url&base_string
        4. Prepend the Request Type ("GET", "POST") to the string above using '&' as separator
            base_string <- req_type&base_string
        5. Generate the siging key as:
            key <- enc_consumer_secret&enc_token_secret
        where, enc_consumer_secret and enc_token_secret are %-encoded 
        OAuth consumer & token secrets respectively.
        6. Generate the SHA1 HMAC by signing the base_string with the key.
            signature <- percent-encode(base64(hmac(base_string,key)))
        '''
        # %-encode the secrets for the signing key, as per specification
        enc_consumer_secret = urllib.quote_plus(consumer_secret)
        enc_token_secret = urllib.quote_plus(token_secret)
        log.debug(argmap)
        
        args = sorted([key + '=' + argmap[key] for key in argmap])
        
        # The Base String as specified here: 
        args_str = '&'.join(args) # as specified by oauth
        args_str = urllib.quote_plus(args_str)
        
        enc_url = urllib.quote_plus(url)
        args_str = req_type + "&" + enc_url + "&" + args_str
        
        args_str = self.sub_escchars(args_str)
        # key = CONSUMER_SECRET& #If you dont have a token yet
        key = ""
        if enc_token_secret is None:
            key = enc_consumer_secret + '&'
        else:
            key = enc_consumer_secret + '&' + enc_token_secret
        #key = &TOKEN_SECRET" 

        log.debug("Base string : %s", args_str)

        log.debug("Signing key : %s", key)
        hashed = hmac.new(key, args_str, sha1)
        hashed_b64 = hashed.digest().encode("base64").rstrip('\n')
        log.debug("Signature : %s", hashed_b64)
        # The signature
        return urllib.quote_plus(hashed_b64)

def create_datafetcher(settings_file):
    ''' Create DataFetcher from settings file
    '''
    settings_fp = None
    try:
        settings_fp = open(settings_file, "r")
        settings = json.load(settings_fp)
    finally:
        if not settings_fp is None:
            settings_fp.close()
    return DataFetcher(settings)

class DataFetcher(object):
    ''' DataFetcher class for twitter data collection
    '''
    TWITTER_API_URL = "https://api.twitter.com"
    TWITTER_STR_API_URL = 'https://stream.twitter.com'
    
    TWITTER_STR_STATUS_FILTER = '/1.1/statuses/filter.json'
    TWITTER_SEARCH = '/1.1/search/tweets.json'

    class Cmd(Enum):
        search = 1
        stream_filter = 2

    

    class Locations(object):
        NORTHAMPTONSHIRE = '-1.386293,51.985165,-0.282167,52.650010'
        LONDON = '-0.567680,51.277729,0.289254,51.701847'
 

    def __init__(self, settings=None):
        self._settings = settings
        self.cmd_map = {
            self.Cmd.search : [False, self.TWITTER_SEARCH],
            self.Cmd.stream_filter : [True, self.TWITTER_STR_STATUS_FILTER],
        }
        self.api = tw.Api(**self._settings)
        self.api.VerifyCredentials()

    def generate_curl_cmdline(self,
                              command,
                              verbose,
                              timeout,
                              **kwargs):
        ''' Generate the curl command needed to fetch twitter statuses
        '''
        # The URL to query
        is_streaming = self.cmd_map[command][0]
        base_url = self.TWITTER_STR_API_URL if is_streaming else self.TWITTER_API_URL
        cmd_url = self.cmd_map[command][1]
        filter_url = base_url + cmd_url
        signer = OAuthSigner()
        twitter_keys = self._settings

        
        """
        Nonce
            The oauth_nonce parameter is a unique token your application
            should generate for each unique request. 
            Twitter will use this value to determine whether a request
            has been submitted multiple times. The value for this request
            was generated by base64 encoding 32 bytes of random data, and
            stripping out all non-word characters, but any approach which
            produces a relatively random alphanumeric string should be OK
            here.
        Timestamp
            The oauth_timestamp parameter indicates when the request was
            created. This value should be the number of seconds since the
            Unix epoch at the point the request is generated, and should be
            easily generated in most programming languages. Twitter will
            reject requests which were created too far in the past, so it
            is important to keep the clock of the computer generating
            requests in sync with NTP.
        """

        # The Parameters used in the base string for signing
        argmap = {
            'oauth_consumer_key' : twitter_keys["consumer_key"],
            'oauth_nonce' : signer.get_nonce(),
            'oauth_signature_method' : "HMAC-SHA1",
            'oauth_timestamp' : str(signer.get_timestamp()),
            'oauth_token' : twitter_keys["access_token_key"],
            'oauth_version' : "1.0",
        }
        
        req_args = {}

        for key in kwargs:
            val = kwargs[key]
            if not val is None:
                arg_val = str(val).lower() if type(val) is bool else str(val)
                argmap[key] = arg_val
                req_args[key] = arg_val

        # Parameters that constitute the siging key
        oauth_consumer_secret = twitter_keys["consumer_secret"]
        oauth_token_secret = twitter_keys["access_token_secret"]

        # Generate the oauth request signature
        oauth_signature = signer.sign_request(oauth_consumer_secret, 
                                              oauth_token_secret, 
                                              "GET", 
                                              filter_url, 
                                              argmap)

        # Generate the %-encoded request args
        twdata = urllib.urlencode(req_args)

        # Set up the request header
        twheader = ('Authorization: OAuth ' + \
                    'oauth_consumer_key="%s", ' + \
                    'oauth_nonce="%s", ' + \
                    'oauth_signature="%s", ' + \
                    'oauth_signature_method="HMAC-SHA1", ' + \
                    'oauth_timestamp="%s", ' + \
                    'oauth_token="%s", ' + \
                    'oauth_version="1.0"') % \
                        (argmap['oauth_consumer_key'], \
                            argmap['oauth_nonce'], \
                            oauth_signature, \
                            argmap['oauth_timestamp'], \
                            argmap['oauth_token']) 

        # Generate the cURL command line
        verbose_str = "--verbose" if verbose else ""
    
        (timeout_switch, timeout_arg) = ("--max-time", str(timeout)) \
                                            if not timeout is None else ("", "")
        print("URL:")
        print(filter_url)
        twcurl_cmd = ["curl", 
                      "--get",
                      filter_url,
                      "--data",
                      twdata,
                      "--header",
                      twheader,
                      timeout_switch,
                      timeout_arg,
                      verbose_str]

        # Run this command to stream the search results.
        log.debug("cURL command line:")
        log.debug(' '.join(twcurl_cmd))

        return twcurl_cmd

    def download_data(self, stdout, stderr, *args, **kwargs):
        ''' Fetch data using cURL
        '''
        curl_cmdline = self.generate_curl_cmdline(*args, **kwargs)

        curl_out = None
        print(curl_cmdline)
        try:
            status = subprocess.call(curl_cmdline,
                            stdout=stdout,
                            stderr=stderr)
        finally:
            pass
        #subprocess.call(curl_cmdline)
        return status

    def fetch_data(self, *args, **kwargs):
        ''' Fetch data using cURL
        '''
        curl_cmdline = self.generate_curl_cmdline(*args, **kwargs)

        curl_out = None
        print(curl_cmdline)
        try:
            curl_out = subprocess.Popen(curl_cmdline,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

            output = curl_out.communicate()
            stdout = output[0]
            stderr = output[1]
        finally:
            if not curl_out is None:
                curl_out.stdout.close()
                curl_out.stderr.close()

        #subprocess.call(curl_cmdline)
        return (stdout, stderr)

    def search(self, *args, **kwargs):
        """ Search twitter using the python-twitter API
        """
        results = self.api.GetSearch(*args, **kwargs)

        return results
