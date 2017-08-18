# collectd-vcenter - vcenter.py
#
# Author : Loic Lambiel @ exoscale
# Description : This is a collectd python module to gather stats from Vmware vcenter

import collectd
import ssl
from pysphere import VIServer

RUN = 0
INTERVAL = 20

METRIC_TYPES = {
#
#Zone = vCenter Level
    'zonedatacenterscount': ('z_datacenters_count', 'current'),
    'zoneclusterscount': ('z_clusters_count', 'current'),
    'zonehostscount': ('z_hosts_count', 'current'),
    'zonememoryusage': ('z_memory_usage', 'current'),
    'zonecpuusage': ('z_cpu_usage', 'current'),
    'zonememoryusagepercent': ('z_memory_usage_pct', 'current'),
    'zonecpuusagepercent': ('z_cpu_usage_pct', 'current'),
    'zonetotalmemory': ('z_total_memory', 'current'),
    'zonecputotal': ('z_cpu_total', 'current'),
    'zonerunningvms': ('z_vm_running_count', 'current'),
    'zonestoppedvms': ('z_vm_stopped_count', 'current'),
    'zonetotalvms': ('z_vm_total_count', 'current'),
#
#Datacenter
    'datacenterclusterscount': ('d_clusters_count', 'current'),
    'datacenterhostscount': ('d_hosts_count', 'current'),
    'clusterhostscount': ('c_hosts_count', 'current'),
    'datacenterrunningvms': ('d_vm_running_count', 'current'),
    'datacenterstoppedvms': ('d_vm_stopped_count', 'current'),
    'datacentertotalvms': ('d_vm_total_count', 'current'),
    'datacentermemoryusage': ('d_memory_usage', 'current'),
    'datacentercpuusage': ('d_cpu_usage', 'current'),
    'datacentermemoryusagepercent': ('d_memory_usage_pct', 'current'),
    'datacentercpuusagepercent': ('d_cpu_usage_pct', 'current'),
    'datacentertotalmemory': ('d_total_memory', 'current'),
    'datacentercputotal': ('d_cpu_total_count', 'current'),
#
#Cluster
    'clustercpuusage': ('c_cpu_usage', 'current'),
    'clustercputotal': ('c_cpu_total', 'current'),
    'clustercpucount': ('c_cpu_count', 'current'),
    'clustercputhreadcount': ('c_cpu_thread_count', 'current'),
    'clustercpuusagepercent': ('c_cpu_usage_percent', 'current'),
    'clustermemoryusage': ('c_memory_usage', 'current'),
    'clustermemoryusagepercent': ('c_memory_usage_percent', 'current'),
    'clustertotalmemory': ('c_total_memory', 'current'),
    'clusterrunningvms': ('c_vm_running_count', 'current'),
    'clusterstoppedvms': ('c_vm_stopped_count', 'current'),
    'clustertotalvms': ('c_vm_total_count', 'current'),
#
#Host
    'hoststatus': ('h_status', 'current'),
    'hostcpumodel': ('h_cpu_model', 'current'),
    'hostcpuusage': ('h_cpu_usage', 'current'),
    'hostcpuusagepercent': ('h_cpu_usage_pct', 'current'),
    'hostcputotal': ('h_cpu_total', 'current'),
    'hostmemoryusage': ('h_memory_usage', 'current'),
    'hostmemoryusagepercent': ('h_memory_usage_pct', 'current'),
    'hosttotalmemory': ('h_total_memory', 'current'),
    'hostrunningvms': ('h_vm_running_count', 'current'),
    'hoststoppedvms': ('h_vm_stopped_count', 'current'),
    'hosttotalvms': ('h_vm_total_count', 'current'),
    'hostniccount': ('h_nic_count', 'current'),
    'hosthbacount': ('h_hba_count', 'current'),
    'hostcpucount': ('h_cpu_count', 'current'),
    'hostcpupackagecount': ('h_cpu_package_count', 'current'),
    'hostcputhreadcount': ('h_cpu_thread_count', 'current'),
#
#Datastore
    'datastorecapacity': ('z_dscapacity', 'current'),
    'datastorefreespace': ('z_dsfreespace', 'current'),
    'datastoreusagepercent': ('z_dsusage_pct', 'current'),

}

METRIC_DELIM = '.'



def get_stats():
    stats = dict()

    v = VCENTERLIST.split()

    for vcenter in v:

        logger('verb', "get_stats calls vcenter %s user %s" % (vcenter, USERNAME))
        server = VIServer()
	default_context = ssl._create_default_https_context
	ssl._create_default_https_context = ssl._create_unverified_context

        try:
            server.connect(vcenter, USERNAME, PASSWORD)
        except Exception:
            logger('warn', "failed to connect to %s" % (vcenter))
            continue

        # get datastores
        for ds, dsname in server.get_datastores().items():

            DatastoreCapacity = 0
            DatastoreFreespace = 0
            DatastoreUsagePercent = 0

            try:
                logger('verb', "get_stats calls Datastore metrics query on vcenter: %s for datastore: %s" % (vcenter, dsname))

                props = server._retrieve_properties_traversal(property_names=['name', 'summary.capacity', 'summary.freeSpace'], from_node=ds, obj_type="Datastore")

                for prop_set in props:
                    # mor = prop_set.Obj #in case you need it
                        for prop in prop_set.PropSet:
                            if prop.Name == "summary.capacity":
                                DatastoreCapacity = (prop.Val / 1048576)
                            elif prop.Name == "summary.freeSpace":
                                DatastoreFreespace = (prop.Val / 1048576)
            except Exception:
                logger('warn', "failed to get Datastore metrics value on vcenter: %s for datastore: %s" % (vcenter, dsname))

            DatastoreUsagePercent = (((DatastoreCapacity - DatastoreFreespace) * 100) / DatastoreCapacity)

            metricnameZoneDatastoreCapacity = METRIC_DELIM.join([dsname.lower(), 'datastorecapacity'])
            metricnameZoneDatastoreFreespace = METRIC_DELIM.join([dsname.lower(), 'datastorefreespace'])
            metricnameZoneDatastoreUsagePercent = METRIC_DELIM.join([dsname.lower(), 'datastoreusagepercent'])

            try:
                stats[metricnameZoneDatastoreCapacity] = DatastoreCapacity
                stats[metricnameZoneDatastoreFreespace] = DatastoreFreespace
                stats[metricnameZoneDatastoreUsagePercent] = DatastoreUsagePercent
		host = dsname.lower()
            except (TypeError, ValueError):
                pass

        ZoneDatacentersCount = 0
        ZoneClustersCount = 0
        ZoneHostsCount = 0
        ZoneRunningVMS = 0
        ZoneStoppedVMS = 0
        ZoneTotalVMS = 0
        ZoneMemoryUsage = 0
        ZoneCpuUsage = 0
        ZoneTotalMemory = 0
        ZoneCpuTotal = 0

        logger('verb', "get_stats calls get_datacenters query on vcenter: %s" % (vcenter))
        datacenters = server.get_datacenters()
        logger('verb', "get_stats completed get_datacenters query on vcenter: %s" % (vcenter))
        ZoneDatacentersCount = len(datacenters)

        for d, dname in server.get_datacenters().items():

            if "." in dname:
                dname = dname.split(".")[0]

            DatacenterRunningVMS = 0
            DatacenterStoppedVMS = 0
            DatacenterTotalVMS = 0
            DatacenterClustersCount = 0
            DatacenterHostsCount = 0
            DatacenterMemoryUsage = 0
            DatacenterCpuUsage = 0
            DatacenterTotalMemory = 0
            DatacenterCpuTotal = 0

            logger('verb', "get_stats calls get_clusters query on vcenter: %s for datacenter: %s" % (vcenter, dname))
            clusters = server.get_clusters(d)
            logger('verb', "get_stats completed get_clusters query on vcenter: %s for datacenter: %s" % (vcenter, dname))
            DatacenterClustersCount = len(clusters)
            ZoneClustersCount = ZoneClustersCount + DatacenterClustersCount

            for c, cname in server.get_clusters(d).items():

                if "." in cname:
                    cname = cname.split(".")[0]

                ClusterHostsCount = 0
                ClusterCpuCount = 0
                ClusterCpuThreadCount = 0
                ClusterCpuTotal = 0
                ClusterCpuUsage = 0
                ClusterMemoryUsage = 0
                ClusterTotalMemory = 0
                ClusterRunningVMS = 0
                ClusterStoppedVMS = 0
                ClusterTotalVMS = 0

                logger('verb', "get_stats calls get_hosts query on vcenter: %s for cluster: %s" % (vcenter, cname))
                hosts = server.get_hosts(c)
                logger('verb', "get_stats completed get_hosts query on vcenter: %s for cluster: %s" % (vcenter, cname))
                ClusterHostsCount = len(hosts)
                DatacenterHostsCount = DatacenterHostsCount + ClusterHostsCount
                ZoneHostsCount = ZoneHostsCount + DatacenterHostsCount

                for h, hname in server.get_hosts(c).items():

		    HostCPUCount = 0
                    HostCpuUsage = 0
                    HostMhzPerCore = 0
                    HostNumCpuPkgs = 0
                    HostNumCpuCores = 0
                    HostNumCpuThreads = 0
                    HostMemoryUsage = 0
                    HostTotalMemory = 0
		    HostNICCount = 0
		    HostHBACount = 0
                    HostStatus = ''
                    HostCPUModel = ''

                    if "." in hname:
                        hname = hname.split(".")[0]

                    try:
                        logger('verb', "get_stats calls Host CPU and Memory metrics query on vcenter: %s for host: %s" % (vcenter, hname))

                        props = server._retrieve_properties_traversal(property_names=['name', 'summary.overallStatus', 'summary.quickStats.overallMemoryUsage', 'summary.quickStats.overallCpuUsage', 'summary.hardware.memorySize', 'summary.hardware.numCpuCores', 'summary.hardware.numCpuPkgs', 'summary.hardware.numCpuThreads', 'summary.hardware.cpuMhz', 'summary.hardware.cpuModel', 'summary.hardware.numNics', 'summary.hardware.numHBAs'], from_node=h, obj_type="HostSystem")

                        for prop_set in props:
                            # mor = prop_set.Obj #in case you need it
                            for prop in prop_set.PropSet:
                                if prop.Name == "summary.quickStats.overallMemoryUsage":
                                    HostMemoryUsage = prop.Val
                                elif prop.Name == "summary.quickStats.overallCpuUsage":
                                    HostCpuUsage = prop.Val
                                elif prop.Name == "summary.hardware.memorySize":
                                    HostTotalMemory = (prop.Val / 1048576)
                                elif prop.Name == "summary.hardware.numCpuPkgs":
                                    HostNumCpuPkgs = prop.Val
                                elif prop.Name == "summary.hardware.numCpuCores":
                                    HostNumCpuCores = prop.Val
                                elif prop.Name == "summary.hardware.numCpuThreads":
                                    HostNumCpuThreads = prop.Val
                                elif prop.Name == "summary.hardware.cpuMhz":
                                    HostMhzPerCore = prop.Val
                                elif prop.Name == "summary.hardware.numNics":
                                    HostNICCount = prop.Val
                                elif prop.Name == "summary.hardware.numHBAs":
                                    HostHBACount = prop.Val
                                elif prop.Name == "summary.hardware.numCpuCores":
                                    HostCPUCount = prop.Val
                                elif prop.Name == "summary.hardware.cpuModel":
                                    HostCPUModel = prop.Val
                                elif prop.Name == "summary.overallStatus":
                                    HostStatus = prop.Val
                                    if HostStatus == "green":
                                        HostStatus = 0
                                    elif HostStatus == "gray":
                                        HostStatus = 1
                                    elif HostStatus == "yellow":
                                        HostStatus = 2
                                    elif HostStatus == "red":
                                        HostStatus = 3
                    except Exception:
                        logger('warn', "failed to get Host CPU and Memory metrics value on vcenter: %s for host: %s" % (vcenter, hname))

                    try:
                        logger('verb', "get_stats calls HostRunningVMS query on vcenter: %s for host: %s" % (vcenter, hname))
                        HostRunningVMS = len(server.get_registered_vms(h, status='poweredOn'))
                    except Exception:
                        logger('warn', "failed to get nb of running VMS value on %s" % (hname))
                    try:
                        logger('verb', "get_stats calls HostStoppedVMS query on vcenter: %s for host: %s" % (vcenter, hname))
                        HostStoppedVMS = len(server.get_registered_vms(h, status='poweredOff'))
                    except Exception:
                        logger('warn', "failed to get nb of stopped VMS value on %s" % (hname))
                    try:
                        logger('verb', "get_stats calls HostTotalVMS query on vcenter: %s for host: %s" % (vcenter, hname))
                        HostTotalVMS = len(server.get_registered_vms(h))
                    except Exception:
                        logger('warn', "failed to get all VMS count on %s" % (hname))

                    HostCpuTotal = (HostNumCpuCores * HostMhzPerCore)
		    HostCPUPackageCount = HostNumCpuPkgs
		    HostCPUThreadsCount = (HostNumCpuPkgs * HostNumCpuCores)
		    HostCPUCount = HostNumCpuCores
                    HostMemoryUsagePercent = ((HostMemoryUsage * 100) / HostTotalMemory)
                    HostCpuUsagePercent = ((HostCpuUsage * 100) / HostCpuTotal)

                    metricnameHostStatus = METRIC_DELIM.join([hname.lower(), 'hoststatus'])
                    metricnameHostCpuUsage = METRIC_DELIM.join([hname.lower(), 'hostcpuusage'])
		    metricnameHostCPUCount = METRIC_DELIM.join([hname.lower(), 'hostcpucount'])
                    metricnameHostCpuTotal = METRIC_DELIM.join([hname.lower(), 'hostcputotal'])
		    metricnameHostCPUPackageCount = METRIC_DELIM.join([hname.lower(), 'hostcpupackagecount'])
		    metricnameHostCPUThreadsCount = METRIC_DELIM.join([hname.lower(), 'hostcputhreadcount'])
                    metricnameHostCpuUsagePercent = METRIC_DELIM.join([hname.lower(), 'hostcpuusagepercent'])
                    metricnameHostMemoryUsagePercent = METRIC_DELIM.join([hname.lower(), 'hostmemoryusagepercent'])
                    metricnameHostMemoryUsage = METRIC_DELIM.join([hname.lower(), 'hostmemoryusage'])
                    metricnameHostTotalMemory = METRIC_DELIM.join([hname.lower(), 'hosttotalmemory'])
                    metricnameHostRunningVMS = METRIC_DELIM.join([hname.lower(), 'hostrunningvms'])
                    metricnameHostStoppedVMS = METRIC_DELIM.join([hname.lower(), 'hoststoppedvms'])
                    metricnameHostTotalVMS = METRIC_DELIM.join([hname.lower(), 'hosttotalvms'])
		    metricnameHostNICCount = METRIC_DELIM.join([hname.lower(), 'hostniccount'])
		    metricnameHostHBACount = METRIC_DELIM.join([hname.lower(), 'hosthbacount'])

                    ClusterCpuCount = ClusterCpuCount + HostNumCpuCores
                    ClusterCpuThreadCount = ClusterCpuThreadCount + HostCPUThreadsCount
                    ClusterCpuUsage = ClusterCpuUsage + HostCpuUsage
                    ClusterCpuTotal = ClusterCpuTotal + HostCpuTotal
                    ClusterCpuUsagePercent = ((ClusterCpuUsage * 100) / ClusterCpuTotal)
                    ClusterMemoryUsage = ClusterMemoryUsage + HostMemoryUsage
                    ClusterTotalMemory = ClusterTotalMemory + HostTotalMemory
                    ClusterMemoryUsagePercent = ((ClusterMemoryUsage * 100) / ClusterTotalMemory)
                    ClusterRunningVMS = ClusterRunningVMS + HostRunningVMS
                    ClusterStoppedVMS = ClusterStoppedVMS + HostStoppedVMS
                    ClusterTotalVMS = ClusterTotalVMS + HostTotalVMS



                    try:
                        stats[metricnameHostStatus] = HostStatus
                        stats[metricnameHostCpuUsage] = HostCpuUsage
                        stats[metricnameHostCpuUsagePercent] = HostCpuUsagePercent
                        stats[metricnameHostCpuTotal] = HostCpuTotal
			stats[metricnameHostCPUCount] = HostCPUCount
			stats[metricnameHostCPUPackageCount] = HostCPUPackageCount
			stats[metricnameHostCPUThreadsCount] = HostCPUThreadsCount
                        stats[metricnameHostMemoryUsage] = HostMemoryUsage
                        stats[metricnameHostTotalMemory] = HostTotalMemory
                        stats[metricnameHostMemoryUsagePercent] = HostMemoryUsagePercent
                        stats[metricnameHostRunningVMS] = HostRunningVMS
                        stats[metricnameHostStoppedVMS] = HostStoppedVMS
                        stats[metricnameHostTotalVMS] = HostTotalVMS
			stats[metricnameHostNICCount] = HostNICCount
			stats[metricnameHostHBACount] = HostHBACount
                    except (TypeError, ValueError):
                        pass

                DatacenterRunningVMS = DatacenterRunningVMS + ClusterRunningVMS
                DatacenterStoppedVMS = DatacenterStoppedVMS + ClusterStoppedVMS
                DatacenterTotalVMS = DatacenterTotalVMS + ClusterTotalVMS
                DatacenterMemoryUsage = DatacenterMemoryUsage + ClusterMemoryUsage
                DatacenterCpuUsage = DatacenterCpuUsage + ClusterCpuUsage
                DatacenterTotalMemory = DatacenterTotalMemory + ClusterTotalMemory
                DatacenterCpuTotal = DatacenterCpuTotal + ClusterCpuTotal
                DatacenterMemoryUsagePercent = ((DatacenterMemoryUsage * 100) / DatacenterTotalMemory)
                DatacenterCpuUsagePercent = ((DatacenterCpuUsage * 100) / DatacenterCpuTotal)

                metricnameClusterCpuCount = METRIC_DELIM.join([cname.lower(), 'clustercpucount'])
                metricnameClusterCpuThreadCount = METRIC_DELIM.join([cname.lower(), 'clustercputhreadcount'])
                metricnameClusterCpuTotal = METRIC_DELIM.join([cname.lower(), 'clustercputotal'])
                metricnameClusterCpuUsage = METRIC_DELIM.join([cname.lower(), 'clustercpuusage'])
                metricnameClusterCpuUsagePercent = METRIC_DELIM.join([cname.lower(), 'clustercpuusagepercent'])
                metricnameClusterHostsCount = METRIC_DELIM.join([cname.lower(), 'clusterhostscount'])
                metricnameClusterMemoryUsage = METRIC_DELIM.join([cname.lower(), 'clustermemoryusage'])
                metricnameClusterMemoryUsagePercent = METRIC_DELIM.join([cname.lower(), 'clustermemoryusagepercent'])
                metricnameClusterTotalMemory = METRIC_DELIM.join([cname.lower(), 'clustertotalmemory'])
                metricnameClusterRunningVMS = METRIC_DELIM.join([cname.lower(), 'clusterrunningvms'])
                metricnameClusterStoppedVMS = METRIC_DELIM.join([cname.lower(), 'clusterstoppedvms'])
                metricnameClusterTotalVMS = METRIC_DELIM.join([cname.lower(), 'clustertotalvms'])


                try:
                    stats[metricnameClusterHostsCount] = ClusterHostsCount
                    stats[metricnameClusterCpuCount] = ClusterCpuCount
                    stats[metricnameClusterCpuThreadCount] = ClusterCpuThreadCount
                    stats[metricnameClusterCpuTotal] = ClusterCpuTotal
                    stats[metricnameClusterCpuUsage] = ClusterCpuUsage
                    stats[metricnameClusterCpuUsagePercent] = ClusterCpuUsagePercent
                    stats[metricnameClusterMemoryUsage] = ClusterMemoryUsage
                    stats[metricnameClusterMemoryUsagePercent] = ClusterMemoryUsagePercent
                    stats[metricnameClusterTotalMemory] = ClusterTotalMemory
                    stats[metricnameClusterRunningVMS] = ClusterRunningVMS
                    stats[metricnameClusterStoppedVMS] = ClusterStoppedVMS
                    stats[metricnameClusterTotalVMS] = ClusterTotalVMS
                except (TypeError, ValueError):
                    pass

            # post datacenter metrics count here

            ZoneRunningVMS = ZoneRunningVMS + DatacenterRunningVMS
            ZoneStoppedVMS = ZoneStoppedVMS + DatacenterStoppedVMS
            ZoneTotalVMS = ZoneTotalVMS + DatacenterTotalVMS
            ZoneMemoryUsage = ZoneMemoryUsage + DatacenterMemoryUsage
            ZoneCpuUsage = ZoneCpuUsage + DatacenterCpuUsage
            ZoneTotalMemory = ZoneTotalMemory + DatacenterTotalMemory
            ZoneCpuTotal = ZoneCpuTotal + DatacenterCpuTotal
            ZoneMemoryUsagePercent = ((ZoneMemoryUsage * 100) / ZoneTotalMemory)
            ZoneCpuUsagePercent = ((ZoneCpuUsage * 100) / ZoneCpuTotal)

            metricnameDatacenterRunningVMS = METRIC_DELIM.join([dname.lower(), 'datacenterrunningvms'])
            metricnameDatacenterStoppedVMS = METRIC_DELIM.join([dname.lower(), 'datacenterstoppedvms'])
            metricnameDatacenterTotalVMS = METRIC_DELIM.join([dname.lower(), 'datacentertotalvms'])
	    metricnameDatacenterHostsCount = METRIC_DELIM.join([dname.lower(), 'datacenterhostscount'])
            metricnameDatacenterMemoryUsage = METRIC_DELIM.join([dname.lower(), 'datacentermemoryusage'])
            metricnameDatacenterCpuUsage = METRIC_DELIM.join([dname.lower(), 'datacentercpuusage'])
            metricnameDatacenterMemoryUsagePercent = METRIC_DELIM.join([dname.lower(), 'datacentermemoryusagepercent'])
            metricnameDatacenterCpuUsagePercent = METRIC_DELIM.join([dname.lower(), 'datacentercpuusagepercent'])
            metricnameDatacenterTotalMemory = METRIC_DELIM.join([dname.lower(), 'datacentertotalmemory'])
            metricnameDatacenterCpuTotal = METRIC_DELIM.join([dname.lower(), 'datacentercputotal'])

            try:
                stats[metricnameDatacenterRunningVMS] = DatacenterRunningVMS
                stats[metricnameDatacenterStoppedVMS] = DatacenterStoppedVMS
                stats[metricnameDatacenterTotalVMS] = DatacenterTotalVMS
                stats[metricnameDatacenterHostsCount] = DatacenterHostsCount
                stats[metricnameDatacenterMemoryUsage] = DatacenterMemoryUsage
                stats[metricnameDatacenterCpuUsage] = DatacenterCpuUsage
                stats[metricnameDatacenterMemoryUsagePercent] = DatacenterMemoryUsagePercent
                stats[metricnameDatacenterCpuUsagePercent] = DatacenterCpuUsagePercent
                stats[metricnameDatacenterTotalMemory] = DatacenterTotalMemory
                stats[metricnameDatacenterCpuTotal] = DatacenterCpuTotal
            except (TypeError, ValueError):
                pass

        # post zone metrics count here
        metricnameZoneRunningVMS = METRIC_DELIM.join([vcenter.lower(), 'zonerunningvms'])
        metricnameZoneStoppedVMS = METRIC_DELIM.join([vcenter.lower(), 'zonestoppedvms'])
        metricnameZoneTotalVMS = METRIC_DELIM.join([vcenter.lower(), 'zonetotalvms'])
        metricnameZoneMemoryUsage = METRIC_DELIM.join([vcenter.lower(), 'zonememoryusage'])
        metricnameZoneCpuUsage = METRIC_DELIM.join([vcenter.lower(), 'zonecpuusage'])
        metricnameZoneMemoryUsagePercent = METRIC_DELIM.join([vcenter.lower(), 'zonememoryusagepercent'])
        metricnameZoneCpuUsagePercent = METRIC_DELIM.join([vcenter.lower(), 'zonecpuusagepercent'])
        metricnameZoneTotalMemory = METRIC_DELIM.join([vcenter.lower(), 'zonetotalmemory'])
        metricnameZoneCpuTotal = METRIC_DELIM.join([vcenter.lower(), 'zonecputotal'])

        try:
            stats[metricnameZoneRunningVMS] = ZoneRunningVMS
            stats[metricnameZoneStoppedVMS] = ZoneStoppedVMS
            stats[metricnameZoneTotalVMS] = ZoneTotalVMS
            stats[metricnameZoneMemoryUsage] = ZoneMemoryUsage
            stats[metricnameZoneCpuUsage] = ZoneCpuUsage
            stats[metricnameZoneMemoryUsagePercent] = ZoneMemoryUsagePercent
            stats[metricnameZoneCpuUsagePercent] = ZoneCpuUsagePercent
            stats[metricnameZoneTotalMemory] = ZoneTotalMemory
            stats[metricnameZoneCpuTotal] = ZoneCpuTotal
        except (TypeError, ValueError):
            pass

        metricnameZoneDatacentersCount = METRIC_DELIM.join([vcenter.lower(), 'zonedatacenterscount'])
        metricnameZoneClustersCount = METRIC_DELIM.join([vcenter.lower(), 'zoneclusterscount'])
        metricnameZoneHostsCount = METRIC_DELIM.join([vcenter.lower(), 'zonehostscount'])

        try:
            stats[metricnameZoneDatacentersCount] = ZoneDatacentersCount
            stats[metricnameZoneClustersCount] = ZoneClustersCount
            stats[metricnameZoneHostsCount] = ZoneHostsCount
        except (TypeError, ValueError):
            pass

        server.disconnect()
    return stats


# callback configuration for module
def configure_callback(conf):

    global NAME, VCENTERLIST, USERNAME, PASSWORD, VERBOSE_LOGGING, SKIP
    NAME = 'Vcenter'
    VCENTERLIST = ''
    USERNAME = ''
    PASSWORD = ''
    VERBOSE_LOGGING = False
    SKIP = 10

    for node in conf.children:
        if node.key == "Vcenter":
            VCENTERLIST = node.values[0]
        elif node.key == "Username":
            USERNAME = node.values[0]
        elif node.key == "Password":
            PASSWORD = node.values[0]
        elif node.key == "Verbose":
            VERBOSE_LOGGING = bool(node.values[0])
        elif node.key == "Skip":
            SKIP = int(node.values[0])
        else:
            logger('warn', 'Unknown config key: %s' % node.key)


def read_callback():
    global RUN, SKIP
    RUN += 1
    if RUN % SKIP != 1:
        return
    logger('verb', "beginning read_callback")
    info = get_stats()

    if not info:
        logger('warn', "%s: No data received" % NAME)
        return

    for key, value in info.items():
        key_prefix = ''
        key_root = key
        logger('verb', "read_callback key %s" % (key))
        logger('verb', "read_callback value %s" % (value))
        if value not in METRIC_TYPES:
            try:
                key_prefix, key_root = key.rsplit(METRIC_DELIM, 1)
            except ValueError:
                pass
        if key_root not in METRIC_TYPES:
            continue

        key_root, val_type = METRIC_TYPES[key_root]
        key_name = METRIC_DELIM.join([key_prefix, key_root])
        logger('verb', "key_name %s" % (key_name))
	host_name = key_prefix
        val = collectd.Values(plugin=NAME, type=key_root)
	val.host = host_name
        val.type_instance = key
        val.values = [value]
        val.dispatch()


# logging function
def logger(t, msg):
    if t == 'err':
        collectd.error('%s: %s' % (NAME, msg))
    elif t == 'warn':
        collectd.warning('%s: %s' % (NAME, msg))
    elif t == 'verb':
        if VERBOSE_LOGGING:
            collectd.info('%s: %s' % (NAME, msg))
    else:
        collectd.notice('%s: %s' % (NAME, msg))

# main
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
