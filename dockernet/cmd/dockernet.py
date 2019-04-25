"""

# PRE-REQUISITES
1. docker platform must be installed.
2. Python 2.7.x must be installed
3. docker image must be present
4. ODL and docker containers must be running under same subnet same IP range.

"""

import sys
import os
import time
import subprocess

from oslo_config import cfg
from oslo_log import log as logging

logging.register_options(cfg.CONF)
LOG = logging.getLogger(__name__)

CLI_OPTS = [
    cfg.IntOpt('start-switches',
               min=1,
               max=200,
               help='Specify number of switches to run in docker containers'),
    cfg.IntOpt('stop-switches',
               min=1,
               max=200,
               help='Specify number of switches to stop running in docker containers'),
    cfg.StrOpt('controller-ip',
               max_length=16,
               help='controller IPv4 address to make switches connect to controller'),
    cfg.ListOpt('dump',
                help='Dump flows/flow-count/ports/groups/tables/ovs-show output for specified switches'),
    cfg.ListOpt('range',
               help='range of switches number on which dump/ping operation will be performed'),
    cfg.BoolOpt('output-file',
               help='Flag to confirm if output will be written into file'),
    cfg.IntOpt('show-containers-info',
                help='Displays or writes into file - details of running containers'),
    cfg.BoolOpt('show-container-count',
                help='Display count of running containers'),
    cfg.BoolOpt('create-network',
                help='Flag to create network in neutron module'),
    cfg.BoolOpt('create-subnet',
                help='Flag to create subnetwork in neutron module'),
    cfg.BoolOpt('del-neutron-data',
                help='Flag to delete neutron data of network, subnetwork and ports'),
    cfg.IntOpt('add-ports',
               min=1,
               max=30,
               help='Specify number of ports to add to switch running in docker container'),
    cfg.IntOpt('bind-ports',
               min=1,
               max=30,
               help='Specify number of ports to bind port to neutron'),
    cfg.IntOpt('del-ports',
               min=1,
               max=30,
               help='Specify number of ports to delete from switch running in docker container'),
    cfg.BoolOpt('create-ping-ips-file',
                help='Flag to create input file of list of IP addresses to ping each other'),
    cfg.BoolOpt('ping-all',
                help='Flag to ping all IPs present in file'),
    cfg.BoolOpt('cleanup',
                help='Cleanup of ports, ovs, containers and output files')
]


cfg.CONF.register_cli_opts(CLI_OPTS)
DUMP_LIST_ALL = ['flows', 'flow-count', 'ports', 'groups', 'tables','ovs-show']
DEFAULT_COMMAND_LINE_OPTIONS = tuple(sys.argv[1:])

def start_switch_arg_handling(conf):
    err_flag=False
    if conf.start_switches: 
        if conf.stop_switches:
            print("ERROR: --start-switches option can not be given with --stop-switches option.")  
            err_flag=True
        elif  not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --start-switches option.")  
            err_flag=True
	elif conf.dump:
	    print("ERROR: --dump option can not be given with --start-switches option.")
	    err_flag=True
	elif conf.range:
	    print("ERROR: --range option can not be given with --start-switches option.")
	    err_flag=True
        elif conf.show_containers_info:
	    print("ERROR: --show-containers-info option can not be given with --start-switches option.")
	    err_flag=True
        elif conf.show_container_count:
            print("ERROR: --show-container-count option can not be given with --start-switches option.")
            err_flag=True
        elif conf.cleanup:
            print("ERROR: --cleanup option can not be given with --start-switches option.")
            err_flag=True
        elif conf.create_network:
            print("ERROR: --create-network option can not be given with --start-switches option.")
            err_flag=True
        elif conf.create_subnet:
            print("ERROR: --create-subnet option can not be given with --start-switches option.")
            err_flag=True
        elif conf.add_ports:
            print("ERROR: --add-ports option can not be given with --start-switches option.")
            err_flag=True
        elif conf.bind_ports:
            print("ERROR: --bind-ports option can not be given with --start-switches option.")
            err_flag=True
        elif conf.del_ports:
            print("ERROR: --del-ports option can not be given with --start-switches option.")
            err_flag=True
        elif conf.del_neutron_data:
            print("ERROR: --del-neutron-data option can not be given with --start-switches option.")
            err_flag=True
        elif conf.create_ping_ips_file:
            print("ERROR: --create-ping-ips-file option can not be given with --start-switches option.")
            err_flag=True
        elif conf.ping_all:
            print("ERROR: --ping-all option can not be given with --start-switches option.")
            err_flag=True

    return err_flag

def range_opt_validation(range_list):
    if (len(range_list)<2):
        print("ERROR: --range option is not given completely.")
        return -1
    if (range_list[0] == '' or
        range_list[1] == '' or
        len(range_list) > 2 or
        int(range_list[0]) > int(range_list[1]) ):
        print("ERROR: --range option is not given correctly.")
        return -1

    return 0

def check_args_and_perform_action(conf):
    if conf.start_switches:
        err_flag = start_switch_arg_handling(conf)

        if err_flag is True:
            return -1

        # normal switch start case
        docker_ovs_run_connect(conf.start_switches, conf.controller_ip)
        return 0
    elif conf.stop_switches:
        # normal switch stop case
        docker_down(conf.stop_switches)
        return 0
    elif conf.controller_ip:
        if (conf.start_switches is None and
            conf.create_network is None and
            conf.create_subnet is None and
            conf.bind_ports is None and
            conf.del_neutron_data is None and
            conf.cleanup is None):

            print "ERROR: Mandatory to specify --start-switches or ", \
                   "--create-network or --create-subnet or --bind-ports or ", \
                   "--del-neutron-data or --cleanup option with --controller-ip option."
            return -1
        else:
            if conf.create_network:
                create_network(conf.controller_ip)
            if conf.create_subnet:
                create_subnet(conf.controller_ip)
            if conf.bind_ports:
                bind_ports_to_neutron(conf.bind_ports, conf.controller_ip)
            if conf.del_neutron_data:
                del_neutron_data(conf.controller_ip)
            if conf.cleanup:
                cleanup(conf.controller_ip)
            return 0
    elif conf.dump:
        for elem in conf.dump:
            #if elem not in ['all', 'flows', 'ports', 'groups', 'tables', 'ovs-show']:
            if elem != 'all' and elem not in DUMP_LIST_ALL:
                print("ERROR: Wrong value %s is specified with --dump option." % elem)  
                return -1

        if conf.range is None:
            print("ERROR: --range option must also be specified while providing --dump option.")
            return -1
        retval = range_opt_validation(conf.range)
        if (retval == -1):
            return retval

        if 'all' in conf.dump:
            # Perform dump all operation
            for elem in DUMP_LIST_ALL:
                dump_ovs(elem, conf.range, conf.output_file)
            return 0       

        for elem in conf.dump:
            if elem is not 'all':
                # Perform specific dump operation
                dump_ovs(elem, conf.range, conf.output_file)
        return 0
    elif conf.show_containers_info:
        filePath=None
        if conf.output_file:
            prefix = 'show-container-outfile-'
            filePath = get_outfile_path(prefix)

        show_containers_info(conf.show_containers_info, filePath)
        return 0
    elif conf.show_container_count:
        cont_count = get_container_count()
        print(cont_count)
        return 0
    elif conf.cleanup:
        if not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --cleanup option.")  
        return 0
    elif conf.add_ports:
        add_ports_to_ovs(conf.add_ports)
        return 0
    elif conf.bind_ports:
        if not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --bind-ports option.")  
        return 0
    elif conf.del_ports:
        del_and_unbind_ports(conf.del_ports)
        return 0
    elif conf.create_ping_ips_file:
        if conf.range is None:
            print("ERROR: --range option must also be specified while providing --create-ping-ips-file option.")
            return -1
        retval = range_opt_validation(conf.range)
        if (retval == -1):
            return retval

        create_ping_ips_file(conf.range)
        return 0
    elif conf.ping_all:
        if conf.range is None:
            print("ERROR: --range option must also be specified while providing --ping-all option.")
            return -1
        retval = range_opt_validation(conf.range)
        if (retval == -1):
            return retval

        ping_ips_from_file(conf.range, conf.output_file)
        return 0
    elif conf.create_network:
        if not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --create-network option.")  
        return 0
    elif conf.create_subnet:
        if not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --create-subnet option.")  
        return 0
    elif conf.del_neutron_data:
        if not conf.controller_ip:
            print("ERROR: Mandatory to specify --controller-ip with --del-neutron-data option.")  
        return 0
    elif conf.range:
        if (conf.dump is None and
            conf.create_ping_ips_file is None and
            conf.ping_all is None):
            print("ERROR: --dump or --ping-all or --create-ping-ips-file option must be specified while providing --range option.")
            return -1
    else:
        print("ERROR: Options not specified properly.")  
        LOG.error("Options not specified properly.")  
        return -1

def printHelp():
    helpStr="""usage: dockernet [-h]
            [--start-switches NUM_OF_SWITCHES_TO_START]
            [--stop-switches NUM_OF_SWITCHES_TO_STOP]
            [--controller-ip CONTROLLER_IP]
            [--dump <all,flows,flow-count,ports,groups,tables,ovs-show>]
            [--show-container-count] [--show-containers-info NUM_OF_CONTAINERS]
            [--add-ports NUM_OF_PORTS_TO_ADD_TO_SWITCH]
            [--bind-ports NUM_OF_PORTS_TO_BIND_TO_NEUTRON]
            [--del-ports NUM_OF_PORTS_TO_DELETE_FROM_SWITCH]
            [--create-network] [--create-subnet] [--del-neutron-data]
            [--create-ping-ips-file] [--ping-all]
            [--range <START_NUM,END_NUM>]
            [--output-file]
            [--cleanup]"""

    print(helpStr)

def start(args=None):
    if args is None:
        args = DEFAULT_COMMAND_LINE_OPTIONS
        if not args:
            print("No arguments specified.")
            return 0

    if '-h' in args or '--help' in args:
        printHelp()
        return


    conf = cfg.CONF
    # prepare conf
    cfg.CONF(args=args)
    ret = check_args_and_perform_action(conf)
    if (ret != 0):
        return 0

    # prepare log
    DOMAIN = "dockernet"
    logging.setup(conf, DOMAIN)


def system(cmd):
    rc = os.system(cmd)
    if rc != 0:
        sys.stderr.write('Error executing "%s", return code %i\n' % (cmd, rc))
    return rc == 0

def docker_exec(cont_name, cmd):
    cmd = 'docker exec %s %s' % (cont_name, cmd)
    result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    return result

def del_neutron_data(controller_ip):
    #delete neutron data 
    cmd = 'curl -u admin:admin -H "Content-Type: application/json" -X DELETE http://%s:8181/restconf/config/neutron:neutron' % controller_ip
    system(cmd)
    print("Deleted neutron data.")

def del_and_unbind_ports(ports_num):
    sw_count = int(get_container_count())
    for j in range(1,sw_count+1):
        cont_name = 'ovs'+str(j)
        for i in range(1,ports_num+1):
            # prepare port names
            ovsnum="%02d" % j
            portnum="%02d" % i
            tapPortName = "tap2d9def%s-%s" % ( ovsnum, portnum )
            vm_port_name = "vm-port%s%s" % ( ovsnum, portnum )

            # delete tap port on ovs
            cmd = 'docker exec %s ovs-vsctl del-port br-int %s' % ( cont_name, tapPortName )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            # delete vm port
            cmd = 'docker exec %s ip link delete %s' % ( cont_name, vm_port_name )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)

            time.sleep(1)
            print("Deleted %s and %s from %s switch." % ( tapPortName, vm_port_name, cont_name ))

def get_network_id():
    # Get nw ID
    cmd = 'cat /tmp/network.json | grep \\"id\\" | cut -d \'\"\' -f 4'
    network_id = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    network_id = network_id.strip('\n')
    
    return network_id

def get_subnet_id():
    # Get subnet ID
    cmd = 'cat /tmp/subnetwork.json | grep \\"id\\" | cut -d \'\"\' -f 4'
    subnet_id = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    subnet_id = subnet_id.strip('\n')

    return subnet_id

def create_network(controller_ip):
    #create network
    cmd = 'curl -u admin:admin -H "Content-Type: application/json" --data @/tmp/network.json -X POST http://%s:8181/controller/nb/v2/neutron/networks' % controller_ip
    system(cmd)
    print("Created network.")

def create_subnet(controller_ip):
    #create subnetwork
    cmd = 'curl -u admin:admin -H "Content-Type: application/json" --data @/tmp/subnetwork.json -X POST http://%s:8181/controller/nb/v2/neutron/subnets' % controller_ip
    system(cmd)
    print("Created sub-network.")

def get_port_ips_from_ovs(cont_name):
    # create list of IPs of VM ports connected to OVS
    ip_pattern = '20.0'
    cmd = 'docker exec %s ip a show | awk \'/inet / {print $2}\' | grep -o ^[^/]* | grep %s' % (cont_name, ip_pattern)
    try:
        retval = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        port_ips_list = list(retval.split("\n"))
        port_ips_list.remove('')
    except subprocess.CalledProcessError as e:
        port_ips_list = []

    return port_ips_list

def create_ping_ips_file(sw_range):
    ping_ips_file = '/tmp/docker_ping_ips.txt'
    f = open(ping_ips_file,'w')

    start = int(sw_range[0])
    end = int(sw_range[1])
    for j in range(start,end+1):
        cont_name = 'ovs'+str(j)
        ovs_port_ips_list = get_port_ips_from_ovs(cont_name)
        for ip in ovs_port_ips_list:
            f.write(ip + '\n') 

    f.close()
    print("Created file %s containing IP addresses of VM ports in DPNs." % ping_ips_file)

def ping_ips_from_file(sw_range, output_file):
    ping_ips_file = '/tmp/docker_ping_ips.txt'
    f = open(ping_ips_file, 'r')
    port_ips_list_from_file = f.readlines()
    f.close()

    f = None
    if output_file:
        prefix = 'ping-ips-outfile-'
        filePath = get_outfile_path(prefix)
        f = open(filePath,'w')
 
    start = int(sw_range[0])
    end = int(sw_range[1])
    for j in range(start,end+1):
        cont_name = 'ovs'+str(j)
        ovs_port_ips_list = get_port_ips_from_ovs(cont_name)

	if f is None:
            print("================== PING from %s switch ==================" % cont_name)
	else:
            f.write("================== PING from %s switch ==================\n" % cont_name)
            f.flush()
        for src in ovs_port_ips_list:
            for dst in port_ips_list_from_file:
                dst = dst.strip('\n')
                cmd = 'docker exec %s ping -c 2 -I %s %s' % (cont_name, src, dst)
                try:
                    resp = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
                    if '0% packet loss' not in resp:
                        if f is None:
                            print("ping src=%s dst=%s FAILED." % (src, dst))
                        else:
                            f.write("ping src=%s dst=%s FAILED.\n" % (src, dst))
                            f.flush()
                    else:
                        if f is None:
                            print("ping src=%s dst=%s PASSED." % (src, dst))
                        else:
                            f.write("ping src=%s dst=%s PASSED.\n" % (src, dst))
                            f.flush()
                except subprocess.CalledProcessError as e:
                    if f is None:
                        print("ping src=%s dst=%s FAILED." % (src, dst))
                    else:
                        f.write("ping src=%s dst=%s FAILED.\n" % (src, dst))
                        f.flush()
    if f is not None:
        print("--ping-all output is written into %s" % filePath)
        f.close()

def bind_ports_to_neutron(ports_num, controller_ip):
    sw_count = int(get_container_count())
    network_id = get_network_id()
    subnet_id = get_subnet_id()
    for j in range(1,sw_count+1):
        cont_name = 'ovs'+str(j)
        for i in range(1,ports_num+1):
            # Prepare port attribute values
            ovsnum = "%02d" % j
            portnum = "%02d" % i
            tapPortName = "tap2d9def%s-%s" % ( ovsnum, portnum )

            ovs_iface_id = "d6c144c2-%s%s-%s%s-ba74-ceaf8df1ac17" % ( ovsnum, ovsnum, portnum, portnum )
            device_id = "e957c01d-%s%s-%s%s-b79e-17aae1a6733d" % ( ovsnum, ovsnum, portnum, portnum )
            vm_port_name = "vm-port%s%s" % ( ovsnum, portnum )

            # Fetch VM port mac address to set while creating neutron port
            cmd = "docker exec %s ip a show %s  | awk '/ether / {print $2}'" % ( cont_name, vm_port_name )
            port_mac_addr = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            port_mac_addr = port_mac_addr.strip('\n')

            port_ip_addr = '20.0.' + str(j) + '.' + str(i)

            # Create json required in REST URL to create neutron port
            cmd = 'cp /tmp/port.json /tmp/port_copy.json'
            system(cmd)
            filePath = '/tmp/port_copy.json'

            # Update port specific details in the body for json
            cmd = 'sed -i "s/OVS_IFACE_ID/%s/g" %s' % (ovs_iface_id,filePath)
            system(cmd)
            cmd = 'sed -i "s/DEVICE_ID/%s/g" %s' % (device_id,filePath)
            system(cmd)
            cmd = 'sed -i "s/PORT_NAME/%s/g" %s' % (tapPortName,filePath)
            system(cmd)
            cmd = 'sed -i "s/PORT_MAC_ADDR/%s/g" %s' % (port_mac_addr,filePath)
            system(cmd)
            cmd = 'sed -i "s/PORT_IP_ADDR/%s/g" %s' % (port_ip_addr,filePath)
            system(cmd)
            cmd = 'sed -i "s/NETWORK_ID/%s/g" %s' % (network_id,filePath)
            system(cmd)
            cmd = 'sed -i "s/SUBNET_ID/%s/g" %s' % (subnet_id,filePath)
            system(cmd)
            cmd = 'sed -i "s/PORT_SEC_ENABLED/false/g" %s' % (filePath)
            system(cmd)

            # Perform neutron create port operation via REST call
            cmd = 'curl -u admin:admin -H "Content-Type: application/json" --data @/tmp/port_copy.json -X POST http://%s:8181/controller/nb/v2/neutron/ports' % controller_ip
            system(cmd)

            time.sleep(1)
            print("Created neutron port %s and bound to %s on %s switch." % ( ovs_iface_id, tapPortName, cont_name ))

        time.sleep(1)
        print("Created total %d neutron ports on %s switch." % ( ports_num, cont_name  ))


def add_ports_to_ovs(ports_num):
    sw_count = int(get_container_count())
    for j in range(1,sw_count+1):
        cont_name = 'ovs'+str(j)
        for i in range(1,ports_num+1):
            # create tap port
            ovsnum="%02d" % j
            portnum="%02d" % i
            tapPortName="tap2d9def%s-%s" % ( ovsnum, portnum )

            # add tap port to ovs switch with below external_ids attributes
            ovs_iface_id="d6c144c2-%s%s-%s%s-ba74-ceaf8df1ac17" % ( ovsnum, ovsnum, portnum, portnum )
            vm_port_name = "vm-port%s%s" % ( ovsnum, portnum )

            # create veth pair port to emulate guest VM connecting to switch
            cmd = 'docker exec %s ip link add %s type veth peer name %s' % ( cont_name, vm_port_name, tapPortName )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)

            #docker exec ovs$j ip link add nsp$ovsnum$portnum type veth peer name $portName
            port_ip_addr='20.0.' + str(j) + '.' + str(i) + '/16'
            cmd = 'docker exec %s ip addr add %s dev %s' % ( cont_name, port_ip_addr, vm_port_name )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            #docker exec ovs$j ip addr add $port_ip_addr/16 dev nsp$ovsnum$portnum
            cmd = 'docker exec %s ip link set dev %s up' % ( cont_name, vm_port_name )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            #docker exec ovs$j ip link set dev nsp$ovsnum$portnum up

            cmd = 'docker exec %s ovs-vsctl add-port br-int %s -- set Interface %s external_ids:iface-id=%s ' % ( cont_name, tapPortName, tapPortName, ovs_iface_id )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            #docker exec ovs$j ovs-vsctl add-port br-int $portName -- set Interface $portName external_ids:iface-id=$ovs_iface_id

            # Bring UP veth interfaces
            cmd = 'docker exec %s ip link set dev %s up' % ( cont_name, tapPortName )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
            #docker exec ovs$j ip link set dev $portName up

            time.sleep(1)
            print("Created tap port %s on %s switch." % ( tapPortName, cont_name  ))

        time.sleep(1)
        print("Created total %d tap port on %s switch." % ( ports_num, cont_name  ))


def get_dump(dump_key, sw_range, filePath):
    start = int(sw_range[0])
    end = int(sw_range[1])
    f = None
    if filePath is not None:
        f = open(filePath,'w')

    for i in range(start,end+1):
        cont_name = 'ovs'+str(i)
        cmd = ''
        if dump_key == 'ovs-show':
            cmd = 'docker exec %s ovs-vsctl show' % (cont_name)
        elif dump_key == 'flow-count':
            cmd = 'docker exec %s ovs-ofctl dump-flows -O Openflow13 br-int | grep cookie | wc -l' % (cont_name)
        else:
            cmd = 'docker exec %s ovs-ofctl dump-%s -O Openflow13 br-int' % (cont_name, dump_key)

        if filePath is None:
            print('=================== %s %s =====================\n' % (cont_name, dump_key) )
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            f.write('=================== %s %s =====================\n' % (cont_name, dump_key) )
            f.flush()
            subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True)

    if filePath is not None:
        f.flush()
        f.close()
        print("--dump %s output is written into %s" % (dump_key, filePath))
        
        

def dump_ovs(elem, sw_range, output_file):
    filePath=None
    if output_file:
        prefix = 'dump-%s-outfile-' % elem
        filePath = get_outfile_path(prefix)

    get_dump(elem, sw_range, filePath)

def cleanup(controller_ip):
    cont_count = int(get_container_count())
    port_count = get_ports_count()
    # Delete ovs ports and neutron ports
    del_and_unbind_ports(port_count)

    #delete neutron data 
    del_neutron_data(controller_ip)

    # Stop switches and remove containers
    docker_down(cont_count)

    # Removes show-containers, dump, ping-all output files
    cmd = 'rm -f /tmp/show-container-out*.txt  /tmp/dump-*.txt /tmp/ping*.txt'
    system(cmd)
    print ('Removed output files from /tmp dir.')
     

def get_outfile_path(fnamePrefix):
    cmd = 'date +%F-%T'
    dt = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    dt = dt.replace(':','-')
    dt = dt.strip('\n')
    fname = '/tmp/' + fnamePrefix + dt + '.txt'
 
    return fname

def get_docker_image():
    cmd = 'docker images  -q "*dockernet*" '
    dock_img_id = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

    return dock_img_id

def get_container_count():
    cmd='docker ps -a | grep ovs | wc -l'
    cont_count = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    cont_count = cont_count.strip('\n')

    return cont_count

def get_ports_count():
    ovs_list = get_ovs_names_list() 
    cont_name = ovs_list[0]
    port_count = len(get_port_ips_from_ovs(cont_name))

    return port_count

def show_containers_info(count, filePath):
    f = None
    if filePath is not None:
        f = open(filePath,'w')
     
    for i in range(1, count+1):
        container_name = 'ovs' + str(i)
        cmd='docker inspect %s' % container_name
        if filePath is None:
            subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)
        else:
            subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True)

    if filePath is not None:
        f.close()
        print("--show-containers-info output is written into %s" % filePath)

def docker_ovs_run_connect(switch_count, controller_ip):
    running_cont=get_container_count()
    start=int(running_cont)+1
    end=switch_count+start
    for i in range(start, end):
        container_name = 'ovs' + str(i)
        dock_image_id = get_docker_image()
        if not dock_image_id:
            print("Failure: No docker image to run the container.")
            return

        cmd='docker run --name %s -e MODE=tcp:%s -itd --cap-add NET_ADMIN %s ' % ( container_name, controller_ip, dock_image_id )
        system(cmd)
        time.sleep(10)
        print ('Started docker container %s.' % container_name)


def get_ovs_names_list():
    cmd='docker ps -a --filter "name=ovs" --format "{{.Names}}" | sort'
    retval = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    ovs_list=list(retval.split("\n"))
    ovs_list.remove('')

    return ovs_list

def docker_down(end):
    ovs_list = get_ovs_names_list() 
    for i in range(0, end):
        #container_name = 'ovs' + str(i)
        container_name = ovs_list[i]
        # Remove local-ip to remove tunnels from ODL
        system('docker exec %s ovs-vsctl remove Open_vSwitch . other_config local_ip' % container_name)
        time.sleep(2)
        # Disconnect openflow channel
        system('docker exec %s ovs-vsctl del-controller br-int' % container_name )
        # Disconnect ovsdb channel
        system('docker exec %s ovs-vsctl del-manager' % container_name )
        # Stop container and suppress cmd result
        system(('docker stop %s' % container_name) + ' >/dev/null 2>&1')
        # Remove container and suppress cmd result
        system(('docker rm -f %s' % container_name ) + ' >/dev/null 2>&1')

        print ('Stopped docker container %s.' % container_name)

