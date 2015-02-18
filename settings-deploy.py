""" Settings for any program that wants to use 'em'
"""

LOGGING = {
    
    "version": 1,
    
    "disable_existing_loggers": True,
    
    "formatters" : {
        "standard" : {
            "format": '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        }
    },

    "handlers": {
        "default": {
            "level" : "DEBUG",
            "class" : "logging.StreamHandler",
        }, 
        "rotating" : {
            "level" : "DEBUG",
            "class" : "logging.FileHandler",
            "formatter" : "standard",
            "filename" : "/usr/share/northants/twout/twitterd.log",
        }
    },

    "loggers": {
        "twitterd" : {                  
            "handlers": ["rotating"],        
            "level": "DEBUG",  
            "propagate": True,
        },
        "analysis.datafetch.twitter_fetch": { 
            "handlers": ["rotating"],
            "level": "DEBUG",  
            "propagate": True,
        }
    }
}

