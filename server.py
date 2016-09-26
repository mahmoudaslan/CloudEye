import datetime
import constants as cons

class Server(object):
    def __init__(self, id, stabilizing_timestamp, profile_id = None, shape = None, shape_line = None, lw = None):
        self.id = id
        self.profile_id = profile_id
        self.stabilizing_done = False
        self.stabilizing_timestamp = stabilizing_timestamp
        
        #Current monitored data
        self.cpu_util_avg = None
        self.memory_resident_avg = None

        #Instance shape to be viewed on graph
        self.shape = shape
        self.shape_line = shape_line
        self.centroid = None
        self.color = 'r'
        self.lw = lw
        
    #Check if the server stabilizing time is complete
    def is_stabilize(self, timestamp):
        if self.stabilizing_timestamp <= timestamp:
            self.stabilizing_done = True
        if self.stabilizing_done:
            return True
        return False

class ServerManager(object):
    def __init__(self, servers, mysql):
        self.servers = servers
        self.mysql = mysql

    #Return the server object or none if not available
    def get_server(self, server_id):
        return next((server for server in self.servers if server.id == server_id), None)

    #TODO: Should be able to delete a server from the db

    #Commit changes to DB
    #TODO: Should use openstack MySQL classes once migrated to openstack service
    #TODO: check for sql injection
    def commit(self):
        for server in servers:
            sql = "INSERT INTO servers (id, profile_id) VALUES (" + server.id + ", " + server.profile_id + ") "
            sql += "ON DUPLICATE KEY UPDATE profile_id = " + server.profile_id + ";"
            self.mysql.execute(sql)

    def is_tracking_done(self, server):
        sql = "SELECT CASE WHEN EXISTS (SELECT * FROM servers WHERE id = " + server.id + ") THEN CAST(1 AS BIT) ELSE CAST(0 AS BIT) END"
        self.mysql.execute(sql)


