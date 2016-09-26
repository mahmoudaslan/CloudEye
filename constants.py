#FILE: constants.py
#DESCIPTION: This file contain the configuration constants of the monitor service

CEILOMETER_VERSION = 2
NOVA_VERSION = 2.1
USERNAME = "admin"
PASSWORD = "admin"
PROJECT_NAME = "demo"
AUTH_URL = "http://192.170.0.7:5000/v2.0"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

POLL_INTERVAL = 40 #30 seconds(has to be > ceilometer poll time so it wont fall behind)
#LIMIT_PER_REQUEST = 10
STABILIZE_TIME = 60 #1 minute (should be ~10 minutes)
#CPU_UTIL_AVG_MARGIN_ERROR = 0.2 #10%

#Number of profiles
PROFILES = 2
ANOMALY_THRESHOLD = 30 #Anomaly threshold percentage
#Features(metrics) normalization parameters
MAX_MEM = 8192 #16GB

#Starting time
fixed_start_timestamp = '2016-09-06 05:19:05'
fixed_end_timestamp = '2016-09-06 05:51:00'
tenant = 'db0d6c08f675447fac289f4b75b3a97f'
