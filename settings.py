# PHIDGETS = [347616, ]
CALLBACK_URLS = {'http://localhost:8080/api/': '3f9d70f25ca0ff54cb29e28ab41b64f42eec1cca'}           # PhidgetServer calls these urls to notify on phidget events

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
            #'class': 'logging.FileHandler',
            #'filename': 'log/PhidgetServer.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
        #'propagate': False
    },
    'loggers': {
        'cherrypy': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False
        },
    },
}