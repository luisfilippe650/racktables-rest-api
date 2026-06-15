'''
IDs of RackTables object types.
Reflects the 'Dictionary' table where chapter_id = 1.
'''

GENERIC = 1
SERVER = 4
ROUTER = 7
NETWORK_SWITCH = 8
FIREWALL = 9
PATCH_PANEL = 1504
PDU = 1505
UPS = 1506
RACK = 1560
ROW = 1561
LOCATION = 1562

# Sets for validation
ALLOWED_OBJTYPES = {
    GENERIC,
    SERVER,
    ROUTER,
    NETWORK_SWITCH,
    FIREWALL,
    PATCH_PANEL,
    PDU,
    UPS,
}
