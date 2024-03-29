"""This script iterates through the different connections and checks the macs addresses of the vms in the hosts"""

import libvirt
import random
from xml.etree import ElementTree as ET
import time

class Utils:
    @staticmethod
    def generate_mac():
        mac = [0x52, 0x54, 0x00,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    @staticmethod
    def generate_unique_mac(macs):
        new_mac = Utils.generate_mac()
        while new_mac in macs:
            new_mac = Utils.generate_mac()
        return new_mac


class Connection:
    def __init__(self, username, ipaddress, protocol):
        if protocol and username and ipaddress:
            self.uri = f'qemu+{protocol}://{username}@{ipaddress}/system'
        else:
            self.uri = 'qemu:///system'

    def connect(self):
        self.conn = libvirt.open(self.uri)
        
        if self.conn:
            print("Connection established")
        else:
            print("Unable to connect")
            exit(1)
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
            print("Connection disconnected")
        else:
            print("No connection exists")
    
    def listAllDomains(self):
        return self.conn.listAllDomains()
    
    def listAllActiveDomains(self):
        return [dom for dom in self.listAllDomains() if dom.ID() > 0]
        
    def lookupByName(self, domainName):
        return self.conn.lookupByName(domainName)
    
    def defineXML(self, xml):
        return self.conn.defineXML(xml)

class Domain:
    def __init__(self, dom = None):
        self.dom = dom

    @staticmethod
    def lookupByName(conn, name):
        return Domain(conn.lookupByName(name))
    
    def getXML(self):
        return self.dom.XMLDesc(0)

    def shutdown(self):
        if self.dom.ID() > 0:
            return self.dom.shutdown()
        else:
            return True
    
    def isActive(self):
        return self.dom.isActive()
    
    def ensureShutdown(self):
        i = 0
        self.shutdown()
        while self.isActive():
            time.sleep(1)
            i += 1
            if i > 20:
                self.shutdown()
    
    def updateByXML(self, conn, xml):
        self.ensureShutdown()
        conn.defineXML(xml)

    def start(self):
        return self.dom.create()

class Driver:
    @staticmethod
    def unique_macs(hosts, active_only = True):
        host_conns = [Connection(host['username'], host['ipaddress'], host['protocol'])  for host in hosts ]
        for host_conn in host_conns:
            host_conn.connect()
        
        macs = {}
        conflict = {}

        for conn in host_conns:
            if active_only:
                domains = conn.listAllActiveDomains()
            else:
                domains = conn.listAllDomains()
            if domains is None:
                print("Failed to get list of domains")
            
            for dom in domains:
                xml_root = ET.fromstring(dom.XMLDesc(0))

                for interface in xml_root.findall("./devices/interface/mac"):
                    mac_address = interface.get("address")
                    print(f"Domain ID {dom.ID()}, Name: {dom.name()}, MAC: {mac_address}")
                    if mac_address in macs:
                        conflict[dom.name()] = [conn, old_mac]
                        print(f"Confict found at {dom.ID()}, Name: {dom.name()}, MAC: {mac_address}")
                    else:
                        macs[mac_address] = dom.name()

        for domainName, conn_details in conflict.items():
            old_mac = conn_details[1]
            conn =  conn_details[0]
            new_mac = Utils.generate_unique_mac(macs)
            macs[new_mac] = domainName
            Driver.update_vm_mac_address(conn, domainName, old_mac, new_mac)
        
        if not conflict:
            print("No conflicting macs found")
    
    @staticmethod
    def update_vm_mac_address(conn, domainName, old_mac, new_mac):
        dom = Domain.lookupByName(conn, domainName)
        dom.shutdown()

        xml_root = ET.fromstring(dom.getXML())
        updated = False
        
        for interface in xml_root.findall("./devices/interface"):
            mac_element = interface.find("mac")
            if mac_element.get("address") == old_mac:
                mac_element.set("address", new_mac)
                updated = True
                print("MAC found and replaced")
                break
        
        if updated:
            new_xml_desc = ET.tostring(xml_root, encoding='unicode')
            dom.updateByXML(conn,new_xml_desc)
            print("MAC address updated")
            dom.start()
            print("Domain restarted")

def main():

    hosts = [
        {'username': 'vmadm', 'ipaddress':'192.168.38.16', 'protocol': 'ssh'},
        {'username': 'vmadm', 'ipaddress':'192.168.38.17', 'protocol': 'ssh'},
    ]
    Driver.unique_macs(hosts, active_only=True)

if __name__ == '__main__':
    main()

