from collections import defaultdict
from typing import Callable, Tuple

from brukeropusreader.block_parser import parse_series, parse_param, parse_text


class UnknownBlockType(Exception):
    pass

# data_type = 0
BLOCK_0 = defaultdict(
    lambda: ("Text Information", parse_text),
    {
        8: ("Info Block", parse_param),
        104: ("History", parse_text),
        152: ("Curve Fit", parse_text),
        168: ("Signature", parse_text),
        240: ("Integration Method", parse_text),
    },
)

# data_type = 7
BLOCK_7 = {
    # Key is channel_type
    4: "ScSm",
    8: "IgSm",
    12: "PhSm",
    132: "ScSm_(1)",
    136: "IgSm_(1)"
    }

# data_type = 11
BLOCK_11 = {
    # Key is channel_type
    4: "ScRf",
    8: "IgRf",
    132: "ScRf_(1)",
    136: "IgRf_(1)"
    }

# data_type = 23
BLOCK_23 = {
    # Key is channel_type
    4: "ScSm Data Parameter",
    8: "IgSm Data Parameter",
    12: "PhSm Data Parameter",
    132: "ScSm_(1) Data Parameter",
    136: "IgSm_(1) Data Parameter"
    }

# data_type = 27
BLOCK_27 = {
    # Key is channel_type
    4: "ScRf Data Parameter",
    8: "IgRf Data Parameter",
    132: "ScRf_(1) Data Parameter",
    136: "IgRf_(1) Data Parameter"
    }

# data_type = 31
BLOCK_31 = {
    # Key is channel_type
    16: "AB Data Parameter",
    # channel_type = 16 was the one which was renamed to AB Data Parameter_(1)
    # by the parse_data script from opus_parser. I assume this is incorrect, as
    # data_type 15 channel_type 144 of AB was renamed to AB_(1)
    144: "AB_(1) Data Parameter"
    }

DIFFERENT_BLOCKS = {
    # Key is data_type
    31: "AB Data Parameter",
    32: "Instrument",
    40: "Instrument (Rf)",
    48: "Acquisition",
    56: "Acquisition (Rf)",
    64: "Fourier Transformation",
    72: "Fourier Transformation (Rf)",
    96: "Optik",
    104: "Optik (Rf)",
    160: "Sample"
    }


class BlockMeta:
    def __init__(
        self,
        data_type: int,
        channel_type: int,
        text_type: int,
        chunk_size: int,
        offset: int,
    ):
        self.data_type = data_type
        self.channel_type = channel_type
        self.text_type = text_type
        self.chunk_size = chunk_size
        self.offset = offset

    def get_name_and_parser(self) -> Tuple[str, Callable]:
        if self.data_type == 0:
            return BLOCK_0[self.text_type]
        elif self.data_type == 7:
            return BLOCK_7[self.channel_type], parse_series
        elif self.data_type == 11:
            return BLOCK_11[self.channel_type], parse_series
        elif self.data_type == 15:
            return "AB", parse_series
        elif self.data_type == 23:
            return BLOCK_23[self.channel_type], parse_param
        elif self.data_type == 27:
            return BLOCK_27[self.channel_type], parse_param
        elif self.data_type == 31:
            return BLOCK_31[self.channel_type], parse_param
        elif self.data_type in DIFFERENT_BLOCKS.keys():
            return DIFFERENT_BLOCKS[self.data_type], parse_param
        else:
            raise UnknownBlockType()
