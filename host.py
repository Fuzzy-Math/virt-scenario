#!/usr/bin/env python3
# Authors: Antoine Ginies <aginies@suse.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Prepare the Host system
"""

import uuid
from string import Template
import template
import util

def create_net_xml(file, net_data):
    """
    Create a libvirt XML for the network bridge
    """
    xml_template = template.NETWORK_TEMPLATE
    xml_net = {
        'network_uuid': str(uuid.uuid4()),
        'network_name': net_data['network_name'],
        'bridge': net_data['bridge'],
        'stp': net_data['stp'],
        'ip': net_data['ip'],
        'netmask': net_data['netmask'],
        'dhcp_start': '.'.join(net_data['ip'].split('.')[0:3]+[net_data['dhcp_start']]),
        'dhcp_end': '.'.join(net_data['ip'].split('.')[0:3]+[net_data['dhcp_end']]),
    }

    xml = Template(xml_template).substitute(xml_net)
    print("Create network bridge " +file)
    with open(file, 'w') as file_h:
        file_h.write(xml)


def create_storage_vol_xml(file, storage_data):
    """
    Create storage vol xml
    """
    xml_template = template.STORAGE_TEMPLATE
    xml_storage = {
        'storage_uuid': str(uuid.uuid4()),
        'storage_name': storage_data['storage_name'],
        'allocation': storage_data['allocation'],
        'unit': storage_data['unit'],
        'capacity': storage_data['capacity'],
        'path': storage_data['path']+'.'+storage_data['type'],
        'owner': storage_data['owner'],
        'group': storage_data['group'],
        'mode': storage_data['mode'],
        'label': storage_data['label'],
        }

    xml = Template(xml_template).substitute(xml_storage)
    print("Create storage volume " +file)
    with open(file, 'w') as file_h:
        file_h.write(xml)

def create_storage_image(storage_data):
    """
    Create the storage image
    TODO check value
    """
    #ie: qemu-img create -f qcow2 Win2k.img 20G
    cmd = "qemu-img create"
    cmdoptions = "-f "+storage_data['type']+" "+storage_data['path']+'.'+storage_data['type']+" "+storage_data['capacity']+storage_data['unit']
    # on / off
    lazyref = "lazy_refcounts="+storage_data['lazy_refcounts']
    # cluster size: 512k / 2M
    clustersize = "cluster_size="+storage_data['cluster_size']
    # on / off
    preallocation = "preallocation="+storage_data['preallocation']
    # zlib zstd
    compression_type = "compression_type="+storage_data['compression_type']

    cmdall = cmd+" "+cmdoptions+" -o "+lazyref+","+clustersize+","+preallocation+","+compression_type
    print(cmdall)
    out, errs = util.system_command(cmdall)
    if errs:
        print(errs)
    if not out:
        print(' No output... seems weird...')
    else:
        print(out)

def check_cpu_flag(flag):
    """
    check if a CPU flag is present
    """
    cpuinfo = open("/proc/cpuinfo")
    data = cpuinfo.read()
    test = data.find(flag)
    cpuinfo.close()
    return test

def check_sev_enable():
    """
    check that sev is enable on this system
    """
    sevinfo = open("/sys/module/kvm_amd/parameters/sev")
    #sevinfo = open("/sys/module/kvm/supported")
    data = sevinfo.read()
    test = data.find("1")
    sevinfo.close()
    return test

def enable_sev():
    """
    enable sev on the system
    """
    sevconf = open("/etc/modprobe.d/sev.conf", "w")
    sevconf.write("options kvm_amd sev=1")
    sevconf.close()

def reprobe_the_module():
    """
    reload the module
    """
    cmd = "modprobe -vr kvm_amd ; modprobe -v kvm_amd"
    out, errs = util.system_command(cmd)
    util.print_summary("\nReprobe the KVM module")
    if errs:
        print(errs)
    print(out)

def kvm_amd_sev():
    """
    be sure kvm_amd sev is enable if not enable it
    https://documentation.suse.com/sles/15-SP1/html/SLES-amd-sev/index.html
    """
    util.print_summary("Host section")
    util.print_summary("Enabling sev if needed")
    flag = "sev"
    test_flag = check_cpu_flag(flag)
    if test_flag <= -1:
        util.print_error(" "+flag+" flag not found...")
        util.print_error("WARNING: You can not do secure VM on this system")
    else:
        util.print_ok("Found "+flag+" CPU flag")
        test_sev = check_sev_enable()
        if test_sev <= -1:
            util.print_error(" SEV not enable on this system")
            enable_sev()
            reprobe_the_module()
        else:
            util.print_ok(" SEV enable on this system")

# Storage
STORAGE_DATA = {
    'storage_name': 'storage_name',
    'allocation': '0',
    'unit': 'G',
    'capacity': '2',
    'path': '/tmp/testname',
    'type': 'qcow2',
    'owner': '107',
    'group': '107',
    'mode': '0744',
    'label': 'storage_label',
    # qemu-img creation options (-o)
    'cluster_size': '2M',
    'lazy_refcounts': 'on',
    'preallocation': 'full',
    'compression_type': 'zlib',
}
#create_storage_vol_xml("storage.xml", STORAGE_DATA)

# Net data
NET_DATA = {
    'network_name': "test_net",
    'bridge': "br0",
    'stp': "on",
    'ip': "192.168.12.1",
    'netmask': "255.255.255.0",
    'dhcp_start': "30",
    'dhcp_end': "254",
}

#create_net_xml("net.xml", NET_DATA)
#create_storage_image(STORAGE_DATA)

#kvm_amd_sev()
