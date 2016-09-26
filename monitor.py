import datetime
import sequential_kmeans as seqkmeans
import server as serv
import profile as prof
import poller
import common_functions as comfuns

import constants as cons
import mysql
import math
import time
from termcolor import colored
import logging
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.ticker as ticker

class Figure(object):
    def __init__(self, fig, skmeans):
        plt.ion()
        self.pts_shapes = ['o', 's', 'D', '^', '*', '>', '<', 'v']
        self.fig = fig
        self.skmeans = skmeans
        self.cent_colors = ['b', 'g', 'y']
        self.anomaly_color = 'r'

    def prep_3dPlotChart(self):
        self.fig1 = self.fig.add_subplot(2, 2, 1, projection='3d')
        self.fig1.set_ylabel("Memory Resident(%)")
        self.fig1.set_xlabel("CPU Utilization(%)")
        self.fig1.set_zlabel("Time(minutes)")
        #Draw initial centroids
        self.fig1_xpoints=[self.skmeans.centroid[0]['cpu_util'],self.skmeans.centroid[1]['cpu_util'],self.skmeans.centroid[2]['cpu_util']]
        self.fig1_ypoints=[self.skmeans.centroid[0]['memory.resident'],self.skmeans.centroid[1]['memory.resident'],self.skmeans.centroid[2]['memory.resident']]
        self.fig1_zpoints=[0, 0, 0]
        self.fig1_points, = self.fig1.plot(self.fig1_xpoints, self.fig1_ypoints, self.fig1_zpoints, marker='+', linestyle='None', markersize=10, mew=3, alpha=0.6, c='k')
        self.fig1_points.set_xdata(self.fig1_xpoints)
        self.fig1_points.set_ydata(self.fig1_ypoints)
        self.fig1_points.set_3d_properties(self.fig1_zpoints)

    def update_3dPlotChart(self, sample, anomaly, closest_cent, server):
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])
        cpu = sample['cpu_util']
        memory = sample['memory.resident']
        #Draw the updated centroids
        self.fig1_xpoints[closest_cent] = self.skmeans.centroid[closest_cent]['cpu_util']
        self.fig1_ypoints[closest_cent] = self.skmeans.centroid[closest_cent]['memory.resident']
        self.fig1_zpoints[closest_cent] = time_in_minutes
        self.fig1_points.set_3d_properties(self.fig1_zpoints)
        self.fig1_points.set_data(self.fig1_xpoints, self.fig1_ypoints)
        #Draw the sample point
        if anomaly:
            self.fig1.scatter(cpu, memory, time_in_minutes, alpha=0.5, c=self.anomaly_color, marker=server.shape, label='VM')
        else:
            self.fig1.scatter(cpu, memory, time_in_minutes, alpha=0.5, c=self.cent_colors[closest_cent], marker=server.shape, label='VM')

    def prep_lineChart1(self):
        self.fig2 = self.fig.add_subplot(223)
        self.fig2.set_ylabel("CPU Utilization(%)")
        self.fig2.set_xlabel("Time(minutes)")
        self.fig2_time_in_minutes = {}
        self.fig2_cpu_util = {}

    def update_lineChart1(self, sample, anomaly, closest_cent, server):
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])
        cpu = sample['cpu_util']
        if server.id not in self.fig2_time_in_minutes:
            self.fig2_time_in_minutes[server.id] = []
        if server.id not in self.fig2_cpu_util:
            self.fig2_cpu_util[server.id] = []
        self.fig2_time_in_minutes[server.id].append(time_in_minutes)
        self.fig2_cpu_util[server.id].append(cpu)
        #Draw the sample point
        self.fig2.plot(self.fig2_time_in_minutes[server.id], self.fig2_cpu_util[server.id], alpha=0.5, ls='-', c=server.color)
        if anomaly:
            self.fig2.scatter(time_in_minutes, cpu, alpha=0.5, c=self.anomaly_color, marker=server.shape) 
            #self.fig2.plot(self.fig2_time_in_minutes[server.id], self.fig2_cpu_util[server.id], alpha=0.5, ls='-', c=self.anomaly_color) 
        else:
            self.fig2.scatter(time_in_minutes, cpu, alpha=0.5, c=self.cent_colors[closest_cent], marker=server.shape)


    def prep_lineChart2(self):
        self.fig3 = self.fig.add_subplot(224)
        self.fig3.set_ylabel("Memory Resident(%)")
        self.fig3.set_xlabel("Time(minutes)")
        self.fig3_time_in_minutes = {}
        self.fig3_memory_resident = {}

    def update_lineChart2(self, sample, anomaly, closest_cent, server):
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])
        memory = sample['memory.resident']
        if server.id not in self.fig3_time_in_minutes:
            self.fig3_time_in_minutes[server.id] = []
        if server.id not in self.fig3_memory_resident:
            self.fig3_memory_resident[server.id] = []
        self.fig3_time_in_minutes[server.id].append(time_in_minutes)
        self.fig3_memory_resident[server.id].append(memory)
        #Draw the sample point
        self.fig3.plot(self.fig3_time_in_minutes[server.id], self.fig3_memory_resident[server.id], alpha=0.5, ls='-', c=server.color)
        if anomaly:
            self.fig3.scatter(time_in_minutes, memory, alpha=0.5, c=self.anomaly_color, marker=server.shape)
        else:
            self.fig3.scatter(time_in_minutes, memory, alpha=0.5, c=self.cent_colors[closest_cent], marker=server.shape)

    def prep_lineChart3(self):
        self.fig4 = self.fig.add_subplot(222)
        self.fig4.set_ylabel("Disk Read Rate(%)")
        self.fig4.set_xlabel("Time(minutes)")
        self.fig4_time_in_minutes = {}
        self.fig4_disk_read_reqs = {}

    def update_lineChart3(self, sample, anomaly, closest_cent, server):
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])
        disk_read_reqs = sample['disk.read.requests']
        if server.id not in self.fig4_time_in_minutes:
            self.fig4_time_in_minutes[server.id] = []
        if server.id not in self.fig4_disk_read_reqs:
            self.fig4_disk_read_reqs[server.id] = []
        self.fig4_time_in_minutes[server.id].append(time_in_minutes)
        self.fig4_disk_read_reqs[server.id].append(disk_read_reqs)
        #Draw the sample point
        #print self.fig4_disk_read_reqs[server.id]
        self.fig4.plot(self.fig4_time_in_minutes[server.id], self.fig4_disk_read_reqs[server.id], alpha=0.5, ls='-', c=server.color)
        if anomaly:
            self.fig4.scatter(time_in_minutes, disk_read_reqs, alpha=0.5, c=self.anomaly_color, marker=server.shape)
        else:
            self.fig4.scatter(time_in_minutes, disk_read_reqs, alpha=0.5, c=self.cent_colors[closest_cent], marker=server.shape)

    def prep_lineChart4(self):
        self.fig5 = self.fig.add_subplot(221)
        self.fig5.set_ylabel("Disk Write Rate(%)")
        self.fig5.set_xlabel("Time(minutes)")
        self.fig5_time_in_minutes = {}
        self.fig5_disk_write_reqs = {}

    def update_lineChart4(self, sample, anomaly, closest_cent, server):
        time_in_minutes = comfuns.timestamp_to_minutes(sample['start_duration'])
        disk_write_reqs = sample['disk.write.requests']
        if server.id not in self.fig5_time_in_minutes:
            self.fig5_time_in_minutes[server.id] = []
        if server.id not in self.fig5_disk_write_reqs:
            self.fig5_disk_write_reqs[server.id] = []
        self.fig5_time_in_minutes[server.id].append(time_in_minutes)
        self.fig5_disk_write_reqs[server.id].append(disk_write_reqs)
        #Draw the sample point
        #print self.fig5_disk_write_reqs[server.id]
        self.fig5.plot(self.fig5_time_in_minutes[server.id], self.fig5_disk_write_reqs[server.id], alpha=0.5, ls='-', c=server.color)
        if anomaly:
            self.fig5.scatter(time_in_minutes, disk_write_reqs, alpha=0.5, c=self.anomaly_color, marker=server.shape)
        else:
            self.fig5.scatter(time_in_minutes, disk_write_reqs, alpha=0.5, c=self.cent_colors[closest_cent], marker=server.shape)

class Figure2(object):
    def __init__(self, fig, skmeans):
        self.pts_shapes = ['-', '--', ':', '-.', '-', '--', ':', '-.']
        self.pts_lw = [1, 1, 1, 1, 2, 2, 2, 2]
        plt.ion()
        self.fig = fig
        self.skmeans = skmeans
        self.cent_colors = ['b', 'g', 'y']
        self.anomaly_color = 'r'

    def prep_parallelChart(self):
        self.sub1 = self.fig.add_subplot(131)
        self.sub2 = self.fig.add_subplot(132)
        self.sub3 = self.fig.add_subplot(133)
        self.sub1.set_xlim([1,2])
        self.sub2.set_xlim([2,3])
        self.sub3.set_xlim([3,4])
        self.sub1.xaxis.set_major_formatter(ticker.FormatStrFormatter('CPU Util'))
        self.sub2.xaxis.set_major_formatter(ticker.FormatStrFormatter('Memory Resident'))
        self.sub3.xaxis.set_major_formatter(ticker.FormatStrFormatter('%s'))
        self.sub1.xaxis.set_major_locator(ticker.FixedLocator([1]))
        self.sub2.xaxis.set_major_locator(ticker.FixedLocator([2]))
        self.sub3.xaxis.set_major_locator(ticker.FixedLocator([3, 4]))

        self.sub3.set_xticklabels(['Disk Read Req', 'Disk Write Req'])

        for tick in self.sub3.yaxis.get_major_ticks():
            tick.label2On=True
        self.fig.subplots_adjust(wspace=0)

        self.fig_time_in_minutes = {}
        self.fig_memory_resident = {}
        self.fig_cpu_util = {}
        

    def update_parallelChart(self, sample, anomaly, closest_cent, server):
        memory = sample['memory.resident']
        cpu = sample['cpu_util']
        disk_read_reqs = sample['disk.read.requests']
        disk_write_reqs = sample['disk.write.requests']
        l1=self.sub1.plot([1, 2, 3, 4], [cpu, memory, disk_read_reqs, disk_write_reqs], server.color, ls=server.shape_line, lw=server.lw)
        l2=self.sub2.plot([1, 2, 3, 4], [cpu, memory, disk_read_reqs, disk_write_reqs], server.color, ls=server.shape_line, lw=server.lw)
        self.sub3.plot([1, 2, 3, 4], [cpu, memory, disk_read_reqs, disk_write_reqs], server.color, ls=server.shape_line, lw=server.lw)




class Monitor(object):
    def __init__(self):
        self.prep_monitor()
        
    def prep_monitor(self):
        self.profiles = []
        self.servers = []
        self.profile_mgr = prof.ProfileManager(self.profiles, mysql)
        self.server_mgr = serv.ServerManager(self.servers, mysql)
        self.start_timestamp = cons.fixed_start_timestamp
        self.end_timestamp = cons.fixed_end_timestamp
        self.tenant = cons.tenant
        self.poll = poller.Poller()
        self.profiles = self.profile_mgr.get_profiles()

        
        self.skmeans = seqkmeans.SequentialKmeans()
        init_samples = self.poll.get_samples_avg(self.tenant, self.start_timestamp, comfuns.add_to_timestamp(self.start_timestamp, 120))
        self.skmeans.initial_guess(init_samples)
        self.skmeans.print_centroid_info()

    def start(self):        
        main_figure = plt.figure(1)
        main_figure2 = plt.figure(2)
        fig = Figure(main_figure, self.skmeans)
        fig2 = Figure2(main_figure2, self.skmeans)
        #fig.prep_3dPlotChart()
        fig.prep_lineChart1()
        fig.prep_lineChart2()
        fig.prep_lineChart3()
        fig.prep_lineChart4()
        fig2.prep_parallelChart()
        #plt.gca().set_color_cycle(['blue', 'green', 'yellow'])
        #plt.locator_params(axis='x',nbins=10)
        #plt.locator_params(axis='y',nbins=10)
        #plt.locator_params(axis='z', nbins=10)

        x = True
        #max_r = 0 
        #max_w = 0
        while True: #self.start_timestamp < self.end_timestamp:
            print self.start_timestamp, comfuns.add_to_timestamp(self.start_timestamp, cons.POLL_INTERVAL)
            samples = self.poll.get_samples_avg(self.tenant, self.start_timestamp, comfuns.add_to_timestamp(self.start_timestamp, cons.POLL_INTERVAL))
            #print samples
            self.start_timestamp = comfuns.add_to_timestamp(self.start_timestamp, cons.POLL_INTERVAL)
            for sample in samples:
                print "============ Sample Info ============="
                print sample, samples[sample]['cpu_util'], samples[sample]['memory.resident']
                print "======================================"
                #Get the server that belongs to the current sample, None otherwise
                server = self.server_mgr.get_server(sample)
                #If new server, create a new server and leave it for sometime to stabilize
                if server is None:
                    print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", "New server detected with id: %s now in stabilizing state", sample
                    dt =  comfuns.add_to_timestamp(samples[sample]['start_duration'], secs=cons.STABILIZE_TIME)
                    server = serv.Server(sample, dt, shape=fig.pts_shapes.pop(0), shape_line=fig2.pts_shapes.pop(0), lw=fig2.pts_lw.pop(0))
                    self.servers.append(server)
                if server is not None and not server.is_stabilize(samples[sample]['start_duration']):
                    continue


                #max_r = max(max_r, samples[sample]['disk.read.requests'])
                #max_w = max(max_w, samples[sample]['disk.write.requests'])
                #print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&", max_r
                #print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&", max_w
                            
                #Update the seq kmeans with the new sample
                anomaly, closest_cent = self.skmeans.update(samples[sample])
                if not anomaly and server.centroid is None:
                    server.centroid = closest_cent
                    server.color = fig.cent_colors[closest_cent]
                
                #Update the graph
                #fig.update_3dPlotChart(samples[sample], anomaly, closest_cent, server)
                fig.update_lineChart1(samples[sample], anomaly, closest_cent, server)
                fig.update_lineChart2(samples[sample], anomaly, closest_cent, server)
                fig.update_lineChart3(samples[sample], anomaly, closest_cent, server)
                fig.update_lineChart4(samples[sample], anomaly, closest_cent, server)
                fig2.update_parallelChart(samples[sample], anomaly, closest_cent, server)
            plt.pause(0.001)

            if x:
                time.sleep(10)
                x = False


#This function gets data from ceilometer
if __name__ == "__main__":
    #connect to nova
    #connection_pool = True for keeping the connection alive as long as the process go(maybe a bad idea!!)
    #nclient = novaclient.client.Client(cons.NOVA_VERSION, cons.USERNAME, cons.PASSWORD, cons.PROJECT_NAME, cons.AUTH_URL, connection_pool=True)
    #connect to ceilometer
    #cclient = ceilometerclient.client.get_client(cons.CEILOMETER_VERSION, os_username=cons.USERNAME, os_password=cons.PASSWORD, os_tenant_name=cons.PROJECT_NAME, os_auth_url=cons.AUTH_URL, connection_pool=True)
    
    #Create the initial profiles(2 for a 2-tier arch.)
    #profile_mgr.create_initial_profile("Webservers", cons.PROJECT_NAME)
    #profile_mgr.create_initial_profile("Database servers", cons.PROJECT_NAME)
    #profile_mgr.create_initial_profile("Application servers", cons.PROJECT_NAME)

    #Get profiles from DB


    #kmeans()

    
    #samples = poll.get_samples_avg(tenant, start_timestamp, end_timestamp)
    #print "\n\n\n", samples#, len(samples)

    #start_timestamp = '2016-09-06 05:12:06'
    #end_timestamp = '2016-09-06 05:21:06'
    #samples = poll.get_samples_avg(tenant, start_timestamp, end_timestamp)
    #print "\n\n\n", samples#, len(samples)
    
    monitor = Monitor()
    monitor.start()
