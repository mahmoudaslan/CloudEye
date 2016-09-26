import datetime
import common_functions as comfuns
import math
import constants as cons
from termcolor import colored

class SequentialKmeans(object):
    def __init__(self):
        self.centroid = [{}, {}, {}]
        #centroid['webservers'] = {}
        #centroid['appservers'] = {}
        #centroid['dbservers'] = {}
        
    def print_centroid_info(self):
        print "========================= Centroids Info ======================================"
        print self.centroid[0]['cpu_util'], self.centroid[0]['memory.resident']
        print self.centroid[1]['cpu_util'], self.centroid[1]['memory.resident']
        print self.centroid[2]['cpu_util'], self.centroid[2]['memory.resident']
        print "================================================================================"

    def initial_guess(self, samples):
        c = 0
        for sample in samples:
            print "Centroid%s: ",c, sample
            self.centroid[c]['cpu_util'] = samples[sample]['cpu_util']
            self.centroid[c]['memory.resident'] = samples[sample]['memory.resident']
            self.centroid[c]['count'] = 1
            c+=1

    #Update the seq-kmeans centroids and return
    #1- boolean anomaly
    #2- closest centroid index
    def update(self, sample):
        cpu = sample['cpu_util']
        memory = sample['memory.resident']
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])

        #Check closest centroid to the current sample                                                                                          
        closest_cent = 0
        closest_d = 1000000
        for i in range(3):
            d = math.hypot(self.centroid[i]['cpu_util'] - cpu, self.centroid[i]['memory.resident'] - memory)
            if d < closest_d:
                closest_d = d
                closest_cent = i
                
        anomaly = False
        #Check for anomalies                                                                                                                   
        if (closest_d > cons.ANOMALY_THRESHOLD):
            anomaly = True
            print colored("Matching [Failed], incident have been reported", "red")
            #fig1_sub1.scatter(cpu, memory, time_in_minutes, alpha=0.5, c=c_anomaly, marker=server.shape)
        else:
            print colored("Matching [OK]", "green")

        mx = self.centroid[closest_cent]['cpu_util']
        my = self.centroid[closest_cent]['memory.resident']
        n = self.centroid[closest_cent]['count'] + 1
        x = cpu
        y = memory
        print "mx: " , mx
        print "(1/n)", (1.0/n)
        print "(x-mx)", (x-mx)
        print closest_cent
        self.centroid[closest_cent]['cpu_util'] = (mx + (1.0/n) * (x-mx))
        self.centroid[closest_cent]['memory.resident'] = (my + (1.0/n) * (y-my))
        self.centroid[closest_cent]['count'] = n
        
        self.print_centroid_info()

        return anomaly, closest_cent
