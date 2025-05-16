#!usr/bin/env python3

# Local modules
from .scanparsers import *

version = 'PACKAGE_VERSION'

def choose_scanparser(station, experiment):
    """Return the best subclass of ScanParser to use for a scan taken
    at the specified station and belonging to the specified experiment
    type.

    :param station: The name of the station at which the scan was
        collected.
    :type station: Literal['id1a3', 'id3a', 'id3b', 'id4b']
    :param experiment: Type of X-ray measurement to which this scan
        belongs.
    :type experiment: Literal['edd', 'giwaxs', 'saxswaxs', 'powder', 'tomo',
        'xrf', 'hdrm', 'n/a']
    :returns: The most appropriate type of ScanParser to use.
    :rtype: type
    """
    station = station.lower()
    experiment = experiment.lower()
    if station in ('id1a3', 'id3a'):
        if experiment in ('saxswaxs', 'powder'):
            return SMBLinearScanParser
        elif experiment == 'edd':
            return SMBMCAScanParser
        elif experiment == 'tomo':
            return SMBRotationScanParser
        raise ValueError(
            f'Invalid experiment type for station {station}: {experiment}')
    elif station == 'id3b':
        if experiment == 'giwaxs':
            return FMBGIWAXSScanParser
        elif experiment in ('saxswaxs', 'powder'):
            return FMBSAXSWAXSScanParser
        elif experiment == 'tomo':
            return FMBRotationScanParser
        elif experiment == 'xrf':
            return FMBXRFScanParser
        raise ValueError(
            f'Invalid experiment type for station {station}: {experiment}')
    elif station == 'id4b':
        if experiment == 'hdrm':
            return QM2HDRMScanParser
        raise ValueError(
            f'Invalid experiment type for station {station}: {experiment}')
#        return QM2HDRMScanParser
    raise ValueError(f'Invalid station: {station}')
