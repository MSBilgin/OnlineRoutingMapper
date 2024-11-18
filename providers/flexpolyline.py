# Copyright (C) 2019 HERE Europe B.V.
# Licensed under MIT, see full license in LICENSE
# SPDX-License-Identifier: MIT
# License-Filename: LICENSE

# Simplified from https://github.com/heremaps/flexible-polyline/tree/master/python/flexpolyline

from collections import namedtuple

ABSENT = 0
LEVEL = 1
ALTITUDE = 2
ELEVATION = 3
RESERVED1 = 4  # Reserved for future types
RESERVED2 = 5  # Reserved for future types
CUSTOM1 = 6
CUSTOM2 = 7

__THIRD_DIM_MAP = {
    ALTITUDE: 'alt',
    ELEVATION: 'elv',
    LEVEL: 'lvl',
    RESERVED1: 'rsv1',
    RESERVED2: 'rsv2',
    CUSTOM1: 'cst1',
    CUSTOM2: 'cst2',
}

__FORMAT_VERSION = 1

__DECODING_TABLE = [
    62, -1, -1, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
    22, 23, 24, 25, -1, -1, -1, -1, 63, -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
    36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51
]


__PolylineHeader = namedtuple('PolylineHeader', 'precision,third_dim,third_dim_precision')


def __decode_header(decoder):
    """Decode the polyline header from an `encoded_char`. Returns a PolylineHeader object."""
    version = next(decoder)
    if version != __FORMAT_VERSION:
        raise ValueError('Invalid format version')
    value = next(decoder)
    precision = value & 15
    value >>= 4
    third_dim = value & 7
    third_dim_precision = (value >> 3) & 15
    return __PolylineHeader(precision, third_dim, third_dim_precision)


def __get_third_dimension(encoded):
    """Return the third dimension of an encoded polyline.
    Possible returned values are: ABSENT, LEVEL, ALTITUDE, ELEVATION, CUSTOM1, CUSTOM2."""
    header = __decode_header(__decode_unsigned_values(encoded))
    return header.third_dim


def __decode_char(char):
    """Decode a single char to the corresponding value"""
    char_value = ord(char)

    try:
        value = __DECODING_TABLE[char_value - 45]
    except IndexError:
        raise ValueError('Invalid encoding')
    if value < 0:
        raise ValueError('Invalid encoding')
    return value


def __to_signed(value):
    """Decode the sign from an unsigned value"""
    if value & 1:
        value = ~value
    value >>= 1
    return value


def __decode_unsigned_values(encoded):
    """Return an iterator over encoded unsigned values part of an `encoded` polyline"""
    result = shift = 0

    for char in encoded:
        value = __decode_char(char)

        result |= (value & 0x1F) << shift
        if (value & 0x20) == 0:
            yield result
            result = shift = 0
        else:
            shift += 5

    if shift > 0:
        raise ValueError('Invalid encoding')


def __iter_decode(encoded):
    """Return an iterator over coordinates. The number of coordinates are 2 or 3
    depending on the polyline content."""

    last_lat = last_lng = last_z = 0
    decoder = __decode_unsigned_values(encoded)

    header = __decode_header(decoder)
    factor_degree = 10.0 ** header.precision
    factor_z = 10.0 ** header.third_dim_precision
    third_dim = header.third_dim

    while True:
        try:
            last_lat += __to_signed(next(decoder))
        except StopIteration:
            return  # sequence completed

        try:
            last_lng += __to_signed(next(decoder))

            if third_dim:
                last_z += __to_signed(next(decoder))
                yield (last_lat / factor_degree, last_lng / factor_degree, last_z / factor_z)
            else:
                yield (last_lat / factor_degree, last_lng / factor_degree)
        except StopIteration:
            raise ValueError("Invalid encoding. Premature ending reached")


def decode(encoded):
    """Return a list of coordinates. The number of coordinates are 2 or 3
    depending on the polyline content."""
    return list(__iter_decode(encoded))
