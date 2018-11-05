# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os


def check_cbm_bits(mask, info_path='/sys/fs/resctrl/info/L3'):
    if mask > get_max_mask(info_path):
        raise ValueError('Mask is bigger than allowed')

    bin_mask = format(mask, 'b')
    number_of_cbm_bits = 0
    series_of_ones_finished = False
    previous = '0'

    for bit in bin_mask:
        if bit == '1':
            if series_of_ones_finished:
                raise ValueError('Bit series of ones in mask '
                                 'must occur without a gap between them')

            number_of_cbm_bits += 1
            previous = bit
        elif bit == '0':
            if previous == '1':
                series_of_ones_finished = True

            previous = bit

    min_cbm_bits = get_min_cbm_bits(info_path)
    if number_of_cbm_bits < min_cbm_bits:
        raise ValueError(str(number_of_cbm_bits) +
                         " cbm bits. Requires minimum " +
                         str(min_cbm_bits))


def get_min_cbm_bits(info_path):
    min_cbm_bits_path = os.path.join(info_path, 'min_cbm_bits')
    with open(min_cbm_bits_path, 'r') as f:
        min_cbm_bits = f.read()
    return int(min_cbm_bits)


def get_max_mask(info_path):
    max_mask_path = os.path.join(info_path, 'cbm_mask')
    max_mask = open(max_mask_path, 'r').read()
    return int(max_mask, 16)
