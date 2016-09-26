import datetime
import constants as cons

def add_to_timestamp(timestamp, secs):
    return str(datetime.datetime.strptime(timestamp, cons.TIMESTAMP_FORMAT) + datetime.timedelta(seconds=secs))

def timestamp_to_minutes(timestamp):
    return (datetime.datetime.strptime(timestamp, cons.TIMESTAMP_FORMAT) - datetime.datetime.strptime(cons.fixed_start_timestamp, cons.TIMESTAMP_FORMAT)).total_seconds()/60
