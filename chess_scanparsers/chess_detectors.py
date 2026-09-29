#!/usr/bin/env python3
#
# The Eiger stream readers in this module, from `_read_string` to
# `EigerStreamV2File`, are derived from hexrd
# (https://github.com/HEXRD/hexrd) and distributed under the license
# below. See also hexrd's NOTICE file:
# https://github.com/HEXRD/hexrd/blob/master/NOTICE
#
# BSD 3-Clause License
#
# Copyright (c) 2024, Lawrence Livermore National Laboratory, Air Force Research
# Laboratory, and Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""Frame-by-frame access to area detector files, by file format.

:func:`open_detector_file` returns the frames of one file as a
sequence: `len()` gives the number of frames without reading any
pixels, and indexing reads only the frame asked for.

The readers for HDF5 files written by the Eiger stream receiver,
versions 1 and 2, are stripped down from hexrd 0.10.2
(https://github.com/HEXRD/hexrd):
`hexrd/core/imageseries/load/eiger_stream_v1.py`,
`hexrd/core/imageseries/load/eiger_stream_v2.py`,
`hexrd/core/imageseries/load/eiger.py` (`decompress_frame`) and
`hexrd/core/utils/hdf5.py` (`unwrap_h5_to_dict`), without hexrd's
imageseries machinery.
"""

# System modules
from io import BytesIO

# Third party modules
import h5py
import numpy as np

DEFAULT_DEXELA_DATA_PATH = 'imageseries/images'
DETECTOR_FORMATS = (
    None, 'eiger-stream-v1', 'eiger-stream-v2', 'hdf5', 'dexela')


class _Frames:
    """Base class for a read-only sequence of the frames in one
    detector file, usable as a context manager. Subclasses set
    `filename` and define `close`, `__len__` and `_get_frame`.
    """

    def close(self):
        """Close the file."""
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, key):
        """Return frame `key`, or with `key = (index, *rest)` that
        frame indexed by `rest`."""
        if isinstance(key, tuple):
            return self[key[0]][key[1:]]
        if not 0 <= key < len(self):
            raise IndexError(
                f'Frame {key} out of range for {self.filename}, which '
                f'holds {len(self)} frames')
        return self._get_frame(key)

    def __iter__(self):
        for index in range(len(self)):
            yield self[index]

    def _get_frame(self, index):
        raise NotImplementedError


class HDF5Frames(_Frames):
    """Frames of one dataset in a plain HDF5 file: a 3D dataset holds
    its frames along axis 0, a 2D dataset is a single frame.
    """
    def __init__(self, filename, data_path):
        """
        :param filename: Name of the HDF5 file.
        :type filename: str
        :param data_path: Path of the dataset in the file.
        :type data_path: str
        :raises ValueError: If the dataset is not 2D or 3D.
        """
        self.filename = filename
        self.data_path = data_path
        self._h5file = h5py.File(filename, 'r')
        try:
            self._dataset = self._h5file[data_path]
            if self._dataset.ndim not in (2, 3):
                raise ValueError(
                    f'Dataset {data_path} in {filename} is '
                    f'{self._dataset.ndim}D, expected 2D or 3D')
        except Exception:
            self._h5file.close()
            raise

    def close(self):
        self._h5file.close()

    def __len__(self):
        if self._dataset.ndim == 2:
            return 1
        return self._dataset.shape[0]

    def _get_frame(self, index):
        if self._dataset.ndim == 2:
            return self._dataset[()]
        return self._dataset[index]


class FabioFrames(_Frames):
    """Frames of an image file that `fabio` reads, e.g. a TIFF."""
    def __init__(self, filename):
        """
        :param filename: Name of the image file.
        :type filename: str
        """
        # Third party modules
        import fabio

        self.filename = filename
        self._image = fabio.open(filename)

    def close(self):
        self._image.close()

    def __len__(self):
        return self._image.nframes

    def _get_frame(self, index):
        if index == 0:
            return self._image.data
        return self._image.getframe(index).data


# Eiger stream readers, derived from hexrd (see the license at the top
# of this module)

def _read_string(dataset):
    """Return the value of a string dataset as a `str`."""
    string_dtype = h5py.check_string_dtype(dataset.dtype)
    if string_dtype is not None and string_dtype.encoding == 'utf-8':
        dataset = dataset.asstr()
    value = dataset[()]
    if isinstance(value, (bytes, np.bytes_)):
        value = value.decode('utf-8')
    return value


def unwrap_h5_to_dict(group):
    """Return the datasets below an HDF5 group as a nested dictionary
    of the same structure. Attributes are ignored, string datasets
    become `str` and single-element 1D datasets become scalars.

    :param group: HDF5 group (or file) to unwrap.
    :type group: h5py.Group
    :rtype: dict
    """
    d = {}
    for key, val in group.items():
        if isinstance(val, h5py.Group):
            d[key] = unwrap_h5_to_dict(val)
        elif val.dtype == np.dtype('O'):
            d[key] = _read_string(val)
        else:
            value = np.array(val)
            if value.ndim == 1 and len(value) == 1:
                value = value[0]
            d[key] = value
    return d


def _decompress_csrnpz(d):
    """Return a frame stored as a sparse `scipy` CSR array in NPZ
    format."""
    # Third party modules
    from scipy.sparse import load_npz

    # The first 8 bytes hold the length of the compressed data. The
    # dtype and shape are also stored inside the NPZ data.
    npz_data = d['data'].tobytes()[8:]
    return load_npz(BytesIO(npz_data)).toarray()


def decompress_frame(d):
    """Return one frame from its unwrapped HDF5 entry.

    :param d: The frame's entry, as returned by
        :func:`unwrap_h5_to_dict`, with keys `'compression_type'`,
        `'dtype'`, `'shape'`, `'data'` and `'elem_size'`.
    :type d: dict
    :raises ValueError: If the compression type is not supported.
    :rtype: numpy.ndarray
    """
    compression_type = d['compression_type']
    dtype = d['dtype']
    shape = d['shape']
    data = d['data']

    if compression_type is None:
        return np.frombuffer(data, dtype=dtype).reshape(shape)
    if compression_type == 'csrnpz':
        return _decompress_csrnpz(d)
    if compression_type in ('lz4', 'bslz4'):
        # Third party modules
        from dectris.compression import decompress

        decompressed_bytes = decompress(
            data, compression_type, elem_size=d['elem_size'])
        return np.frombuffer(decompressed_bytes, dtype=dtype).reshape(shape)
    raise ValueError(f'Unsupported compression type: {compression_type}')


class _EigerStreamFile(_Frames):
    """Read-only sequence of the frames in an Eiger stream HDF5 file.
    A frame is read and decompressed when it is accessed.
    """
    def __init__(self, filename):
        """
        :param filename: Name of the HDF5 file.
        :type filename: str
        """
        self.filename = filename
        self._h5file = h5py.File(filename, 'r')
        try:
            self.metadata = unwrap_h5_to_dict(self._h5file['/metadata'])
        except Exception:
            self._h5file.close()
            raise

    def close(self):
        """Close the HDF5 file."""
        if self._h5file is not None:
            self._h5file.close()
            self._h5file = None

    def __getstate__(self):
        # An open h5py file cannot be pickled: reopen it on unpickling
        state = self.__dict__.copy()
        state.pop('_h5file')
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._h5file = h5py.File(self.filename, 'r')

    def __len__(self):
        return len(self._h5file['data'])

    def _load_frame(self, entry_path):
        """Return the frame stored in the entry at `entry_path` below
        the file's `data` group."""
        return decompress_frame(
            unwrap_h5_to_dict(self._h5file['data'][entry_path]))


class EigerStreamV1File(_EigerStreamFile):
    """Frames of an Eiger stream (version 1) HDF5 file, where frame
    `k` is stored in the group `/data/<k>`.
    """
    def _get_frame(self, index):
        return self._load_frame(str(index))

    @property
    def dtype(self):
        return np.dtype(self._h5file['data/0/dtype'][()])

    @property
    def shape(self):
        return tuple(int(n) for n in self._h5file['data/0/shape'][()])


class EigerStreamV2File(_EigerStreamFile):
    """Frames of an Eiger stream (version 2) HDF5 file, where frame
    `k` is stored for each energy threshold in the groups
    `/data/<k>/threshold_1` and `/data/<k>/threshold_2`.
    """
    threshold_settings = ('threshold_1', 'threshold_2', 'man_diff')

    def __init__(
            self, filename, threshold_setting='threshold_1', multiplier=1.0):
        """
        :param filename: Name of the HDF5 file.
        :type filename: str
        :param threshold_setting: Which frames to return:
            `'threshold_1'`, `'threshold_2'` or `'man_diff'`
            (`threshold_1 - multiplier * threshold_2`), defaults to
            `'threshold_1'`.
        :type threshold_setting: str, optional
        :param multiplier: Multiplier of `threshold_2` for
            `'man_diff'`, defaults to `1.0`.
        :type multiplier: float, optional
        :raises ValueError: If `threshold_setting` is not one of the
            above.
        """
        if threshold_setting not in self.threshold_settings:
            raise ValueError(
                f'Invalid threshold_setting "{threshold_setting}", '
                f'allowed values are: {", ".join(self.threshold_settings)}')
        super().__init__(filename)
        self.threshold_setting = threshold_setting
        self.multiplier = float(multiplier)

    def _get_frame(self, index):
        if self.threshold_setting == 'man_diff':
            return (self._load_frame(f'{index}/threshold_1')
                    - self.multiplier
                    * self._load_frame(f'{index}/threshold_2'))
        return self._load_frame(f'{index}/{self.threshold_setting}')

    @property
    def dtype(self):
        if self.threshold_setting == 'man_diff':
            return np.dtype('float64')
        return np.dtype(self._h5file['data/0/threshold_1/dtype'][()])

    @property
    def shape(self):
        shape = self._h5file['data/0/threshold_1/shape'][()]
        return tuple(int(n) for n in shape)


def open_detector_file(filename, detector_format=None, reader_kwargs=None):
    """Return the frames of one detector file as a sequence that reads
    a frame only when it is indexed. Use it as a context manager, or
    call its `close` method.

    :param filename: Name of the detector file.
    :type filename: str
    :param detector_format: Format of the file: `'eiger-stream-v1'`
        or `'eiger-stream-v2'` (:class:`EigerStreamV1File`,
        :class:`EigerStreamV2File`), `'hdf5'` (one dataset of frames,
        :class:`HDF5Frames`; needs `data_path` in `reader_kwargs`),
        `'dexela'` (`'hdf5'` with `data_path` defaulting to
        `'imageseries/images'`), or `None` to read it with `fabio`
        (:class:`FabioFrames`), defaults to `None`.
    :type detector_format: str, optional
    :param reader_kwargs: Keyword arguments for the reader, e.g.
        `{'threshold_setting': 'man_diff', 'multiplier': 1.9111}` for
        `'eiger-stream-v2'`, or `{'data_path': 'imageseries/images'}`
        for `'hdf5'`.
    :type reader_kwargs: dict, optional
    :raises ValueError: If the format is not supported, or the
        `reader_kwargs` do not fit it.
    :return: The frames of the file, supporting `len()` and indexing
        by frame number.
    """
    kwargs = dict(reader_kwargs or {})
    if detector_format is None:
        if kwargs:
            raise ValueError(
                'detector_format None (fabio) takes no reader_kwargs, got: '
                f'{", ".join(kwargs)}')
        return FabioFrames(filename)
    if detector_format in ('hdf5', 'dexela'):
        if detector_format == 'dexela':
            kwargs.setdefault('data_path', DEFAULT_DEXELA_DATA_PATH)
        data_path = kwargs.pop('data_path', None)
        if data_path is None:
            raise ValueError(
                f'detector_format "{detector_format}" needs the path of the '
                "dataset in the file in reader_kwargs['data_path']")
        if kwargs:
            raise ValueError(
                f'Unsupported reader_kwargs for detector_format '
                f'"{detector_format}": {", ".join(kwargs)}')
        return HDF5Frames(filename, data_path)
    if detector_format == 'eiger-stream-v1':
        return EigerStreamV1File(filename, **kwargs)
    if detector_format == 'eiger-stream-v2':
        return EigerStreamV2File(filename, **kwargs)
    raise ValueError(
        f'Unsupported detector_format "{detector_format}", allowed values '
        f'are: {", ".join(str(f) for f in DETECTOR_FORMATS)}')
