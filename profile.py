import server
import constants as cons
from termcolor import colored

#This class contains a profile information
class Profile(object):

    def __init__(self):
        self.id = None
        self.name = None
        self.last_updated = None
        self.samples_count = None
        #Profile feautures
        self.cpu_util_avg = None
        self.memory_usage_avg = None

class ProfileManager(object):

    def __init__(self, profiles, mysql):
        self.mysql = mysql
        self.profiles = profiles

    def match_server_to_profile(self, profiles, server):
        print "Checking server", server.id, "profile"
        is_matched = False
        #if server doesn't belong to any profile yet, try matching it to an existing one
        if server.profile_id is None:
            print "Server doesn't belongs to a profile, trying matching it's behaviour to a profile..."
            for profile in profiles:
                print "Server cpu_util:", server.cpu_util_avg, "Profile cpu_util: ", profile.cpu_util_avg
                if (profile.cpu_util_avg - cons.CPU_UTIL_AVG_MARGIN_ERROR) <= server.cpu_util_avg <= (profile.cpu_util_avg + cons.CPU_UTIL_AVG_MARGIN_ERROR):
                    server.profile_id = profile.id
                    is_matched = True
                    #May a server match more than one profile???
                    break
        else:
            print "Server already belongs to a profile, trying matching it's behaviour to that profile..."
            profile = next((profile for profile in profiles if profile.id == server.profile_id), None)
            print "Server cpu_util:", server.cpu_util_avg, "Profile cpu_util: ", profile.cpu_util_avg
            if (profile.cpu_util_avg - cons.CPU_UTIL_AVG_MARGIN_ERROR) <= server.cpu_util_avg <= (profile.cpu_util_avg + cons.CPU_UTIL_AVG_MARGIN_ERROR):
                server.profile_id = profile.id
                is_matched = True

        if not is_matched:
            print colored("Matching [Failed], incident have been reported", "red")
        else: 
            print colored("Matching [OK]", "green")
        return is_matched

    #Get profile information from DB and store it in profile objects
    def get_profiles(self):
        sql = "SELECT * FROM profiles"
        self.mysql.cur.execute(sql)
        profiles = []
        for row in self.mysql.cur.fetchall():
            profile = Profile()
            profile.name = row["name"]
            profile.id = row["id"]
            profile.samples_count = row["samples_count"]
            profile.cpu_util_avg = row["cpu_util_avg"]
            profile.memory_usage_avg = row["memory_usage_avg"]
            profile.last_updated = row["last_updated"]
            profiles.append(profile)
        return profiles
    
    def create_initial_profile(self, profile_name, project_name):
        sql = "INSERT INTO profiles (name, project_name) VALUES (%s, %s)"
        self.mysql.cur.execute(sql, (profile_name, project_name))
        self.mysql.commit()

