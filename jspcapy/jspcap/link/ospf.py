#!/usr/bin/python3
# -*- coding: utf-8 -*-


# Open Shortest Path First
# Analyser for OSPF header


from .link import Link
from ..protocol import Info


# OSPF Packet Types
TYPE = {
    1 : 'Hello',
    2 : 'Database Description',
    3 : 'Link State Request',
    4 : 'Link State Update',
    5 : 'Link State Acknowledgment',
}


# Authentication Types
AUTH = {
    0 : 'Null Authentication',
    1 : 'Simple Password',
    2 : 'Cryptographic Authentication',
}


class OSPF(Link):

    __all__ = ['name', 'info', 'length', 'layer', 'type', 'protochain']

    ##########################################################################
    # Properties.
    ##########################################################################

    @property
    def name(self):
        return 'Open Shortest Path First'

    @property
    def info(self):
        return self._info

    @property
    def length(self):
        return 24

    @property
    def layer(self):
        return self.__layer__

    @property
    def type(self):
        return self._info.type

    ##########################################################################
    # Data models.
    ##########################################################################

    def __init__(self, _file):
        self._file = _file
        self._info = Info(self.read_ospf())

    def __len__(self):
        return 24

    def __length_hint__(self):
        return 24

    ##########################################################################
    # Utilities.
    ##########################################################################

    def read_ospf(self):
        """Read Open Shortest Path First.

        Structure of OSPF header [RFC 2328]:

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |   Version #   |     Type      |         Packet length         |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                          Router ID                            |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                           Area ID                             |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |           Checksum            |             AuType            |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                       Authentication                          |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                       Authentication                          |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            Octets          Bits          Name                Discription
              0              0          ospf.version      Version #
              1              8          ospf.type         Type (0/1)
              2              16         ospf.len          Packet Length (header includes)
              4              32         ospf.router_id    Router ID
              8              64         ospf.area_id      Area ID
              12             96         ospf.chksum       Checksum
              14             112        ospf.autype       AuType
              16             128        ospf.auth         Authentication

        """
        _vers = self._read_unpack(1)
        _type = self._read_unpack(1)
        _tlen = self._read_unpack(2)
        _rtid = self._read_id_numbers()
        _area = self._read_id_numbers()
        _csum = self._read_fileng(2)
        _autp = self._read_unpack(2)

        ospf = dict(
            version = _vers,
            type = TYPE.get(_type),
            len = _tlen,
            router_id = _rtid,
            area_id = _area,
            chksum = _csum,
            autype = AUTH.get(_autp) or 'Reserved',
        )

        if _autp == 2:
            ospf['auth'] = self._read_encrypt_auth()
        else:
            ospf['auth'] = self._read_fileng(8)

        return self._read_next_layer(ospf)

    def _read_id_numbers(self):
        _byte = self._read_fileng(4)
        _addr = '.'.join([str(_) for _ in _byte])
        return _addr

    def _read_encrypt_auth(self):
        """Read Authentication field when Cryptographic Authentication is employed.

        Structure of Cryptographic Authentication [RFC 2328]:

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |              0                |    Key ID     | Auth Data Len |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                 Cryptographic sequence number                 |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            Octets          Bits          Name                Discription
              0              0          ospf.auth.resv    Reserved (must be zero)
              2              16         ospf.auth.key_id  Key ID
              3              24         ospf.auth.len     Auth Data Length
              4              32         ospf.auth.seq     Cryptographic Aequence Number

        """
        _resv = self._read_fileng(2)
        _keys = self._read_unpack(1)
        _alen = self._read_unpack(1)
        _seqn = self._read_unpack(4)

        auth = dict(
            resv = _resv,
            key_id = _keys,
            len = _alen,
            seq = _seqn,
        )

        return auth
