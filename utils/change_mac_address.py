
"""This program will replace the first interface of the domain with given mac address"""

import libvirt
import time
import xml.etree.ElementTree as ET

# Connect to the local libvirt daemon
conn = libvirt.open('qemu:///system')
if conn is None:
    raise Exception("Failed to open connection to qemu:///system")

domain_name = 'base'  

replace_first = True
new_mac = '52:54:00:88:a2:2f'  # Replace new_mac_address with the desired MAC address
old_mac = None # Define mac which you want to replace with new
start_vm = True

if not replace_first:
    assert old_mac is not None
assert new_mac is not None

try:
    # Fetch the domain by its ID
    domain = conn.lookupByName(domain_name)

    if domain.isActive():
        print("Shutting down the domain...")
        domain.shutdown()
        
        # Wait for the domain to be fully shut down
        while domain.isActive():
            print("Waiting for the domain to shut down...")
            time.sleep(1)
        print("Domain is shut down.")
    
    # Get the current XML configuration of the domain
    xml_desc = domain.XMLDesc(0)
    
    # Parse the XML
    xml_root = ET.fromstring(xml_desc)
    
    # Find the MAC address element and update it
    if replace_first:
        for mac in xml_root.iter('mac'):
            mac.set('address', new_mac)
            break
    else:
        for mac in xml_root.iter('mac'):
            if mac.get("address") == old_mac:
                mac.set('address', new_mac)


    
    # Get the updated XML configuration as a string
    new_xml_desc = ET.tostring(xml_root, encoding='unicode')
    
    
    # Redefine the domain with the new XML configuration
    conn.defineXML(new_xml_desc)
    
    print(f"MAC address successfully changed to {new_mac} for domain Name {domain_name}")

    # Start the domain
    if start_vm:
        domain.create()
        print("Domain has been started.")
    
except libvirt.libvirtError as e:
    print(f"An error occurred: {e}")

finally:
    # Close the connection
    conn.close()
