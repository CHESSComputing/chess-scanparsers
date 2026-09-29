#!/usr/bin/env python3
"""Tests of SMBXRDScanParser's detector file handling and of the Eiger
stream readers, run against example detector files.

The example files are read from the folder named by the environment
variable `CHESS_SCANPARSERS_TEST_DATA`, by default
`/nfs/chess/user/ad785/codes/examples/detector_data`, laid out as:

    eig/v1/EIG16M_CdTe_002317.h5   Eiger stream v1, 10 frames
    eig/v2/EIG16M_CdTe_000282.h5   Eiger stream v2, 1 frame
    dex/ff1_000035.h5              Dexela panel 1, plain HDF5
    dex/ff2_000035.h5              Dexela panel 2, plain HDF5

Tests that need the files are skipped when the folder is missing.
`ScanParser` imports CHAP, so CHAP must be importable. Run from the
repository root with:

    python -m unittest discover -s tests -v
"""

# System modules
import os
import unittest
from unittest import mock

# Third party modules
import h5py
import numpy as np

# Local modules
from chess_scanparsers.chess_detectors import (
    EigerStreamV1File,
    EigerStreamV2File,
)
from chess_scanparsers.scanparsers import SMBXRDScanParser

DATA_DIR = os.environ.get(
    'CHESS_SCANPARSERS_TEST_DATA',
    '/nfs/chess/user/ad785/codes/examples/detector_data')
EIGER_V1 = os.path.join(DATA_DIR, 'eig', 'v1', 'EIG16M_CdTe_002317.h5')
EIGER_V2 = os.path.join(DATA_DIR, 'eig', 'v2', 'EIG16M_CdTe_000282.h5')
EIGER_SHAPE = (4362, 4148)
DEXELA_SHAPE = (3888, 3072)
DEXELA_FF1 = os.path.join(DATA_DIR, 'dex', 'ff1_000035.h5')
DEXELA_FF2 = os.path.join(DATA_DIR, 'dex', 'ff2_000035.h5')
MULTIPLIER = 1.9111

needs_data = unittest.skipUnless(
    os.path.isdir(DATA_DIR), f'Example detector data not found: {DATA_DIR}')


def make_parser(detector_data_path=DATA_DIR, spec_scan_shape=None):
    """Return an `SMBXRDScanParser` whose detector folders are found
    below `detector_data_path`, without reading a SPEC file.

    :param detector_data_path: Folder holding the detector folders,
        defaults to `DATA_DIR`.
    :type detector_data_path: str, optional
    :param spec_scan_shape: Scan shape to use in place of the one
        read from the SPEC file.
    :type spec_scan_shape: tuple[int], optional
    :rtype: SMBXRDScanParser
    """
    parser = SMBXRDScanParser(
        os.path.join(detector_data_path, 'spec.log'), 1,
        detector_data_path=detector_data_path)
    # There is no SPEC file: set the cached SPEC command, which
    # __repr__ (used in error messages) would otherwise read from it
    parser._spec_command = 'test'
    if spec_scan_shape is not None:
        # spec_scan_shape caches its value in _spec_scan_shape
        parser._spec_scan_shape = spec_scan_shape
    return parser


@needs_data
class TestDetectorFiles(unittest.TestCase):
    """`get_detector_data_files` on the example folders."""

    def test_eiger_v1(self):
        self.assertEqual(
            make_parser().get_detector_data_files('eig/v1'), [EIGER_V1])

    def test_eiger_v2(self):
        self.assertEqual(
            make_parser().get_detector_data_files('eig/v2'), [EIGER_V2])

    def test_dexela_panels_by_prefix(self):
        parser = make_parser()
        ff1 = os.path.join(DATA_DIR, 'dex', 'ff1_000035.h5')
        ff2 = os.path.join(DATA_DIR, 'dex', 'ff2_000035.h5')
        self.assertEqual(parser.get_detector_data_files('dex', 'ff1_'), [ff1])
        self.assertEqual(parser.get_detector_data_files('dex', 'ff2_'), [ff2])
        self.assertEqual(parser.get_detector_data_files('dex'), [ff1, ff2])

    def test_missing_folder(self):
        with self.assertRaises(OSError):
            make_parser().get_detector_data_files('no_such_detector')

    def test_no_matching_files(self):
        with self.assertRaises(OSError):
            make_parser().get_detector_data_files('dex', 'ff9_')


class TestFileNameChecks(unittest.TestCase):
    """`get_detector_data_files` checks on file names, with the folder
    listing faked so that no files are needed.
    """

    def list_files(self, filenames):
        """Return the detector files of a faked folder holding
        `filenames`."""
        with mock.patch('os.path.isdir', return_value=True), \
                mock.patch('os.path.isfile', return_value=True), \
                mock.patch('os.listdir', return_value=filenames):
            return make_parser('/fake/scan').get_detector_data_files('det')

    def test_padded_names_sorted(self):
        files = self.list_files(['a_010.tif', 'a_002.tif', 'a_001.tif'])
        self.assertEqual(
            [os.path.basename(f) for f in files],
            ['a_001.tif', 'a_002.tif', 'a_010.tif'])

    def test_unpadded_names(self):
        with self.assertRaises(RuntimeError):
            self.list_files(['a_1.tif', 'a_10.tif', 'a_2.tif'])

    def test_h5_and_tiff_mixed(self):
        with self.assertRaises(OSError):
            self.list_files(['a_001.h5', 'a_002.tif'])


@needs_data
class TestEigerStreamReaders(unittest.TestCase):
    """The Eiger stream readers in `chess_scanparsers.chess_detectors`."""

    def test_v1(self):
        with EigerStreamV1File(EIGER_V1) as frames:
            self.assertEqual(len(frames), 10)
            self.assertEqual(frames.shape, EIGER_SHAPE)
            self.assertEqual(frames.dtype, np.uint32)
            frame = frames[9]
            self.assertEqual(frame.shape, EIGER_SHAPE)
            self.assertEqual(frame.dtype, np.uint32)
            self.assertIsInstance(frames.metadata, dict)

    def test_index_out_of_range(self):
        with EigerStreamV1File(EIGER_V1) as frames:
            for index in (10, -1):
                with self.assertRaises(IndexError):
                    frames[index]

    def test_v2_thresholds(self):
        with EigerStreamV2File(EIGER_V2) as frames:
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames.shape, EIGER_SHAPE)
            threshold_1 = frames[0]
        with EigerStreamV2File(
                EIGER_V2, threshold_setting='threshold_2') as frames:
            threshold_2 = frames[0]
        with EigerStreamV2File(
                EIGER_V2, threshold_setting='man_diff',
                multiplier=MULTIPLIER) as frames:
            self.assertEqual(frames.dtype, np.float64)
            man_diff = frames[0]
        self.assertEqual(threshold_1.shape, EIGER_SHAPE)
        self.assertEqual(threshold_2.shape, EIGER_SHAPE)
        np.testing.assert_array_equal(
            man_diff, threshold_1 - MULTIPLIER * threshold_2)

    def test_v2_invalid_threshold_setting(self):
        with self.assertRaises(ValueError):
            EigerStreamV2File(EIGER_V2, threshold_setting='threshold_3')


@needs_data
class TestReadThroughParser(unittest.TestCase):
    """`get_detector_data_pointers` and `get_detector_data`."""

    reader_kwargs = {'threshold_setting': 'man_diff',
                     'multiplier': MULTIPLIER}

    def test_pointers_eiger_v1(self):
        parser = make_parser(spec_scan_shape=(10,))
        pointers = parser.get_detector_data_pointers(
            'eig/v1', detector_format='eiger-stream-v1')
        self.assertEqual(pointers, [(EIGER_V1, i) for i in range(10)])

    def test_pointers_two_rows(self):
        # A scan of two rows of one step each: one file per row
        parser = make_parser(spec_scan_shape=(1, 2))
        pointers = parser.get_detector_data_pointers(
            'dex', detector_format='dexela')
        self.assertEqual(pointers, [(DEXELA_FF1, 0), (DEXELA_FF2, 0)])

    def test_eiger_v1_one_step(self):
        frame = make_parser(spec_scan_shape=(10,)).get_detector_data(
            'eig/v1', 3, detector_format='eiger-stream-v1')
        self.assertEqual(frame.shape, EIGER_SHAPE)
        with EigerStreamV1File(EIGER_V1) as frames:
            np.testing.assert_array_equal(frame, frames[3])

    def test_eiger_v2_man_diff(self):
        frame = make_parser(spec_scan_shape=(1,)).get_detector_data(
            'eig/v2', 0, detector_format='eiger-stream-v2',
            reader_kwargs=self.reader_kwargs)
        self.assertEqual(frame.shape, EIGER_SHAPE)
        self.assertEqual(frame.dtype, np.float64)
        with EigerStreamV2File(EIGER_V2, **self.reader_kwargs) as frames:
            np.testing.assert_array_equal(frame, frames[0])

    def check_dexela(
            self, filename, prefix, detector_format, reader_kwargs=None):
        """Read one Dexela panel through the parser and compare it
        with a direct h5py read of `imageseries/images`."""
        frame = make_parser(spec_scan_shape=(1,)).get_detector_data(
            'dex', 0, detector_prefix=prefix,
            detector_format=detector_format, reader_kwargs=reader_kwargs)
        self.assertEqual(frame.shape, DEXELA_SHAPE)
        self.assertEqual(frame.dtype, np.uint16)
        with h5py.File(filename, 'r') as h5_file:
            np.testing.assert_array_equal(
                frame, h5_file['imageseries/images'][0])

    def test_dexela(self):
        self.check_dexela(DEXELA_FF1, 'ff1_', 'dexela')

    def test_hdf5_with_data_path(self):
        self.check_dexela(
            DEXELA_FF2, 'ff2_', 'hdf5',
            reader_kwargs={'data_path': 'imageseries/images'})

    def test_step_in_second_row(self):
        # Step 1 of a (1, 2) scan is frame 0 of the second file
        frame = make_parser(spec_scan_shape=(1, 2)).get_detector_data(
            'dex', 1, detector_format='dexela')
        with h5py.File(DEXELA_FF2, 'r') as h5_file:
            np.testing.assert_array_equal(
                frame, h5_file['imageseries/images'][0])

    def test_hdf5_without_data_path(self):
        with self.assertRaises(ValueError):
            make_parser(spec_scan_shape=(1,)).get_detector_data(
                'dex', 0, 'ff1_', detector_format='hdf5')

    def test_hdf5_unknown_reader_kwargs(self):
        with self.assertRaises(ValueError):
            make_parser(spec_scan_shape=(1,)).get_detector_data(
                'dex', 0, 'ff1_', detector_format='dexela',
                reader_kwargs={'threshold_setting': 'man_diff'})

    def test_unsupported_format(self):
        with self.assertRaises(ValueError):
            make_parser(spec_scan_shape=(1,)).get_detector_data(
                'eig/v2', 0, detector_format='no-such-format')

    def test_too_few_frames(self):
        with self.assertRaises(RuntimeError):
            make_parser(spec_scan_shape=(2,)).get_detector_data_pointers(
                'eig/v2', detector_format='eiger-stream-v2')

    def test_too_many_frames(self):
        with self.assertRaises(RuntimeError):
            make_parser(spec_scan_shape=(5,)).get_detector_data_pointers(
                'eig/v1', detector_format='eiger-stream-v1')

    def test_wrong_number_of_files(self):
        with self.assertRaises(RuntimeError):
            make_parser(spec_scan_shape=(1, 3)).get_detector_data_pointers(
                'dex', detector_format='dexela')

    def test_step_out_of_range(self):
        parser = make_parser(spec_scan_shape=(1,))
        for step in (1, -1):
            with self.assertRaises(IndexError):
                parser.get_detector_data(
                    'eig/v2', step, detector_format='eiger-stream-v2')

if __name__ == '__main__':
    unittest.main()
