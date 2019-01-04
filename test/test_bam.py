import unittest
import pathlib

from igv_reports import bam

class BAMTest(unittest.TestCase):


    def test_bam(self):


        region = {
            "chr": "minigenome",
            "start": 4000,
            "end": 10000
        }

        bam_file_path = str((pathlib.Path(__file__).parent / "data/minigenome/alignments.bam").resolve())

        alignments = bam.get_data(bam_file_path, region)

        self.assertTrue(alignments)
