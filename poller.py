import datetime
import ConfigParser
import csv

class Poller(object):
    def __init__(self):
        self._get_config()
        self._open_file()

    #Parse the configuration file for the poller
    def _get_config(self):
        configParser = ConfigParser.RawConfigParser()
        configFilePath = r'monitor.config'
        configParser.read(configFilePath)
        poller_type = configParser.get('Poller', 'poller_type')
        if poller_type == "file":
            self.filepath = configParser.get('Poller', 'filepath')
            self.data_poll_interval = float(configParser.get('Poller', 'data_poll_interval'))
            self.data_avg_interval = float(configParser.get('Poller', 'data_avg_interval'))
            self.max_mem = float(configParser.get('Poller', 'max_mem'))
            self.max_disk_read_requests = float(configParser.get('Poller', 'max_disk_read_requests'))
            self.max_disk_write_requests = float(configParser.get('Poller', 'max_disk_write_requests'))
        #TODO: else if poller_type == ceilometer
        
    #Open the file containing the samples
    def _open_file(self):
        self.reader = csv.reader(open(self.filepath))
        self.next_line = next(self.reader)

    #Get samples between start and end timestamp that belong to specific tenant
    def get_samples(self, project, max_timestamp):
        #No more samples in the file
        if not self.next_line:
            return "done"
        if max_timestamp < self.next_line[0]:
            return
        sample = self.next_line
        samples = {}
        #Get all samples that are equal to current start_timestamp(filter for tenant)
        fixed_timestamp = sample[0]
        while True:
            timestamp = sample[0]
            meter_name = sample[1]
            volume = sample[2]
            resource_id = sample[3]
            project_id = sample[4]
            meta_data = sample[5]
            if timestamp != fixed_timestamp:
                self.next_line = sample
                break
            if project_id == project:
                if resource_id not in samples:
                    samples[resource_id] = {}
                samples[resource_id][meter_name] = float(volume)
                samples[resource_id]['project_id'] = project_id
                samples[resource_id]['timestamp'] = timestamp

            try:
                sample = next(self.reader)
            except Exception:
                pass
        #Check if each sample is complete or missing a meter_name. If a one meter_name is missing delete the entire sample
        for sample in list(samples):
            if 'cpu_util' not in samples[sample] or 'memory.resident' not in samples[sample]:
                del samples[sample]

        return samples
        
    
    #Normalize samples to percentage
    def normalize_samples(self, samples):
        for sample in samples:
            samples[sample]['memory.resident'] = samples[sample]['memory.resident'] / self.max_mem * 100.0
            samples[sample]['disk.read.requests'] = samples[sample]['disk.read.requests'] / self.max_disk_read_requests * 100.0
            samples[sample]['disk.write.requests'] = samples[sample]['disk.write.requests'] / self.max_disk_write_requests * 100.0

        return samples

    def get_samples_avg(self, project, start_timestamp, end_timestamp):
        samples = {}
        while start_timestamp <= end_timestamp:
            #print "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\", start_timestamp
            new_samples = self.get_samples(project, end_timestamp)
            #print new_samples
            if new_samples == "done":
                return
            if new_samples == None:
                break

            for sample in new_samples:
                if sample not in samples:
                    samples[sample] = {}
                    if 'cpu_util' in new_samples[sample]:
                        samples[sample]['cpu_util'] = new_samples[sample]['cpu_util']
                        samples[sample]['cpu_util_count'] = 1
                    else:
                        samples[sample]['cpu_util'] = 0
                        samples[sample]['cpu_util_count'] = 0
                    if 'memory.resident' in new_samples[sample]:
                        samples[sample]['memory.resident'] = new_samples[sample]['memory.resident']
                        samples[sample]['memory.resident_count'] = 1
                    else:
                        samples[sample]['memory.resident'] = 0
                        samples[sample]['memory.resident_count'] = 0
                    if 'disk.read.requests.rate' in new_samples[sample]:
                        samples[sample]['disk.read.requests.rate'] = new_samples[sample]['disk.read.requests.rate']
                        samples[sample]['disk.read.requests.rate_count'] = 1
                    else:
                        samples[sample]['disk.read.requests.rate'] = 0
                        samples[sample]['disk.read.requests.rate_count'] = 0
                    if 'disk.write.requests.rate' in new_samples[sample]:
                        samples[sample]['disk.write.requests.rate'] = new_samples[sample]['disk.write.requests.rate']
                        samples[sample]['disk.write.requests.rate_count'] = 1
                    else:
                        samples[sample]['disk.write.requests.rate'] = 0
                        samples[sample]['disk.write.requests.rate_count'] = 0

                    if 'disk.write.requests' in new_samples[sample]:
                        samples[sample]['disk.write.requests'] = new_samples[sample]['disk.write.requests']
                        samples[sample]['disk.write.requests_count'] = 1
                    else:
                        samples[sample]['disk.write.requests'] = 0
                        samples[sample]['disk.write.requests_count'] = 0
                    if 'disk.read.requests' in new_samples[sample]:
                        samples[sample]['disk.read.requests'] = new_samples[sample]['disk.read.requests']
                        samples[sample]['disk.read.requests_count'] = 1
                    else:
                        samples[sample]['disk.read.requests'] = 0
                        samples[sample]['disk.read.requests_count'] = 0
                    #samples[sample]['network.incoming.bytes.rate'] = new_samples[sample]['network.incoming.bytes.rate']
                    #samples[sample]['network.outgoing.bytes.rate'] = new_samples[sample]['network.outgoing.bytes.rate']
                    #samples[sample]['network.incoming.packets.rate'] = new_samples[sample]['network.incoming.packets.rate']
                    #samples[sample]['network.outgoing.packets.rate'] = new_samples[sample]['network.outgoing.packets.rate']
                    samples[sample]['project_id'] = new_samples[sample]['project_id']
                    samples[sample]['start_duration'] = new_samples[sample]['timestamp']
                    samples[sample]['end_duration'] = new_samples[sample]['timestamp']

                else:
                    samples[sample]['end_duration'] = new_samples[sample]['timestamp']
                    start_timestamp = samples[sample]['end_duration']
                    if 'cpu_util' in new_samples[sample]:
                        samples[sample]['cpu_util'] += new_samples[sample]['cpu_util']
                        samples[sample]['cpu_util_count'] += 1
                    if 'memory.resident' in new_samples[sample]:
                        samples[sample]['memory.resident'] += new_samples[sample]['memory.resident']
                        samples[sample]['memory.resident_count'] += 1
                    if 'disk.read.requests.rate' in new_samples[sample]:
                        samples[sample]['disk.read.requests.rate'] += new_samples[sample]['disk.read.requests.rate']
                        samples[sample]['disk.read.requests.rate_count'] += 1
                    if 'disk.write.requests.rate' in new_samples[sample]:
                        samples[sample]['disk.write.requests.rate'] += new_samples[sample]['disk.write.requests.rate']
                        samples[sample]['disk.write.requests.rate_count'] += 1

                    if 'disk.write.requests' in new_samples[sample]:
                        samples[sample]['disk.write.requests'] += new_samples[sample]['disk.write.requests']
                        samples[sample]['disk.write.requests_count'] += 1
                    if 'disk.read.requests' in new_samples[sample]:
                        samples[sample]['disk.read.requests'] += new_samples[sample]['disk.read.requests']
                        samples[sample]['disk.read.requests_count'] += 1


                    #samples[sample]['network.incoming.bytes.rate'] += new_samples[sample]['network.incoming.bytes.rate']
                    #samples[sample]['network.outgoing.bytes.rate'] += new_samples[sample]['network.outgoing.bytes.rate']
                    #samples[sample]['network.incoming.packets.rate'] += new_samples[sample]['network.incoming.packets.rate']
                    #samples[sample]['network.outgoing.packets.rate'] += new_samples[sample]['network.outgoing.packets.rate']
        
        for sample in samples:
            if samples[sample]['cpu_util_count'] != 0:
                samples[sample]['cpu_util'] /= samples[sample]['cpu_util_count']
            if samples[sample]['memory.resident_count'] != 0:
                samples[sample]['memory.resident'] /= samples[sample]['memory.resident_count']
            if samples[sample]['disk.read.requests.rate_count'] != 0:
                samples[sample]['disk.read.requests.rate'] /= samples[sample]['disk.read.requests.rate_count']
            if samples[sample]['disk.write.requests.rate_count'] != 0:
                samples[sample]['disk.write.requests.rate'] /= samples[sample]['disk.write.requests.rate_count']

            if samples[sample]['disk.read.requests_count'] != 0:
                samples[sample]['disk.read.requests'] /= samples[sample]['disk.read.requests_count']
            if samples[sample]['disk.write.requests_count'] != 0:
                samples[sample]['disk.write.requests'] /= samples[sample]['disk.write.requests_count']
            #samples[sample]['network.incoming.bytes.rate'] /= samples[sample]['count']
            #samples[sample]['network.outgoing.bytes.rate'] /= samples[sample]['count']
            #samples[sample]['network.incoming.packets.rate'] /= samples[sample]['count']
            #samples[sample]['network.outgoing.packets.rate'] /= samples[sample]['count']

        
        samples = self.normalize_samples(samples)
        return samples
