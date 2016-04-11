# Copyright 2012-2016 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test object factories."""

__all__ = [
    "factory",
    "Messages",
    ]

from datetime import timedelta
import hashlib
from io import BytesIO
import logging
import random
import time

from distro_info import UbuntuDistroInfo
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.utils import timezone
from maasserver.clusterrpc.power_parameters import get_power_types
from maasserver.enum import (
    ALLOCATED_NODE_STATUSES,
    BOOT_RESOURCE_FILE_TYPE,
    BOOT_RESOURCE_TYPE,
    CACHE_MODE_TYPE,
    FILESYSTEM_FORMAT_TYPE_CHOICES,
    FILESYSTEM_GROUP_TYPE,
    FILESYSTEM_TYPE,
    INTERFACE_TYPE,
    IPADDRESS_TYPE,
    IPRANGE_TYPE,
    NODE_STATUS,
    NODE_TYPE,
    PARTITION_TABLE_TYPE,
    POWER_STATE,
    RDNS_MODE,
)
from maasserver.fields import (
    LargeObjectFile,
    MAC,
)
from maasserver.models import (
    BlockDevice,
    BootResource,
    BootResourceFile,
    BootResourceSet,
    BootSource,
    BootSourceCache,
    BootSourceSelection,
    CacheSet,
    Device,
    DHCPSnippet,
    DNSData,
    DNSResource,
    Domain,
    Event,
    EventType,
    Fabric,
    FanNetwork,
    FileStorage,
    Filesystem,
    FilesystemGroup,
    IPRange,
    LargeFile,
    LicenseKey,
    Node,
    Partition,
    PartitionTable,
    PhysicalBlockDevice,
    RackController,
    RegionController,
    RegionControllerProcess,
    RegionControllerProcessEndpoint,
    RegionRackRPCConnection,
    Service,
    Space,
    SSHKey,
    SSLKey,
    StaticIPAddress,
    Subnet,
    Tag,
    VersionedTextFile,
    VirtualBlockDevice,
    VLAN,
    VolumeGroup,
    Zone,
)
from maasserver.models.blockdevice import MIN_BLOCK_DEVICE_SIZE
from maasserver.models.bmc import BMC
from maasserver.models.bootresourceset import (
    COMMISSIONABLE_SET,
    XINSTALL_TYPES,
)
from maasserver.models.interface import (
    Interface,
    InterfaceRelationship,
)
from maasserver.models.node import typecast_node
from maasserver.models.partition import MIN_PARTITION_SIZE
from maasserver.node_status import NODE_TRANSITIONS
from maasserver.testing import get_data
from maasserver.utils.converters import round_size_to_nearest_block
from maasserver.utils.orm import reload_object
import maastesting.factory
from maastesting.factory import TooManyRandomRetries
from maastesting.typecheck import typed
from metadataserver.enum import RESULT_TYPE
from metadataserver.fields import Bin
from metadataserver.models import (
    CommissioningScript,
    NodeResult,
)
from netaddr import (
    IPAddress,
    IPNetwork,
)
from provisioningserver.utils.enum import map_enum
from provisioningserver.utils.network import inet_ntop

# We have a limited number of public keys:
# src/maasserver/tests/data/test_rsa{0, 1, 2, 3, 4}.pub
MAX_PUBLIC_KEYS = 5


ALL_NODE_STATES = list(map_enum(NODE_STATUS).values())


# Use `undefined` instead of `None` for default factory arguments when `None`
# is a reasonable value for the argument.
undefined = object()


class Messages:
    """A class to record messages published by Django messaging
    framework.
    """

    def __init__(self):
        self.messages = []

    def add(self, level, message, extras):
        self.messages.append((level, message, extras))

    def __iter__(self):
        for message in self.messages:
            yield message


class Factory(maastesting.factory.Factory):

    def make_fake_request(self, path, method="GET"):
        """Create a fake request.

        :param path: The path to which to make the request.
        :param method: The method to use for the request
            ('GET' or 'POST').
        """
        rf = RequestFactory()
        request = rf.get(path)
        request.method = method
        request._messages = Messages()
        return request

    def make_file_upload(self, name=None, content=None):
        """Create a file-like object for upload in http POST or PUT.

        To upload a file using the Django test client, just include a
        parameter that maps not to a string, but to a file upload as
        produced by this method.

        :param name: Name of the file to be uploaded.  If omitted, one will
            be made up.
        :type name: `unicode`
        :param content: Contents for the uploaded file.  If omitted, some
            contents will be made up.
        :type content: `bytes`
        :return: A file-like object, with the requested `content` and `name`.
        """
        if content is None:
            content = self.make_string().encode(settings.DEFAULT_CHARSET)
        if name is None:
            name = self.make_name('file')
        assert isinstance(content, bytes)
        upload = BytesIO(content)
        upload.name = name
        return upload

    def pick_choice(self, choices, but_not=None):
        """Pick a random item from `choices`.

        :param choices: A sequence of choices in Django form choices format:
            [
                ('choice_id_1', "Choice name 1"),
                ('choice_id_2', "Choice name 2"),
            ]
        :param but_not: A list of choices' IDs to exclude.
        :type but_not: Sequence.
        :return: The "id" portion of a random choice out of `choices`.
        """
        if but_not is None:
            but_not = ()
        return random.choice(
            [choice for choice in choices if choice[0] not in but_not])[0]

    def pick_power_type(self, but_not=None):
        """Pick a random power type and return it.

        :param but_not: Exclude these values from result
        :type but_not: Sequence
        """
        if but_not is None:
            but_not = []
        else:
            but_not = list(but_not)
        but_not.append('')
        return random.choice(
            [choice for choice in list(get_power_types().keys())
                if choice not in but_not])

    def pick_commissioning_release(self, osystem):
        """Pick a random commissioning release from operating system."""
        releases = osystem.get_supported_commissioning_releases()
        return random.choice(releases)

    def pick_ubuntu_release(self, but_not=None):
        """Pick a random supported Ubuntu release.

        :param but_not: Exclude these releases from the result
        :type but_not: Sequence
        """
        ubuntu_releases = UbuntuDistroInfo()
        supported_releases = ubuntu_releases.all[
            ubuntu_releases.all.index('precise'):]
        if but_not is None:
            but_not = []
        return random.choice(
            [choice for choice in supported_releases if choice not in but_not],
        )

    def _save_node_unchecked(self, node):
        """Save a :class:`Node`, but circumvent status transition checks."""
        valid_initial_states = NODE_TRANSITIONS[None]
        NODE_TRANSITIONS[None] = ALL_NODE_STATES
        try:
            node.save()
        finally:
            NODE_TRANSITIONS[None] = valid_initial_states

    def make_Device(self, hostname=None, interface=False, domain=None,
                    disable_ipv4=None, vlan=None, fabric=None, **kwargs):
        if hostname is None:
            hostname = self.make_string(20)
        if disable_ipv4 is None:
            disable_ipv4 = self.pick_bool()
        if domain is None:
            domain = Domain.objects.get_default_domain()
        device = Device(
            hostname=hostname, disable_ipv4=disable_ipv4, domain=domain,
            **kwargs)
        device.save()
        if interface:
            self.make_Interface(
                INTERFACE_TYPE.PHYSICAL, node=device, vlan=vlan, fabric=fabric)
        return reload_object(device)

    def make_RegionController(self, hostname=None):
        if hostname is None:
            hostname = self.make_string(20)
        region = RegionController(hostname=hostname)
        region.save()
        return region

    def make_RegionControllerProcess(
            self, region=None, pid=None, updated=None):
        if region is None:
            region = self.make_RegionController()
        if pid is None:
            pid = random.randint(1, 10000)
        process = RegionControllerProcess(
            region=region, pid=pid, updated=updated)
        process.save()
        return process

    def make_RegionControllerProcessEndpoint(
            self, process=None, address=None, port=None):
        if process is None:
            process = self.make_RegionControllerProcess()
        if address is None:
            address = self.make_ip_address()
        if port is None:
            port = random.randint(1, 10000)
        endpoint = RegionControllerProcessEndpoint(
            process=process, address=address, port=port)
        endpoint.save()
        return endpoint

    def make_RegionRackRPCConnection(
            self, rack_controller=None, endpoint=None):
        if rack_controller is None:
            rack_controller = self.make_RackController()
        if endpoint is None:
            endpoint = self.make_RegionControllerProcessEndpoint()
        conn = RegionRackRPCConnection(
            rack_controller=rack_controller, endpoint=endpoint)
        conn.save()
        return conn

    def make_Node(
            self, interface=False, hostname=None, domain=None, status=None,
            architecture="i386/generic", min_hwe_kernel=None,
            hwe_kernel=None, node_type=NODE_TYPE.MACHINE, updated=None,
            created=None, zone=None, networks=None, sortable_name=False,
            power_type=None, power_parameters=None, power_state=None,
            power_state_updated=undefined, disable_ipv4=None,
            with_boot_disk=True, vlan=None, fabric=None,
            bmc_connected_to=None, **kwargs):
        """Make a :class:`Node`.

        :param sortable_name: If `True`, use a that will sort consistently
            between different collation orders.  Use this when testing sorting
            by name, where the database and the python code may have different
            ideas about collation orders, especially when it comes to case
            differences.
        :param bmc_connected_to: Assign an IP address to the BMC for this node
            so this rack controller can control the power.
        :type bmc_connected_to: `:class:RackController`
        """
        # hostname=None is a valid value, hence the set_hostname trick.
        if hostname is None:
            hostname = self.make_string(20)
        if domain is None:
            domain = Domain.objects.get_default_domain()
        if sortable_name:
            hostname = hostname.lower()
        if status is None:
            status = NODE_STATUS.DEFAULT
        if zone is None:
            zone = self.make_Zone()
        if power_type is None:
            power_type = 'virsh'
        if power_parameters is None:
            power_parameters = {}
        if power_state is None:
            power_state = self.pick_enum(POWER_STATE)
        if power_state_updated is undefined:
            power_state_updated = (
                timezone.now() - timedelta(minutes=random.randint(0, 15)))
        if disable_ipv4 is None:
            disable_ipv4 = self.pick_bool()
        node = Node(
            hostname=hostname, status=status, architecture=architecture,
            min_hwe_kernel=min_hwe_kernel, hwe_kernel=hwe_kernel,
            node_type=node_type, zone=zone,
            power_state=power_state, power_state_updated=power_state_updated,
            disable_ipv4=disable_ipv4, domain=domain,
            **kwargs)
        node.power_type = power_type
        node.power_parameters = power_parameters
        self._save_node_unchecked(node)
        # We do not generate random networks by default because the limited
        # number of VLAN identifiers (4,094) makes it very likely to
        # encounter collisions.
        if networks is not None:
            node.networks.add(*networks)
        if interface:
            self.make_Interface(
                INTERFACE_TYPE.PHYSICAL, node=node, vlan=vlan, fabric=fabric)
        if node_type == NODE_TYPE.MACHINE and with_boot_disk:
            root_partition = self.make_Partition(node=node)
            acquired = node.status in ALLOCATED_NODE_STATUSES
            self.make_Filesystem(
                partition=root_partition, mount_point='/', acquired=acquired)

        # Setup the BMC connected to rack controller if a BMC is created.
        if bmc_connected_to is not None:
            if node.power_type != "virsh":
                raise Exception(
                    "bmc_connected_to requires that power_type set to 'virsh'")
            rack_interface = bmc_connected_to.get_boot_interface()
            if rack_interface is None:
                rack_interface = self.make_Interface(
                    INTERFACE_TYPE.PHYSICAL, node=bmc_connected_to)
            existing_static_ips = [
                ip_address
                for ip_address in rack_interface.ip_addresses.filter(
                    alloc_type__in=[
                        IPADDRESS_TYPE.AUTO,
                        IPADDRESS_TYPE.STICKY,
                    ], subnet__isnull=False, ip__isnull=False)
                if ip_address.ip
            ]
            if len(existing_static_ips) == 0:
                network = factory.make_ipv4_network()
                subnet = self.make_Subnet(
                    cidr=str(network.cidr), vlan=rack_interface.vlan)
                ip_address = self.make_StaticIPAddress(
                    alloc_type=IPADDRESS_TYPE.STICKY,
                    ip=self.pick_ip_in_Subnet(subnet),
                    subnet=subnet, interface=rack_interface)
            else:
                ip_address = existing_static_ips[0]
            bmc_ip_address = self.pick_ip_in_Subnet(ip_address.subnet)
            node.power_parameters = {
                "power_address": "qemu+ssh://user@%s/system" % bmc_ip_address
            }
            node.save()

        # Update the 'updated'/'created' fields with a call to 'update'
        # preventing a call to save() from overriding the values.
        if updated is not None:
            Node.objects.filter(id=node.id).update(updated=updated)
        if created is not None:
            Node.objects.filter(id=node.id).update(created=created)
        return reload_object(node)

    def make_RackController(self, last_image_sync=undefined, **kwargs):
        node = self.make_Node_with_Interface_on_Subnet(
            node_type=NODE_TYPE.RACK_CONTROLLER,
            with_dhcp_rack_primary=False, with_dhcp_rack_secondary=False,
            **kwargs)
        if last_image_sync is undefined:
            node.last_image_sync = (
                timezone.now() - timedelta(minutes=random.randint(1, 15)))
        else:
            node.last_image_sync = last_image_sync
        node.save()
        return typecast_node(node, RackController)

    def make_RegionRackController(self, *args, **kwargs):
        region_rack = self.make_RackController(*args, **kwargs)
        region_rack.node_type = NODE_TYPE.REGION_AND_RACK_CONTROLLER
        region_rack.save()
        return region_rack

    def make_BMC(
            self, power_type=None, power_parameters=None, ip_address=None,
            **kwargs):
        """Make a :class:`BMC`. """
        if power_type is None:
            power_type = 'manual'
        if power_parameters is None:
            power_parameters = {}
        bmc = BMC(
            power_type=power_type, power_parameters=power_parameters,
            ip_address=ip_address, **kwargs)
        bmc.save()
        return bmc

    def make_Domain(self, name=None, ttl=None, authoritative=True):
        if name is None:
            name = self.make_name('domain')
        domain = Domain(
            name=name, ttl=ttl,
            authoritative=authoritative)
        domain.save()
        return domain

    def pick_rrset(self, rrtype=None, rrdata=None, exclude=[]):
        while rrtype is None:
            rrtype = self.pick_choice((
                ('CNAME', "Canonical name"),
                ('MX', "Mail Exchanger"),
                ('NS', "Name Server"),
                # We don't autogenerate SRV, because of NAME.
                # ('SRV', "Service"),
                ('TXT', "Text"),
            ))
            if rrtype in exclude:
                rrtype = None
            # Force data appropriate to the (random) RRType.
            rrdata = None
        rrtype = rrtype.upper()
        if rrdata is None:
            if rrtype == 'CNAME' or rrtype == 'NS':
                rrdata = "%s" % self.make_name(rrtype.lower())
            elif rrtype == 'MX':
                rrdata = "%d %s" % (
                    random.randint(0, 65535), self.make_name('mx'))
            elif rrtype == 'SRV':
                raise ValueError("No automatic generation of SRV DNSData")
            elif rrtype == 'TXT':
                rrdata = self.make_name(size=random.randint(100, 65535))
            else:
                rrdata = self.make_name("dnsdata")
        return (rrtype, rrdata)

    def make_DNSData(self, dnsresource=None, rrtype=None,
                     rrdata=None, ttl=None, **kwargs):
        # If they didn't pass in an ip_addresses, suppress them.
        if 'ip_addresses' not in kwargs:
            kwargs['no_ip_addresses'] = True
            exclude = []
        else:
            exclude = ['CNAME']
        if rrtype is None or rrdata is None:
            if (dnsresource is not None and
                    dnsresource.ip_addresses.count() > 0):
                exclude = ['CNAME']
            (rrtype, rrdata) = self.pick_rrset(
                rrtype, rrdata, exclude=exclude)
        if dnsresource is None:
            dnsresource = self.make_DNSResource(**kwargs)
        dnsdata = DNSData(
            dnsresource=dnsresource,
            ttl=ttl,
            rrtype=rrtype,
            rrdata=rrdata)
        dnsdata.save()
        return dnsdata

    def make_DNSResource(self, domain=None, ip_addresses=None, name=None,
                         address_ttl=None, no_ip_addresses=False, **kwargs):
        if 'name' in kwargs:
            name = kwargs['name']
            del kwargs['name']
        if 'domain' in kwargs:
            domain = kwargs['domain']
            del kwargs['domain']
        if 'address_ttl' in kwargs:
            address_ttl = kwargs['address_ttl']
            del kwargs['address_ttl']
        if domain is None:
            domain = self.make_Domain()
        if name is None:
            name = self.make_name('label')
        if ip_addresses is None and not no_ip_addresses:
            ip_addresses = [self.make_StaticIPAddress(**kwargs)]
        dnsrr = DNSResource(
            name=name, address_ttl=address_ttl,
            domain=domain)
        dnsrr.save()
        if ip_addresses:
            dnsrr.ip_addresses = ip_addresses
            dnsrr.save()
        return dnsrr

    def make_NodeResult_for_commissioning(
            self, node=None, name=None, script_result=None, data=None):
        """Create a `NodeResult` as one would see from commissioning a node."""
        if node is None:
            node = self.make_Node()
        if name is None:
            name = "ncrname-" + self.make_string(92)
        if data is None:
            data = b"ncrdata-" + self.make_bytes()
        if script_result is None:
            script_result = random.randint(0, 10)
        ncr = NodeResult(
            node=node, name=name, script_result=script_result,
            result_type=RESULT_TYPE.COMMISSIONING, data=Bin(data))
        ncr.save()
        return ncr

    def make_NodeResult_for_installation(
            self, node=None, name=None, script_result=None, data=None):
        """Create a `NodeResult` as one would see from installing a node."""
        if node is None:
            node = self.make_Node()
        if name is None:
            name = "ncrname-" + self.make_string(92)
        if data is None:
            data = b"ncrdata-" + self.make_bytes()
        if script_result is None:
            script_result = random.randint(0, 10)
        ncr = NodeResult(
            node=node, name=name, script_result=script_result,
            result_type=RESULT_TYPE.INSTALLATION, data=Bin(data))
        ncr.save()
        return ncr

    def make_MAC(self):
        """Generate a random MAC address, in the form of a MAC object."""
        return MAC(self.make_mac_address())

    def make_Node_with_Interface_on_Subnet(
            self, interface_count=1, vlan=None, subnet=None,
            cidr=None, fabric=None, ifname=None, unmanaged=False,
            with_dhcp_rack_primary=True, with_dhcp_rack_secondary=False,
            primary_rack=None, secondary_rack=None,
            **kwargs):
        """Create a Node that has a Interface which is on a Subnet.

        :param interface_count: count of interfaces to add
        :param **kwargs: Additional parameters to pass to make_Node.
        """
        mac_address = None
        iftype = INTERFACE_TYPE.PHYSICAL
        if 'address' in kwargs:
            mac_address = kwargs['address']
            del kwargs['address']
        if 'iftype' in kwargs:
            iftype = kwargs['iftype']
            del kwargs['iftype']
        node = self.make_Node(fabric=fabric, **kwargs)
        if vlan is None and subnet is not None:
            vlan = subnet.vlan
        if vlan is None:
            if fabric is None:
                fabric = factory.make_Fabric()
            vlan = fabric.get_default_vlan()
            dhcp_on = with_dhcp_rack_primary or with_dhcp_rack_secondary
            vlan.dhcp_on = dhcp_on
            vlan.save()
        if subnet is None:
            subnet = self.make_Subnet(vlan=vlan, cidr=cidr)
        boot_interface = self.make_Interface(
            iftype, name=ifname, node=node, vlan=vlan,
            mac_address=mac_address)
        node.boot_interface = boot_interface
        node.save()

        self.make_StaticIPAddress(
            alloc_type=IPADDRESS_TYPE.DISCOVERED, ip="",
            subnet=subnet, interface=boot_interface)
        should_have_default_link_configuration = (
            node.status not in [
                NODE_STATUS.NEW,
                NODE_STATUS.COMMISSIONING,
                NODE_STATUS.FAILED_COMMISSIONING,
            ])
        if should_have_default_link_configuration:
            self.make_StaticIPAddress(
                alloc_type=IPADDRESS_TYPE.AUTO, ip="",
                subnet=subnet, interface=boot_interface)
        for _ in range(1, interface_count):
            interface = self.make_Interface(
                INTERFACE_TYPE.PHYSICAL, node=node, vlan=vlan)
            self.make_StaticIPAddress(
                alloc_type=IPADDRESS_TYPE.DISCOVERED, ip="",
                subnet=subnet, interface=interface)
            if should_have_default_link_configuration:
                self.make_StaticIPAddress(
                    alloc_type=IPADDRESS_TYPE.STICKY, ip="",
                    subnet=subnet, interface=interface)
        if with_dhcp_rack_primary:
            if primary_rack is None:
                if vlan.primary_rack is None:
                    primary_rack = self.make_RackController(
                        vlan=vlan, subnet=subnet)
                else:
                    primary_rack = vlan.primary_rack
            vlan.primary_rack = primary_rack
            vlan.save()
        if with_dhcp_rack_secondary:
            if secondary_rack is None:
                if vlan.secondary_rack is None:
                    secondary_rack = self.make_RackController(
                        vlan=vlan, subnet=subnet)
                else:
                    secondary_rack = vlan.secondary_rack
            vlan.secondary_rack = secondary_rack
            vlan.save()
        return reload_object(node)

    UNDEFINED = float('NaN')

    def _get_exclude_list(self, subnet):
        ip_addresses = [
            IPAddress(ip) for ip in StaticIPAddress.objects.filter(
                subnet=subnet).values_list('ip', flat=True)
            if ip is not None
        ]
        if subnet.gateway_ip is not None:
            ip_addresses.append(IPAddress(subnet.gateway_ip))
        return ip_addresses

    def make_StaticIPAddress(self, ip=UNDEFINED,
                             alloc_type=IPADDRESS_TYPE.AUTO, interface=None,
                             user=None, subnet=None, **kwargs):
        """Create and return a StaticIPAddress model object.

        If a non-None `interface` is passed, connect this IP address to the
        given interface.
        """
        if subnet is None:
            subnet = Subnet.objects.first()
        if subnet is None and alloc_type != IPADDRESS_TYPE.USER_RESERVED:
            subnet = self.make_Subnet()
        hostname = kwargs.pop('hostname', None)

        if ip is self.UNDEFINED:
            if not subnet and alloc_type == IPADDRESS_TYPE.USER_RESERVED:
                ip = self.make_ip_address()
            else:
                ip = self.pick_ip_in_network(
                    IPNetwork(subnet.cidr),
                    but_not=self._get_exclude_list(subnet))
        elif ip is None or ip == '':
            ip = ''

        ipaddress = StaticIPAddress(
            ip=ip, alloc_type=alloc_type, user=user, subnet=subnet, **kwargs)
        ipaddress.save()
        if interface is not None:
            interface.ip_addresses.add(ipaddress)
            interface.save()
        if hostname is not None:
            if not isinstance(hostname, (tuple, list)):
                hostname = [hostname]
            for name in hostname:
                if name.find('.') > 0:
                    name, domain = name.split('.', 1)
                    domain = Domain.objects.get(name=domain)
                else:
                    domain = None
                dnsrr, created = DNSResource.objects.get_or_create(
                    name=name, domain=domain)
                ipaddress.dnsresource_set.add(dnsrr)
        return reload_object(ipaddress)

    def make_email(self):
        return '%s@example.com' % self.make_string(10)

    def make_User(self, username=None, password='test', email=None):
        if username is None:
            username = self.make_username()
        if email is None:
            email = self.make_email()
        return User.objects.create_user(
            username=username, password=password, email=email)

    def make_SSHKey(self, user, key_string=None):
        if key_string is None:
            key_string = get_data('data/test_rsa0.pub')
        key = SSHKey(key=key_string, user=user)
        key.save()
        return key

    def make_SSLKey(self, user, key_string=None):
        if key_string is None:
            key_string = get_data('data/test_x509_0.pem')
        key = SSLKey(key=key_string, user=user)
        key.save()
        return key

    def make_Space(self, name=None):
        space = Space(name=name)
        space.save()
        return space

    def make_Subnet(self, name=None, vlan=None, space=None, cidr=None,
                    gateway_ip=None, dns_servers=None, host_bits=None,
                    fabric=None, vid=None, dhcp_on=False,
                    rdns_mode=RDNS_MODE.DEFAULT, allow_proxy=True):
        if name is None:
            name = factory.make_name('name')
        if vlan is None:
            vlan = factory.make_VLAN(fabric=fabric, vid=vid, dhcp_on=dhcp_on)
        if space is None:
            space = factory.make_Space()
        network = None
        if cidr is None:
            network = factory.make_ip4_or_6_network(host_bits=host_bits)
            cidr = str(network.cidr)
        if gateway_ip is None:
            network = IPNetwork(cidr) if network is None else network
            gateway_ip = inet_ntop(network.first + 1)
        if dns_servers is None:
            dns_servers = [
                self.make_ip_address() for _ in range(random.randint(1, 3))]
        subnet = Subnet(
            name=name, vlan=vlan, cidr=cidr, gateway_ip=gateway_ip,
            space=space, dns_servers=dns_servers, rdns_mode=rdns_mode,
            allow_proxy=allow_proxy)
        subnet.save()
        return subnet

    def pick_ip_in_Subnet(self, subnet, but_not=[]):
        # Exclude all addresses currently in use
        for iprange in subnet.get_ipranges_in_use():
            for i in range(iprange.num_addresses):
                but_not.append(IPAddress(iprange.first + i).format())
        return self.pick_ip_in_network(IPNetwork(subnet.cidr), but_not=but_not)

    def pick_ip_in_IPRange(self, ip_range, but_not=[]):
        if but_not is None:
            but_not = []
        netaddr_range = ip_range.netaddr_iprange
        first = netaddr_range.first
        last = netaddr_range.last
        but_not = [IPAddress(but) for but in but_not if but is not None]
        for _ in range(100):
            address = IPAddress(random.randint(first, last))
            if address not in but_not:
                return str(address)
        raise TooManyRandomRetries(
            "Could not find available IP in IPRange")

    def make_FanNetwork(self, name=None, underlay=None, overlay=None,
                        dhcp=None, host_reserve=1, bridge=None, off=None):
        if name is None:
            name = self.make_name('fan network')
        if underlay is None:
            underlay = factory.make_ipv4_network(slash=16)
        if overlay is None:
            overlay = factory.make_ipv4_network(
                slash=8, disjoint_from=[underlay])
        fannetwork = FanNetwork(
            name=name, underlay=underlay, overlay=overlay, dhcp=dhcp,
            host_reserve=host_reserve, bridge=bridge, off=off)
        fannetwork.save()
        return fannetwork

    def make_Fabric(self, name=None, class_type=None):
        fabric = Fabric(name=name, class_type=class_type)
        fabric.save()
        return fabric

    def make_Service(self, node, name=None):
        if name is None:
            name = self.make_name('name')
        service = Service(node=node, name=name)
        service.save()
        return service

    def _get_available_vid(self, fabric):
        """Return a free vid in the given Fabric."""
        taken_vids = set(fabric.vlan_set.all().values_list('vid', flat=True))
        for attempt in range(1000):
            vid = random.randint(1, 4094)
            if vid not in taken_vids:
                return vid
        raise maastesting.factory.TooManyRandomRetries(
            "Could not generate vid in fabric %s" % fabric)

    def make_VLAN(
            self, name=None, vid=None, fabric=None, dhcp_on=False,
            primary_rack=None, secondary_rack=None):
        assert vid != 0, "VID=0 VLANs are auto-created"
        if fabric is None:
            fabric = Fabric.objects.get_default_fabric()
        if vid is None:
            # Don't create the vid=0 VLAN, it's auto-created.
            vid = self._get_available_vid(fabric)
        vlan = VLAN(
            name=name, vid=vid, fabric=fabric, dhcp_on=dhcp_on,
            primary_rack=primary_rack, secondary_rack=secondary_rack)
        vlan.save()
        return vlan

    def make_Interface(
            self, iftype=INTERFACE_TYPE.PHYSICAL, node=None, mac_address=None,
            vlan=None, parents=None, name=None, cluster_interface=None,
            ip=None, enabled=True, fabric=None):
        if name is None:
            if iftype in (INTERFACE_TYPE.PHYSICAL, INTERFACE_TYPE.UNKNOWN):
                name = self.make_name('eth')
            elif iftype == INTERFACE_TYPE.ALIAS:
                name = self.make_name('eth', sep=':')
            elif iftype == INTERFACE_TYPE.BOND:
                name = self.make_name('bond')
            elif iftype == INTERFACE_TYPE.BRIDGE:
                name = self.make_name('br')
            elif iftype == INTERFACE_TYPE.UNKNOWN:
                name = self.make_name('eth')
            elif iftype == INTERFACE_TYPE.VLAN:
                # This will be determined by the VLAN's VID.
                name = None
        if iftype is None:
            iftype = INTERFACE_TYPE.PHYSICAL
        if vlan is None:
            if fabric is not None:
                if iftype == INTERFACE_TYPE.VLAN:
                    vlan = self.make_VLAN(fabric=fabric)
                else:
                    vlan = fabric.get_default_vlan()
            else:
                if iftype == INTERFACE_TYPE.VLAN and parents:
                    vlan = self.make_VLAN(fabric=parents[0].vlan.fabric)
                elif iftype == INTERFACE_TYPE.BOND and parents:
                    vlan = parents[0].vlan
                else:
                    fabric = self.make_Fabric()
                    vlan = fabric.get_default_vlan()
        if (mac_address is None and
                iftype in [
                    INTERFACE_TYPE.PHYSICAL,
                    INTERFACE_TYPE.BOND,
                    INTERFACE_TYPE.BRIDGE,
                    INTERFACE_TYPE.UNKNOWN]):
            mac_address = self.make_MAC()
        if node is None and iftype == INTERFACE_TYPE.PHYSICAL:
            node = self.make_Node()
        interface = Interface(
            node=node, mac_address=mac_address, type=iftype,
            name=name, vlan=vlan, enabled=enabled)
        interface.save()
        if cluster_interface is not None:
            sip = StaticIPAddress.objects.create(
                ip=ip,
                alloc_type=IPADDRESS_TYPE.DHCP,
                subnet=cluster_interface.subnet)
            interface.ip_addresses.add(sip)
        if parents:
            for parent in parents:
                InterfaceRelationship(child=interface, parent=parent).save()
        interface.save()
        return reload_object(interface)

    def make_IPRange(
            self, subnet=None, start_ip=None, end_ip=None, comment=None,
            user=None, type=IPRANGE_TYPE.DYNAMIC):
        if subnet is None and start_ip is None and end_ip is None:
            subnet = self.make_ipv4_Subnet_with_IPRanges()
            return subnet.get_dynamic_ranges().first()
        # If any of these values are provided, they must all be provided.
        assert subnet is not None
        assert start_ip is not None
        assert end_ip is not None
        iprange = IPRange(
            subnet=subnet, start_ip=start_ip, end_ip=end_ip, type=type,
            comment=comment, user=user)
        iprange.save()
        return iprange

    def make_ipv4_Subnet_with_IPRanges(
            self, cidr=None, unmanaged=False, with_dynamic_range=True,
            with_static_range=True, dns_servers=None, with_router=True,
            **kwargs):
        if cidr is not None:
            network = IPNetwork(cidr)
            slash = network.prefixlen
        else:
            slash = random.choice(
                [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28])
            network = factory.make_ipv4_network(slash=slash)
        host_bits = 32 - slash
        # Use at most 25% of the subnet per range type.
        range_size = 2 ** (host_bits - 2)
        if with_router:
            router_address = IPAddress(network.first + 1)
        else:
            router_address = ''
        if dns_servers is None:
            dns_servers = random.choice([
                [], ['8.8.8.8', '8.8.4.4'], [str(IPAddress(network.last - 1))]
            ])
        subnet = self.make_Subnet(
            cidr=str(network), gateway_ip=str(router_address),
            dns_servers=dns_servers, **kwargs)
        # Create a "dynamic range" for this Subnet.
        if with_dynamic_range:
            if unmanaged:
                subnet.vlan.dhcp_on = False
                subnet.vlan.save()
            else:
                subnet.vlan.dhcp_on = True
                subnet.vlan.save()
            self.make_IPRange(
                subnet, type=IPRANGE_TYPE.DYNAMIC,
                start_ip=str(IPAddress(network.first + 2)),
                end_ip=str(IPAddress(network.first + range_size + 2)))
        # Create a "static range" for this Subnet.
        if not with_static_range:
            self.make_IPRange(
                subnet, type=IPRANGE_TYPE.RESERVED,
                start_ip=str(IPAddress(network.last - range_size - 2)),
                end_ip=str(IPAddress(network.last - 2)))
        return reload_object(subnet)

    def make_managed_ipv6_Subnet(self, cidr=None, dhcp=True, **kwargs):
        if cidr is not None:
            network = IPNetwork(cidr)
        else:
            network = factory.make_ipv6_network(slash=64)
        router_address = IPAddress(network.first + 1)
        dns_servers = random.choice([
            [], ['8.8.8.8', '8.8.4.4'], [str(IPAddress(network.last - 1))]])
        subnet = self.make_Subnet(
            cidr=str(network), gateway_ip=str(router_address),
            dns_servers=dns_servers, **kwargs)
        if dhcp:
            subnet.vlan.dhcp_on = True
            subnet.vlan.save()
        else:
            subnet.vlan.dhcp_on = False
            subnet.vlan.save()
        return subnet

    def make_managed_Subnet(self, *args, **kwargs):
        ipv6 = random.choice([True, False])
        if ipv6:
            return self.make_managed_ipv6_Subnet()
        else:
            return self.make_ipv4_Subnet_with_IPRanges()

    def make_Tag(self, name=None, definition=None, comment='',
                 kernel_opts=None, created=None, updated=None):
        if name is None:
            name = self.make_name('tag')
        if definition is None:
            # Is there a 'node' in this xml?
            definition = '//node'
        tag = Tag(
            name=name, definition=definition, comment=comment,
            kernel_opts=kernel_opts)
        tag.save()
        # Update the 'updated'/'created' fields with a call to 'update'
        # preventing a call to save() from overriding the values.
        if updated is not None:
            Tag.objects.filter(id=tag.id).update(updated=updated)
        if created is not None:
            Tag.objects.filter(id=tag.id).update(created=created)
        return reload_object(tag)

    def make_user_with_keys(self, n_keys=2, user=None, **kwargs):
        """Create a user with n `SSHKey`.  If user is not None, use this user
        instead of creating one.

        Additional keyword arguments are passed to `make_user()`.
        """
        if n_keys > MAX_PUBLIC_KEYS:
            raise RuntimeError(
                "Cannot create more than %d public keys.  If you need more: "
                "add more keys in src/maasserver/tests/data/."
                % MAX_PUBLIC_KEYS)
        if user is None:
            user = self.make_User(**kwargs)
        keys = []
        for i in range(n_keys):
            key_string = get_data('data/test_rsa%d.pub' % i)
            key = SSHKey(user=user, key=key_string)
            key.save()
            keys.append(key)
        return user, keys

    def make_user_with_ssl_keys(self, n_keys=2, user=None, **kwargs):
        """Create a user with n `SSLKey`.

        :param n_keys: Number of keys to add to user.
        :param user: User to add keys to. If user is None, then user is made
            with make_user. Additional keyword arguments are passed to
            `make_user()`.
        """
        if n_keys > MAX_PUBLIC_KEYS:
            raise RuntimeError(
                "Cannot create more than %d public keys.  If you need more: "
                "add more keys in src/maasserver/tests/data/."
                % MAX_PUBLIC_KEYS)
        if user is None:
            user = self.make_User(**kwargs)
        keys = []
        for i in range(n_keys):
            key_string = get_data('data/test_x509_%d.pem' % i)
            key = SSLKey(user=user, key=key_string)
            key.save()
            keys.append(key)
        return user, keys

    def make_admin(self, username=None, password='test', email=None):
        if username is None:
            username = self.make_username()
        if email is None:
            email = self.make_email()
        return User.objects.create_superuser(
            username, password=password, email=email)

    def make_FileStorage(self, filename=None, content=None, owner=None):
        fake_file = self.make_file_upload(filename, content)
        return FileStorage.objects.save_file(fake_file.name, fake_file, owner)

    def make_oauth_header(self, missing_param=None, **kwargs):
        """Fake an OAuth authorization header.

        This will use arbitrary values.  Pass as keyword arguments any
        header items that you wish to override.
        :param missing_param: Optional parameter name.  This parameter will
            be omitted from the OAuth header.  This is used to create bogus
            OAuth headers to make sure the code deals properly with them.
        """
        items = {
            'realm': self.make_string(),
            'oauth_nonce': random.randint(0, 99999),
            'oauth_timestamp': time.time(),
            'oauth_consumer_key': self.make_string(18),
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_version': '1.0',
            'oauth_token': self.make_string(18),
            'oauth_signature': "%%26%s" % self.make_string(32),
        }
        items.update(kwargs)
        if missing_param is not None:
            del items[missing_param]
        return "OAuth " + ", ".join([
            '%s="%s"' % (key, value) for key, value in items.items()])

    def make_CommissioningScript(self, name=None, content=None):
        if name is None:
            name = self.make_name('script')
        if content is None:
            content = b'content:' + self.make_string().encode(
                settings.DEFAULT_CHARSET)
        return CommissioningScript.objects.create(
            name=name, content=Bin(content))

    def make_Zone(self, name=None, description=None, nodes=None,
                  sortable_name=False):
        """Create a physical `Zone`.

        :param sortable_name: If `True`, use a that will sort consistently
            between different collation orders.  Use this when testing sorting
            by name, where the database and the python code may have different
            ideas about collation orders, especially when it comes to case
            differences.
        """
        if name is None:
            name = self.make_name('zone')
        if sortable_name:
            name = name.lower()
        if description is None:
            description = self.make_string()
        zone = Zone(name=name, description=description)
        zone.save()
        if nodes is not None:
            zone.node_set.add(*nodes)
        return zone

    make_zone = make_Zone

    def make_BootSource(self, url=None, keyring_filename=None,
                        keyring_data=None):
        """Create a new `BootSource`."""
        if url is None:
            url = "http://%s.com" % self.make_name('source-url')
        # Only set _one_ of keyring_filename and keyring_data.
        if keyring_filename is None and keyring_data is None:
            keyring_filename = self.make_name("keyring")
        boot_source = BootSource(
            url=url,
            keyring_filename=(
                "" if keyring_filename is None else keyring_filename),
            keyring_data=(
                b"" if keyring_data is None else keyring_data),
        )
        boot_source.save()
        return boot_source

    def make_BootSourceCache(self, boot_source=None, os=None, arch=None,
                             subarch=None, release=None, label=None):
        """Create a new `BootSourceCache`."""
        if boot_source is None:
            boot_source = self.make_BootSource()
        if os is None:
            os = factory.make_name('os')
        if arch is None:
            arch = factory.make_name('arch')
        if subarch is None:
            subarch = factory.make_name('subarch')
        if release is None:
            release = factory.make_name('release')
        if label is None:
            label = factory.make_name('label')
        return BootSourceCache.objects.create(
            boot_source=boot_source, os=os, arch=arch,
            subarch=subarch, release=release, label=label)

    def make_many_BootSourceCaches(self, number, **kwargs):
        caches = list()
        for _ in range(number):
            caches.append(self.make_BootSourceCache(**kwargs))
        return caches

    def make_BootSourceSelection(self, boot_source=None, os=None,
                                 release=None, arches=None, subarches=None,
                                 labels=None):
        """Create a `BootSourceSelection`."""
        if boot_source is None:
            boot_source = self.make_BootSource()
        if os is None:
            os = self.make_name('os')
        if release is None:
            release = self.make_name('release')
        if arches is None:
            arch_count = random.randint(1, 10)
            arches = [self.make_name("arch") for _ in range(arch_count)]
        if subarches is None:
            subarch_count = random.randint(1, 10)
            subarches = [
                self.make_name("subarch")
                for _ in range(subarch_count)
                ]
        if labels is None:
            label_count = random.randint(1, 10)
            labels = [self.make_name("label") for _ in range(label_count)]
        boot_source_selection = BootSourceSelection(
            boot_source=boot_source, release=release, arches=arches,
            subarches=subarches, labels=labels)
        boot_source_selection.save()
        return boot_source_selection

    def make_LicenseKey(self, osystem=None, distro_series=None,
                        license_key=None):
        if osystem is None:
            osystem = factory.make_name('osystem')
        if distro_series is None:
            distro_series = factory.make_name('distro_series')
        if license_key is None:
            license_key = factory.make_name('key')
        return LicenseKey.objects.create(
            osystem=osystem,
            distro_series=distro_series,
            license_key=license_key)

    def make_EventType(self, name=None, level=None, description=None):
        if name is None:
            name = self.make_name('name', size=20)
        if description is None:
            description = factory.make_name('description')
        if level is None:
            level = random.choice([
                logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG])
        return EventType.objects.create(
            name=name, description=description, level=level)

    def make_Event(self, node=None, type=None, action=None, description=None):
        if node is None:
            node = self.make_Node()
        if type is None:
            type = self.make_EventType()
        if action is None:
            action = self.make_name('action')
        if description is None:
            description = self.make_name('desc')
        return Event.objects.create(
            node=node, type=type, action=action, description=description)

    @typed
    def make_LargeFile(self, content: bytes=None, size=512):
        """Create `LargeFile`.

        :param content: Data to store in large file object.
        :param size: Size of `content`. If `content` is None
            then it will be a random string of this size. If content is
            provided and `size` is not the same length, then it will
            be an inprogress file.
        """
        if content is None:
            content = factory.make_bytes(size=size)
        sha256 = hashlib.sha256()
        sha256.update(content)
        sha256 = sha256.hexdigest()
        largeobject = LargeObjectFile()
        with largeobject.open('wb') as stream:
            stream.write(content)
        return LargeFile.objects.create(
            sha256=sha256, total_size=size, content=largeobject)

    def make_BootResource(self, rtype=None, name=None, architecture=None,
                          extra=None, kflavor=None):
        if rtype is None:
            rtype = self.pick_enum(BOOT_RESOURCE_TYPE)
        if name is None:
            if rtype == BOOT_RESOURCE_TYPE.UPLOADED:
                name = self.make_name('name')
            else:
                os = self.make_name('os')
                series = self.make_name('series')
                name = '%s/%s' % (os, series)
        if architecture is None:
            arch = self.make_name('arch')
            subarch = self.make_name('subarch')
            architecture = '%s/%s' % (arch, subarch)
        if extra is None:
            extra = {
                self.make_name('key'): self.make_name('value')
                for _ in range(3)
                }
        if kflavor is None:
            extra['kflavor'] = 'generic'
        else:
            extra['kflavor'] = kflavor
        return BootResource.objects.create(
            rtype=rtype, name=name, architecture=architecture, extra=extra)

    def make_BootResourceSet(self, resource, version=None, label=None):
        if version is None:
            version = self.make_name('version')
        if label is None:
            label = self.make_name('label')
        return BootResourceSet.objects.create(
            resource=resource, version=version, label=label)

    def make_BootResourceFile(self, resource_set, largefile, filename=None,
                              filetype=None, extra=None):
        if filename is None:
            filename = self.make_name('name')
        if filetype is None:
            filetype = self.pick_enum(BOOT_RESOURCE_FILE_TYPE)
        if extra is None:
            extra = {
                self.make_name('key'): self.make_name('value')
                for _ in range(3)
                }
        return BootResourceFile.objects.create(
            resource_set=resource_set, largefile=largefile, filename=filename,
            filetype=filetype, extra=extra)

    def make_boot_resource_file_with_content(
            self, resource_set, filename=None, filetype=None, extra=None,
            content=None, size=512):
        largefile = self.make_LargeFile(content=content, size=size)
        return self.make_BootResourceFile(
            resource_set, largefile, filename=filename, filetype=filetype,
            extra=extra)

    def make_usable_boot_resource(
            self, rtype=None, name=None, architecture=None,
            extra=None, version=None, label=None, kflavor=None):
        resource = self.make_BootResource(
            rtype=rtype, name=name, architecture=architecture, extra=extra,
            kflavor=kflavor)
        resource_set = self.make_BootResourceSet(
            resource, version=version, label=label)
        filetypes = set(COMMISSIONABLE_SET)
        filetypes.add(random.choice(XINSTALL_TYPES))
        for filetype in filetypes:
            # We set the filename to the same value as filetype, as in most
            # cases this will always be true. The simplestreams content from
            # maas.io, is formatted this way.
            self.make_boot_resource_file_with_content(
                resource_set, filename=filetype, filetype=filetype)
        return resource

    def make_BlockDevice(
            self, node=None, name=None, id_path=None, size=None,
            block_size=None, tags=None):
        if node is None:
            node = self.make_Node()
        if name is None:
            name = self.make_name('name')
        if id_path is None:
            id_path = '/dev/disk/by-id/id_%s' % name
        if block_size is None:
            block_size = random.choice([512, 1024, 4096])
        if size is None:
            size = round_size_to_nearest_block(
                random.randint(
                    MIN_BLOCK_DEVICE_SIZE * 4,
                    MIN_BLOCK_DEVICE_SIZE * 1024),
                block_size)
        if tags is None:
            tags = [self.make_name('tag') for _ in range(3)]
        return BlockDevice.objects.create(
            node=node, name=name, size=size, block_size=block_size,
            tags=tags)

    def make_PhysicalBlockDevice(
            self, node=None, name=None, size=None, block_size=None,
            tags=None, model=None, serial=None, id_path=None):
        if node is None:
            node = self.make_Node()
        if name is None:
            name = self.make_name('name')
        if block_size is None:
            block_size = random.choice([512, 1024, 4096])
        if size is None:
            size = round_size_to_nearest_block(
                random.randint(
                    MIN_BLOCK_DEVICE_SIZE * 4, MIN_BLOCK_DEVICE_SIZE * 1024),
                block_size)
        if tags is None:
            tags = [self.make_name('tag') for _ in range(3)]
        if id_path is None:
            if model is None:
                model = self.make_name('model')
            if serial is None:
                serial = self.make_name('serial')
        else:
            model = ""
            serial = ""
        return PhysicalBlockDevice.objects.create(
            node=node, name=name, size=size, block_size=block_size,
            tags=tags, model=model, serial=serial, id_path=id_path)

    def make_PartitionTable(
            self, table_type=None, block_device=None, node=None,
            block_device_size=None):
        if block_device is None:
            if node is None:
                if table_type == PARTITION_TABLE_TYPE.GPT:
                    node = factory.make_Node(bios_boot_method="uefi")
                else:
                    node = factory.make_Node()
            block_device = self.make_PhysicalBlockDevice(
                node=node, size=block_device_size)
        return PartitionTable.objects.create(
            table_type=table_type, block_device=block_device)

    def make_Partition(
            self, partition_table=None, uuid=None, size=None, bootable=None,
            node=None, block_device_size=None):
        if partition_table is None:
            partition_table = self.make_PartitionTable(
                node=node, block_device_size=block_device_size)
        if size is None:
            available_size = partition_table.get_available_size() // 2
            if available_size < MIN_PARTITION_SIZE:
                raise ValueError(
                    "Cannot make another partition on partition_table not "
                    "enough free space.")
            size = random.randint(MIN_PARTITION_SIZE, available_size)
        if bootable is None:
            bootable = random.choice([True, False])
        return Partition.objects.create(
            partition_table=partition_table, uuid=uuid,
            size=size, bootable=bootable)

    def pick_filesystem_type(self, but_not=()):
        """Pick a filesystem that requires block storage and a mount point."""
        # XXX: Temporarily exclude swap, ramfs, and tmpfs from the random
        # choice. Swap doesn't use a mount point, and ramfs/tmpfs don't use
        # storage, and this can surprise some tests. This is obviously not a
        # tenable position longer term.
        but_not = {
            FILESYSTEM_TYPE.SWAP, FILESYSTEM_TYPE.RAMFS,
            FILESYSTEM_TYPE.TMPFS}.union(but_not)
        return factory.pick_choice(
            FILESYSTEM_FORMAT_TYPE_CHOICES, but_not=but_not)

    def pick_any_filesystem_type(self, but_not=()):
        """Pick any filesystem type, including swap, ramfs, or tmpfs."""
        return factory.pick_choice(
            FILESYSTEM_FORMAT_TYPE_CHOICES, but_not=but_not)

    def make_Filesystem(
            self, uuid=None, fstype=None, partition=None, block_device=None,
            node=None, filesystem_group=None, label=None, create_params=None,
            mount_point=None, mount_options=undefined, block_device_size=None,
            acquired=False):
        if fstype is None:
            if node is None:
                # Pick a filesystem that requires storage and a mount point.
                fstype = self.pick_filesystem_type()
            else:
                # Pick a filesystem that does not require storage, like tmpfs.
                fstype = self.pick_any_filesystem_type(
                    but_not=Filesystem.TYPES_REQUIRING_STORAGE)
        if fstype in Filesystem.TYPES_REQUIRING_STORAGE:
            if partition is None and block_device is None:
                if self.pick_bool():
                    partition = self.make_Partition()
                else:
                    block_device = self.make_PhysicalBlockDevice(
                        size=block_device_size)
        else:
            if node is None:
                node = self.make_Node()
            if mount_point is None:
                mount_point = factory.make_absolute_path()
        if mount_options is undefined:
            mount_options = self.make_name("mount-options")
        return Filesystem.objects.create(
            uuid=uuid, fstype=fstype, partition=partition,
            block_device=block_device, node=node,
            filesystem_group=filesystem_group, label=label,
            create_params=create_params, mount_point=mount_point,
            mount_options=mount_options, acquired=acquired)

    def make_CacheSet(self, block_device=None, partition=None, node=None):
        if node is None:
            node = self.make_Node()
        if partition is None and block_device is None:
            if self.pick_bool():
                partition = self.make_Partition(node=node)
            else:
                block_device = self.make_PhysicalBlockDevice(node=node)
        if block_device is not None:
            return CacheSet.objects.get_or_create_cache_set_for_block_device(
                block_device)
        else:
            return CacheSet.objects.get_or_create_cache_set_for_partition(
                partition)

    def make_FilesystemGroup(
            self, uuid=None, group_type=None, name=None, create_params=None,
            filesystems=None, node=None, block_device_size=None,
            cache_mode=None, num_lvm_devices=4, cache_set=None):
        if group_type is None:
            group_type = self.pick_enum(FILESYSTEM_GROUP_TYPE)
        if group_type == FILESYSTEM_GROUP_TYPE.BCACHE:
            if cache_mode is None:
                cache_mode = self.pick_enum(CACHE_MODE_TYPE)
            if cache_set is None:
                cache_set = self.make_CacheSet(node=node)
        group = FilesystemGroup(
            uuid=uuid, group_type=group_type, name=name, cache_mode=cache_mode,
            create_params=create_params, cache_set=cache_set)
        group.save()
        if filesystems is None:
            if node is None:
                node = self.make_Node()
            if node.physicalblockdevice_set.count() == 0:
                # Add the boot disk and leave it as is.
                self.make_PhysicalBlockDevice(node=node)
            if group_type == FILESYSTEM_GROUP_TYPE.LVM_VG:
                for _ in range(num_lvm_devices):
                    block_device = self.make_PhysicalBlockDevice(
                        node, size=block_device_size)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.LVM_PV,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.RAID_0:
                for _ in range(2):
                    block_device = self.make_PhysicalBlockDevice(node)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.RAID,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.RAID_1:
                for _ in range(2):
                    block_device = self.make_PhysicalBlockDevice(node)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.RAID,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.RAID_5:
                for _ in range(3):
                    block_device = self.make_PhysicalBlockDevice(node)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.RAID,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
                spare_block_device = self.make_PhysicalBlockDevice(node)
                spare_filesystem = self.make_Filesystem(
                    fstype=FILESYSTEM_TYPE.RAID_SPARE,
                    block_device=spare_block_device)
                group.filesystems.add(spare_filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.RAID_6:
                for _ in range(4):
                    block_device = self.make_PhysicalBlockDevice(node)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.RAID,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
                spare_block_device = self.make_PhysicalBlockDevice(node)
                spare_filesystem = self.make_Filesystem(
                    fstype=FILESYSTEM_TYPE.RAID_SPARE,
                    block_device=spare_block_device)
                group.filesystems.add(spare_filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.RAID_10:
                for _ in range(4):
                    block_device = self.make_PhysicalBlockDevice(node)
                    filesystem = self.make_Filesystem(
                        fstype=FILESYSTEM_TYPE.RAID,
                        block_device=block_device)
                    group.filesystems.add(filesystem)
                spare_block_device = self.make_PhysicalBlockDevice(node)
                spare_filesystem = self.make_Filesystem(
                    fstype=FILESYSTEM_TYPE.RAID_SPARE,
                    block_device=spare_block_device)
                group.filesystems.add(spare_filesystem)
            elif group_type == FILESYSTEM_GROUP_TYPE.BCACHE:
                backing_block_device = self.make_PhysicalBlockDevice(node)
                backing_filesystem = self.make_Filesystem(
                    fstype=FILESYSTEM_TYPE.BCACHE_BACKING,
                    block_device=backing_block_device)
                group.filesystems.add(backing_filesystem)
        else:
            for filesystem in filesystems:
                group.filesystems.add(filesystem)
        # Save again to make sure that the added filesystems are correct.
        group.save()
        return group

    def make_VolumeGroup(self, *args, **kwargs):
        if len(args) > 1:
            args[1] = FILESYSTEM_GROUP_TYPE.LVM_VG
        else:
            kwargs['group_type'] = FILESYSTEM_GROUP_TYPE.LVM_VG
        filesystem_group = self.make_FilesystemGroup(*args, **kwargs)
        return VolumeGroup.objects.get(id=filesystem_group.id)

    def make_VirtualBlockDevice(
            self, name=None, size=None, block_size=None,
            tags=None, uuid=None, filesystem_group=None, node=None):
        if node is None:
            node = factory.make_Node()
        if block_size is None:
            block_size = random.choice([512, 1024, 4096])
        if filesystem_group is None:
            filesystem_group = self.make_FilesystemGroup(
                node=node,
                group_type=FILESYSTEM_GROUP_TYPE.LVM_VG,
                block_device_size=size,
                num_lvm_devices=2)
        if size is None:
            available_size = filesystem_group.get_lvm_free_space()
            if available_size < MIN_BLOCK_DEVICE_SIZE:
                raise ValueError(
                    "Cannot make a virtual block device in filesystem_group; "
                    "not enough space.")
            size = round_size_to_nearest_block(
                random.randint(
                    MIN_BLOCK_DEVICE_SIZE, available_size),
                block_size)
        if tags is None:
            tags = [self.make_name("tag") for _ in range(3)]

        elif not filesystem_group.is_lvm():
            raise RuntimeError(
                "make_VirtualBlockDevice should only be used with "
                "filesystem_group that has a group_type of LVM_VG.  "
                "If you need a VirtualBlockDevice that is for another type "
                "use make_FilesystemGroup which will create a "
                "VirtualBlockDevice automatically.")
        if name is None:
            name = self.make_name("lv")
        if size is None:
            size = random.randint(1, filesystem_group.get_size())
        if block_size is None:
            block_size = random.choice([512, 1024, 4096])
        return VirtualBlockDevice.objects.create(
            name=name, size=size, block_size=block_size,
            tags=tags, uuid=uuid, filesystem_group=filesystem_group)

    def make_DHCPSnippet(
            self, name=None, value=None, description=None, enabled=True,
            node=None, subnet=None):
        if name is None:
            name = self.make_name("dhcp_snippet")
        if value is None:
            value = VersionedTextFile.objects.create(data=self.make_string())
        if description is None:
            description = self.make_string()
        return DHCPSnippet.objects.create(
            name=name, value=value, description=description, enabled=enabled,
            node=node, subnet=subnet)


# Create factory singleton.
factory = Factory()
