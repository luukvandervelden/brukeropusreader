from typing import List
from brukeropusreader.block_data import BlockMeta, UnknownBlockType
from brukeropusreader.constants import (
    HEADER_LEN,
    FIRST_CURSOR_POSITION,
    META_BLOCK_SIZE,
    JUNK_LINES_START,
    JUNK_LINES_BETWEEN
)
from brukeropusreader.opus_reader import (
    read_data_type,
    read_channel_type,
    read_text_type,
    read_additional_type,
    read_chunk_size,
    read_offset,
)
import numpy as np
from scipy.interpolate import interp1d


class OpusData(dict):
    def __init__(self, file_path):
        # Read the file
        with open(file_path, "rb") as opus_file:
            data = opus_file.read()
        # Parse the metadata
        meta_data = self.parse_meta(data)
        # Parse the data
        self = self.parse_data(data, meta_data)

    def parse_meta(self, data: bytes) -> List[BlockMeta]:
        """Parse the header of the opus file.

        Returns a list of metadata (BlockMeta) for each block to be read,

        :parameter:
            data: bytes content of the opus file
        :returns:
            parse_meta: list of BlockMeta
        """
        header = data[:HEADER_LEN]
        spectra_meta = []
        cursor = FIRST_CURSOR_POSITION
        while True:
            if cursor + META_BLOCK_SIZE > HEADER_LEN:
                break

            data_type = read_data_type(header, cursor)
            channel_type = read_channel_type(header, cursor)
            text_type = read_text_type(header, cursor)
            additional_type = read_additional_type(header, cursor)
            chunk_size = read_chunk_size(header, cursor)
            offset = read_offset(header, cursor)

            if offset <= 0:
                break

            block_meta = BlockMeta(data_type, channel_type, text_type,
                                   additional_type, chunk_size, offset)

            spectra_meta.append(block_meta)

            next_offset = offset + 4 * chunk_size
            if next_offset >= len(data):
                break
            cursor += META_BLOCK_SIZE
        return spectra_meta

    def parse_data(self, data: bytes, blocks_meta: List[BlockMeta]):
        """parse the data of the opus file using the file header's informations
        parame"""
        for block_meta in blocks_meta:
            try:
                name, parser = block_meta.get_name_and_parser()
            except UnknownBlockType:
                continue
            parsed_data = parser(data, block_meta)
            # in some instances, multiple entries - in particular 'AB' are
            # present. They are added with a key ending by
            # '_(1)', '_(2)', etc...
            if name in self.keys():
                i = 1
                while name + '_(' + str(i) + ')' in self.keys():
                    i += 1
                name = name + '_(' + str(i) + ')'
            self[name] = parsed_data
        return self

    def get_range(self, spec_name="AB", wavenums=True):
        '''Get the wavelength, by reading the lower (LXV) and
        upper (FXV) limit and interpolating the values, based on the reported
        number of datapoints (NPT)
        '''
        param_key = f"{spec_name} Data Parameter"
        FXV = self[param_key]["FXV"]
        LXV = self[param_key]["LXV"]
        # the number of points here is OK.
        # It is "AB" that can return more values (equals to zero)
        NPT = self[param_key]["NPT"]
        x_no_unit = np.linspace(FXV, LXV, NPT)
        if wavenums:
            return x_no_unit
        else:
            return 10_000_000 / x_no_unit

    def interpolate(self, start, stop, num, spec_name="AB"):
        xav = self.get_range(spec_name=spec_name)
        yav = self[spec_name]
        iwave_nums = np.linspace(start, stop, num)
        f2 = interp1d(xav, yav, kind="cubic", fill_value="extrapolate")
        return iwave_nums, f2(iwave_nums)

    def parse_sm(self, data_type="ScSm"):
        # Time-resolved data (interferogram goes in IgSm, spectrum in ScSm)
        # unless only one time slice, when it can be handled as normal data,
        # has some lines of junk in there.  The magic numbers below are
        # consistent across all tests by ChrisHodgesUK
        WAS = self["Acquisition"]["WAS"]#number of timeslices
        NPT = self[f"{data_type} Data Parameter"]["NPT"]# points per timeslice
        raw_Sm = self[data_type]#grab the data
        if WAS == 1:
            Sm = self[data_type][0:NPT]
        else:
            Sm = np.zeros((NPT,WAS))
            for timeslice in range(WAS): #reshape the array, discarding junk
                start = JUNK_LINES_START + timeslice*(NPT + JUNK_LINES_BETWEEN)
                Sm[:,timeslice] = raw_Sm[start:start+NPT]

        return Sm

    def get_spectra(self, spec_name="AB"):
        '''Get the spectra series. The first spectrum starts after a number of
        junk lines 'JUNK_LINES_START'. There is 'JUNK_LINES_BETWEEN'
        lines between the spectra.
        '''
        data = self[spec_name]
        NPT = self[f"{spec_name} Data Parameter"]["NPT"]
        num_spectra = round(
            (data.size - JUNK_LINES_START) / (NPT + JUNK_LINES_BETWEEN))

        spectra = np.empty(shape=(num_spectra, NPT))
        for i in range(0,num_spectra):
            start = JUNK_LINES_START + i*(NPT + JUNK_LINES_BETWEEN)
            spectra[i] = data[start:start+NPT]

        return spectra
