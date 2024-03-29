import os
import sys
import json
import socket
import sqlite3
import requests
import pathlib
import time
import uuid

PATH = str(pathlib.Path(__file__).parent.absolute()) + os.path.sep
DB_FILENAME = "net_devs.db"
ip_address = None
mac_address = None
ip_mask = None
conn = None #connection variable
seconds = 10 # seconds before another scan

def get_ip_mask():
    global ip_address, mac_address, ip_mask
    #read ip address for network with internet access
    ip_address = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
                  [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
    #assume that the mask is 0/24
    ip_mask = ip_address.split('.')
    ip_mask[3] = '0/24'
    ip_mask = '.'.join(ip_mask)
    #read and format mac address
    mac_address = (':'.join(['{:02x}'.format(
        (uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1]))
    mac_address = mac_address.upper()

    return ip_mask

def scan_network_devices(ip_mask):
    global PATH
    #stream = os.popen('cd %s;git pull' %(PATH))
    #sys.stdout.flush()
    stream = os.popen('nmap --privileged -sn %s' %(ip_mask))
    #stream = os.popen('nmap --privileged -sn %s' %(ip_mask))
    output = stream.read()
    outputList = output.splitlines()
    
    init = 1 #first line contains nmap version
    #fin = len(outputList) - (1 + 3)# 1 - last line, 3 - the scanning device itself
    fin = len(outputList) - 1 #last line is irrelevant
    devices_list = []

    for i in range(init, fin, 3):
        ip = 'None'
        mac = 'None'
        vendor = 'Unknown'
        device_name = ''
        line0 = outputList[i]
        line1 = outputList[i+1] #never used, we do not need this line
        line2 = outputList[i+2] 
        
        #Nmap scan report for 192.168.x.x
        ip = line0.replace('Nmap scan report for ', '') #remove everything but ip
        device_name = ''
        #ip can contain device name sometimes
        if(ip.find('(') > -1):
            device_name = ip[0: ip.find('(')-1]
            ip = ip.replace(ip[0: ip.find('(')+1], '')
            ip = ip.replace( ')', '')
        
        if line1: #Host is up (0.0024s latency).
            pass
        if(line2.startswith('MAC Address:')):
            mac = line2 [13 : 30]
            vendor = line2 [32: len(line2)-1] #we will scan vendor online
        elif(line2.startswith('Nmap done')):
            global ip_address, mac_address
            if ip == ip_address:
                mac = mac_address

        device = {
            'ip': ip,
            'mac': mac,
            'vendor': vendor,
            'device_name': device_name
        }

        devices_list.append(device)
    devices_list = scan_vendors(devices_list)
    return devices_list

def db_clear_table(db_table):
    global conn
    cur = conn.cursor()
    cur.execute("DELETE FROM %s" %db_table)
    conn.commit()

def db_store_devices(devices_list, db_table):
    global conn
    cur = conn.cursor()

    for device in devices_list:
        cur.execute("INSERT INTO %s (mac, ip, vendor, device_name) VALUES ('%s', '%s', '%s', '%s')" %(db_table, device['mac'], device['ip'], device['vendor'], device['device_name']))
    conn.commit()

def create_database(db_file):
    create_devices_table ="""CREATE TABLE "devices" ( "mac" TEXT NOT NULL, "ip" TEXT NOT NULL, "vendor" TEXT, "device_name" TEXT, PRIMARY KEY("mac") )"""
    create_previous_devices_table = """CREATE TABLE "previous_devices" ( "mac" TEXT NOT NULL, "ip" TEXT NOT NULL, "vendor" TEXT, "device_name" TEXT, PRIMARY KEY("mac") )"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(create_devices_table)
    c.execute(create_previous_devices_table)
    conn.commit()
    conn.close()

def create_connection():
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    global conn
    global PATH 
    db_file = PATH  + DB_FILENAME

    if not os.path.isfile(db_file):
        create_database(db_file)
    conn = None    
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
        conn.close()
        sys.exit(1)

def select_all_devices(db_table):
    """
    Query all rows in the devices table
    :return:
    """
    global conn
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM %s" %db_table)
    devices_list = cur.fetchall()
    return devices_list

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_devices_from_db(db_table):
    create_connection()
    devices_list = select_all_devices(db_table)
    return devices_list

def get_connected_devices(devices_list, devices_list_prev1, devices_list_prev2):
    connected_devs = []
    if (len(devices_list_prev1) > 0 and len(devices_list_prev2) > 0):
        for dev in devices_list:
            res1 = len(list(filter(lambda d: d['mac'] == dev['mac'], devices_list_prev1)))
            res2 = len(list(filter(lambda d: d['mac'] == dev['mac'], devices_list_prev2)))
            if(res1 == res2 and res2 == 0):
                connected_devs.append(dev)
    return connected_devs

def get_disconnected_devices(devices_list, devices_list_prev1, devices_list_prev2):
    disconnected_devs = []
    if (len(devices_list_prev1) > 0 and len(devices_list_prev2) > 0):
        for dev in devices_list_prev2:
            res1 = len(list(filter(lambda d: d['mac'] == dev['mac'], devices_list_prev1)))
            res2 = len(list(filter(lambda d: d['mac'] == dev['mac'], devices_list)))
            if(res1 == res2 and res2 == 0):
                disconnected_devs.append(dev)
    return disconnected_devs

def scan_vendors(devices_list):
    for device in devices_list:
        mac = device['mac'].replace(":", "-")
        response = requests.get("https://api.macvendors.com/%s" %mac)
        if(response.status_code == 200):
            device['vendor'] = response.text
            time.sleep(0.5)
    return devices_list

def db_update_devices(devices_list, devices_list_prev1):
    db_clear_table("devices")
    db_store_devices(devices_list, "devices")
    #db_clear_table("previous_devices")
    devices_list_prev2 = get_devices_from_db("previous_devices")
    macun = [dict_elem for dict_elem in devices_list if dict_elem["mac"] not in [d["mac"] for d in devices_list_prev2]]
    if macun:
        db_store_devices(macun, "previous_devices")
#    if not devices_list_prev2:
#        db_store_devices(devices_list_prev1, "previous_devices")

def get_current_devices(devices_list, devices_list_prev1):
    sum_list = devices_list + devices_list_prev1
    current_devices = list({dev['mac']:dev for dev in sum_list}.values())
    return current_devices

def main():
    print("Function executed at:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    global conn
    ip_mask = get_ip_mask()
    #scan network for devices
    devices_list = scan_network_devices(ip_mask)
    #get devices from db
    devices_list_prev1 = get_devices_from_db("devices")
    #print("bruh")
    devices_list_prev2 = get_devices_from_db("previous_devices")
    #print(devices_list_prev2)
    #print("bruh")
    #update devices --------------------------------
    db_update_devices(devices_list, devices_list_prev1)
    #-----------------------------------------------
    current_devices = get_current_devices(devices_list, devices_list_prev1)
    connected_devs = get_connected_devices(devices_list, devices_list_prev1, devices_list_prev2)
    disconnected_devs = get_disconnected_devices(devices_list, devices_list_prev1, devices_list_prev2)

    res = {
        "current_devices": current_devices,
        "connected": connected_devs,
        "disconnected": disconnected_devs
    }
    res = json.dumps(res)
    conn.close()
    print(res)
    
if __name__ == "__main__":
    while True:
        main()
        time.sleep(seconds) 