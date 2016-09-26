import ceilometerclient.client
import novaclient
from novaclient import client
import datetime
import inspect
import server as serv
import profile as prof
import poller
import constants as cons
import mysql
import math
import time
from termcolor import colored
import logging
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

#This function returns the last processed timestamp for the service to complete from where it stopped
def get_last_processed_timestamp():
    #TODO: Implementation needed when database is ready
    #return datetime.datetime.strptime("2016-04-20T22:38:11.957100", TIMESTAMP_FORMAT)
    #return datetime.datetime.strptime("2016-06-20T13:25:27.505537", cons.TIMESTAMP_FORMAT)
    return datetime.datetime.now() - datetime.timedelta(seconds=30)

#TODO: should change to 1 request to ceilometer not 2
def get_samples(start_timestamp):
    demo_tenant = u'5bd9457e680e4c7aad93c435441f2927'
    end_timestamp = start_timestamp + datetime.timedelta(seconds=cons.POLL_INTERVAL)
    query = [dict(field='timestamp', op='gt', value=start_timestamp), dict(field='timestamp', op='lt', value=end_timestamp)]
    samples = {}

    #Get cpu util samples
    stats = cclient.statistics.list(meter_name='cpu_util', groupby=['resource_id', 'project_id'], q = query)
    #print stats
    if len(stats) > 0:
        for stat in stats:
            #filter based on demo tenant(a little hack that must be change)
            if (stat.groupby['project_id'] != demo_tenant):
                continue
            samples[stat.groupby['resource_id']] = {}
            samples[stat.groupby['resource_id']]['cpu_util_avg'] = stat.avg
            samples[stat.groupby['resource_id']]['project_id'] = stat.groupby['project_id']
            samples[stat.groupby['resource_id']]['samples_count'] = stat.count
            samples[stat.groupby['resource_id']]['duration_start'] = stat.duration_start
            samples[stat.groupby['resource_id']]['duration_end'] = stat.duration_end

    #Get memory resident samples
    stats = cclient.statistics.list(meter_name='memory.resident', groupby=['resource_id', 'project_id'], q = query)
    #print stats
    if len(stats) > 0:
        for stat in stats:
            #filter based on demo tenant(a little hack that must be change)
            #Should be based on the project name not ID
            if (stat.groupby['project_id'] != demo_tenant):
                continue
            if stat.groupby['resource_id'] in samples:
                samples[stat.groupby['resource_id']]['memory_resident_avg'] = stat.avg
        start_timestamp = datetime.datetime.strptime(stat.duration_end, cons.TIMESTAMP_FORMAT)
    else:
        start_timestamp = end_timestamp if end_timestamp < datetime.datetime.now() else start_timestamp

    #Check if samples are having all features
    for sample in list(samples):
        delete = False
        if 'cpu_util_avg' not in samples[sample]:
            delete = True
        if 'memory_resident_avg' not in samples[sample]:
            delete = True
        if delete:
            print sample
            del samples[sample]
    
    samples = normalize_samples(samples)
    return samples, start_timestamp

#Normalize samples to percentage
def normalize_samples(samples):
    #print samples
    for sample in samples:
        samples[sample]['memory_resident_avg'] = float(samples[sample]['memory_resident_avg']) / float(cons.MAX_MEM) * 100.0
    return samples

def is_server_stabilize(server, timestamp):
    if server is not None and server.stabilizing_done is False:
        if server.stabilizing_timestamp <= datetime.datetime.strptime(timestamp, cons.TIMESTAMP_FORMAT):
            server.stabilizing_done = True
            print "Server", server.id, "stabilizing stage completed"
        else:
            print "Server", server.id, "is still in stabilizing stage"
    if server is not None and server.stabilizing_done:
        return True
    else:
        return False
    

def kmeans():
    #Generating live graph
    #fig, ax = plt.subplots()
    fig1 = plt.figure(1)
    fig1_sub1 = fig1.add_subplot(111, projection='3d')
    plt.locator_params(axis='x',nbins=10)
    plt.locator_params(axis='y',nbins=10)
    plt.locator_params(axis='z', nbins=10)
    #fig1_sub1.set_xlim(0, 100)
    #fig1_sub1.set_ylim(0, 100)
    #fig1_sub1.set_zlim(0, 100)
    
    #plt.axis([0, 100, 0, 100, 0, 100])
    plt.ion()
    fig1_sub1.set_ylabel("Memory Resident(%)")
    fig1_sub1.set_xlabel("CPU Utilization(%)")
    fig1_sub1.set_zlabel("Time(minutes)")
    plt.pause(0.05)

    start_timestamp = get_last_processed_timestamp()
    logging.info("Starting at %s", start_timestamp)

    #Make initial guess to means(just take two data points from 2 diff. VMs)
    samples, start_timestamp = get_samples(start_timestamp)
    end_timestamp = start_timestamp + datetime.timedelta(seconds=cons.POLL_INTERVAL)
    centroids = [(0, 0, 0), (0, 0, 0), (0, 0, 0)]
    cent_names = []
    c = 0
    #print samples
    #TODO: [IMPORTANT] this needs to change as the initial instances running before the monitor maybe > or < than the number of centroids
    for sample in samples:
        cent_names.append(sample)
        centroids[c] = (float(samples[sample]['cpu_util_avg']), float(samples[sample]['memory_resident_avg']), 0)
        c = c + 1
    start_date = datetime.datetime.strptime(samples[sample]['duration_start'], cons.TIMESTAMP_FORMAT)
    #================ Print Initial Centroids values =================#
    print "************************** Initial centroids values *************************************************"
    print "Centroid 1 => {cpu_util_avg: ", centroids[0][0], "} {memory_resident_avg: ", centroids[0][1], "} {Samples count: ", centroids[0][2], "}"
    print "Centroid 2 => {cpu_util_avg: ", centroids[1][0], "} {memory_resident_avg: ", centroids[1][1], "} {Samples count: ", centroids[1][2], "}"
    print "Centroid 2 => {cpu_util_avg: ", centroids[2][0], "} {memory_resident_avg: ", centroids[2][1], "} {Samples count: ", centroids[2][2], "}"
    print "*****************************************************************************************************"

    #Points color: red belongs to centroid 0, black belongs to centroid 1
    c0 = 'b'
    c1 = 'g'
    c2 = 'y'
    c_anomaly = 'r'
    #List of available shapes for VMs
    pts_shapes = ['o', 's', 'D', '^', '*', '>', '<', 'v']

    #Draw initial centroids
    xpoints = [centroids[0][0], centroids[1][0], centroids[2][0]]
    ypoints = [centroids[0][1], centroids[1][1], centroids[2][1]]
    zpoints = [0, 0, 0]
    points, = fig1_sub1.plot(xpoints, ypoints, zpoints, marker='+', linestyle='None', markersize=10, mew=3, alpha=0.6, c='k')
    #print points.pop(0)

    for i in range (len(cent_names)):
        srv = nclient.servers.find(id = cent_names[i])
        if (srv.security_groups[0]['name'] == "db-server-sec-grp"):
            cent_names[i] = fig1_sub1.text(centroids[i][0], centroids[i][1], centroids[i][2], "dbservers")
        elif (srv.security_groups[0]['name'] == "webserver-sec-grp"):
            cent_names[i] = fig1_sub1.text(centroids[i][0], centroids[i][1], centroids[i][2], "webservers")
        elif (srv.security_groups[0]['name'] == "appserver-sec-grp"):
            cent_names[i] = fig1_sub1.text(centroids[i][0], centroids[i][1], centroids[i][2], "appservers")

    points.set_xdata(xpoints)
    points.set_ydata(ypoints)
    points.set_3d_properties(zpoints)
    #points.set_data(xpoints, ypoints, zpoints)
    plt.pause(0.05)


    while (True):
        #plt.pause(0.05)
        samples, start_timestamp = get_samples(start_timestamp)
        #end_timestamp = start_timestamp + datetime.timedelta(seconds=cons.POLL_INTERVAL)
        logging.info("Polled %s samples at time %s", len(samples), start_timestamp)
        for sample in samples:
            #Get the server that belongs to the current stat, None otherwise
            server = next((server for server in servers if server.id == sample), None)
            
            #If new server, create a new server and leave it for sometime to stabilize
            if server is None:
                logging.info("New server detected with id: %s now in stabilizing state", sample)
                dt =  datetime.datetime.strptime(samples[sample]['duration_start'], cons.TIMESTAMP_FORMAT) + datetime.timedelta(seconds=cons.STABILIZE_TIME)
                servers.append(serv.Server(sample, dt, shape=pts_shapes.pop(0)))
            if is_server_stabilize(server, samples[sample]['duration_start']):
                cpu = float(samples[sample]['cpu_util_avg'])
                memory = float(samples[sample]['memory_resident_avg'])
                server.cpu_util_avg = cpu
                server.memory_resident_avg = memory
                time_in_minutes = (datetime.datetime.strptime(samples[sample]['duration_start'], cons.TIMESTAMP_FORMAT) - start_date).total_seconds()/60
                logging.info("Time: %s New point => VM: %s | CPU_Util: %s | MEM_Resident: %s", samples[sample]['duration_end'], sample, cpu, memory)
                
                #Check closest centroid to the current sample
                closest_cent = 0
                closest_d = 1000000
                for i in range(len(centroids)):
                    d = math.hypot(centroids[i][0] - cpu, centroids[i][1] - memory)
                    print "Distance between two points(", centroids[i][0], ", ",  centroids[i][1], ") and (", cpu, ",", memory, ") = ", d
                    if d < closest_d:
                        closest_d = d
                        closest_cent = i
                print closest_cent

                flag = True
                #Check for anomalies
                if (closest_d > cons.ANOMALY_THRESHOLD):
                    flag = False
                    print colored("Matching [Failed], incident have been reported", "red")
                    fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c_anomaly, marker=server.shape)
                    #continue
                else:
                    print colored("Matching [OK]", "green")

                mx = centroids[closest_cent][0]
                my = centroids[closest_cent][1]
                n = centroids[closest_cent][2] + 1
                
                x = cpu
                y = memory
                print "mx: " , mx
                print "(1/n)", (1.0/n)
                print "(x-mx)", (x-mx)
                centroids[closest_cent] = (mx + (1.0/n) * (x-mx), my + (1.0/n) * (y-my), n)
                print "New centroid: (", centroids[closest_cent][0], ", ",  centroids[closest_cent][1], ")", "Count: ", centroids[closest_cent][2]

                
                
                #Draw the updated centroids
                xpoints[closest_cent] = centroids[closest_cent][0]
                ypoints[closest_cent] = centroids[closest_cent][1]
                zpoints[closest_cent] = time_in_minutes
                points.set_3d_properties(zpoints)
                points.set_data(xpoints, ypoints)
                
                cent_names[closest_cent].set_x(centroids[closest_cent][0])
                cent_names[closest_cent].set_y(centroids[closest_cent][1])
                cent_names[closest_cent].set_3d_properties(time_in_minutes)


                #Draw the sample point
                if flag:
                    if closest_cent == 0:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c0, marker=server.shape)
                    elif closest_cent == 1:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c1, marker=server.shape)
                    elif closest_cent == 2:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c2, marker=server.shape)

        plt.pause(5)
        #time.sleep(20)
        print "========================================================"
    
def add_to_timestamp(timestamp, secs):
    return datetime.datetime.strptime(timestamp, cons.TIMESTAMP_FORMAT) + datetime.timedelta(seconds=secs)



def sequential_kmeans():
    profiles = profile_mgr.get_profiles()

    start_timestamp = '2016-09-06 05:19:05'
    end_timestamp = '2016-09-06 05:51:00'
    tenant = 'db0d6c08f675447fac289f4b75b3a97f'
    
    poll = poller.Poller()

    while start_timestamp < end_timestamp:
        samples = poll.get_samples_avg(tenant, start_timestamp, add_to_timestamp(start_timestamp, =cons.STABILIZE_TIME))
        for sample in samples:
            #Get the server that belongs to the current sample, None otherwise
            server = get_server(sample)
            #If new server, create a new server and leave it for sometime to stabilize
            if server is None:
                print "New server detected with id: %s now in stabilizing state", sample
                dt =  add_to_timestamp(samples[sample]['duration_start'], seconds=cons.STABILIZE_TIME)
                servers.append(serv.Server(sample, dt, shape=pts_shapes.pop(0)))
            if is_server_stabilize(server, samples[sample]['duration_start']):
                cpu = float(samples[sample]['cpu_util_avg'])
                memory = float(samples[sample]['memory_resident_avg'])
                server.cpu_util_avg = cpu
                server.memory_resident_avg = memory
                time_in_minutes = (datetime.datetime.strptime(samples[sample]['duration_start'], cons.TIMESTAMP_FORMAT) - start_date).total_seconds()/60
                logging.info("Time: %s New point => VM: %s | CPU_Util: %s | MEM_Resident: %s", samples[sample]['duration_end'], sample, cpu, memory)
                
                #Check closest centroid to the current sample
                closest_cent = 0
                closest_d = 1000000
                for i in range(len(centroids)):
                    d = math.hypot(centroids[i][0] - cpu, centroids[i][1] - memory)
                    print "Distance between two points(", centroids[i][0], ", ",  centroids[i][1], ") and (", cpu, ",", memory, ") = ", d
                    if d < closest_d:
                        closest_d = d
                        closest_cent = i
                print closest_cent

                flag = True
                #Check for anomalies
                if (closest_d > cons.ANOMALY_THRESHOLD):
                    flag = False
                    print colored("Matching [Failed], incident have been reported", "red")
                    fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c_anomaly, marker=server.shape)
                    #continue
                else:
                    print colored("Matching [OK]", "green")

                mx = centroids[closest_cent][0]
                my = centroids[closest_cent][1]
                n = centroids[closest_cent][2] + 1
                
                x = cpu
                y = memory
                print "mx: " , mx
                print "(1/n)", (1.0/n)
                print "(x-mx)", (x-mx)
                centroids[closest_cent] = (mx + (1.0/n) * (x-mx), my + (1.0/n) * (y-my), n)
                print "New centroid: (", centroids[closest_cent][0], ", ",  centroids[closest_cent][1], ")", "Count: ", centroids[closest_cent][2]

                
                
                #Draw the updated centroids
                xpoints[closest_cent] = centroids[closest_cent][0]
                ypoints[closest_cent] = centroids[closest_cent][1]
                zpoints[closest_cent] = time_in_minutes
                points.set_3d_properties(zpoints)
                points.set_data(xpoints, ypoints)
                
                cent_names[closest_cent].set_x(centroids[closest_cent][0])
                cent_names[closest_cent].set_y(centroids[closest_cent][1])
                cent_names[closest_cent].set_3d_properties(time_in_minutes)


                #Draw the sample point
                if flag:
                    if closest_cent == 0:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c0, marker=server.shape)
                    elif closest_cent == 1:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c1, marker=server.shape)
                    elif closest_cent == 2:
                        fig1_sub1.scatter(float(cpu), float(memory), time_in_minutes, alpha=0.5, c=c2, marker=server.shape)

        plt.pause(5)
        #time.sleep(20)
        print "========================================================"


#TODO: should be the main thread
#This function gets data from ceilometer
if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    #connect to nova
    #connection_pool = True for keeping the connection alive as long as the process go(maybe a bad idea!!)
    #nclient = novaclient.client.Client(cons.NOVA_VERSION, cons.USERNAME, cons.PASSWORD, cons.PROJECT_NAME, cons.AUTH_URL, connection_pool=True)
    #connect to ceilometer
    #cclient = ceilometerclient.client.get_client(cons.CEILOMETER_VERSION, os_username=cons.USERNAME, os_password=cons.PASSWORD, os_tenant_name=cons.PROJECT_NAME, os_auth_url=cons.AUTH_URL, connection_pool=True)
    
    servers = []
    profiles = []

    profile_mgr = prof.ProfileManager(profiles, mysql)
    server_mgr = serv.ServerManager(servers, mysql)

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
