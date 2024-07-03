from enum import Enum


class PayloadPreprocessor(Enum):
    ZLIB_DECOMPRESS = "ZLIB_DECOMPRESS"
    JSON_LOADS = "JSON_LOADS"
    BYTES_DECODE = "BYTES_DECODE"
