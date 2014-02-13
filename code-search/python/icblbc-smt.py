#!/usr/bin/env python
#
# Copyright (c) 2014 - Digital Operatives LLC
# All rights reserved
# 
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE
# Version 2.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Evan A. Sultanik, Ph.D.
#         <evan.sultanik@digitaloperatives.com>
#
# Background info is available in this blog post:
#
#     http://digitaloperatives.blogspot.com/2014/01/unambiguous-encapsulation-defending.html
#
#######################################################################

import z3
import itertools

def get_bit(bit_vector, bit_index):
    n = bit_vector.size()
    return z3.LShR(bit_vector << (n - 1 - bit_index), n-1)

def hamming_distance(bv1, bv2):
    n = bv1.size()
    assert n == bv2.size()
    differences = bv1 ^ bv2
    s = None
    for i in range(n):
        if s is None:
            s = get_bit(differences, i)
        else:
            s += get_bit(differences, i)
    return s

def find_codes(num_bits, num_codes_in_subcode_1, num_codes_in_subcode_2, min_hamming_distance, min_isolation):
    assert 2**num_bits >= num_codes_in_subcode_1 + num_codes_in_subcode_2
    subcode1 = []
    s = z3.Solver()
    for c in range(num_codes_in_subcode_1):
        subcode1.append(z3.BitVec('s1c' + str(c), num_bits))
    # for each pair of codes in this subcode, the minimum hamming distance between them must be at least min_hamming_distance:
    for c1, c2 in itertools.combinations(subcode1, 2):
        s.add(hamming_distance(c1, c2) >= min_hamming_distance)
    subcode2 = []
    for c in range(num_codes_in_subcode_2):
        subcode2.append(z3.BitVec('s2c' + str(c), num_bits))
    # for each pair of codes in this subcode, the minimum hamming distance between them must be at least min_hamming_distance:
    for c1, c2 in itertools.combinations(subcode2, 2):
        s.add(hamming_distance(c1, c2) >= min_hamming_distance)
    # for each pair of codes between the subcodes, the minimum hamming distance must be at least min_isolation:
    for c1, c2 in itertools.product(subcode1, subcode2):
        s.add(hamming_distance(c1, c2) >= min_isolation)
    while s.check() == z3.sat:
        m = s.model()
        yield (map(lambda c : m[c], subcode1), map(lambda c : m[c], subcode2))
        asmts = []
        for c in subcode1:
            asmts.append(c != m[c])
        for c in subcode2:
            asmts.append(c != m[c])
        s.add(z3.Or(*asmts)) # prevent next model from using the same assignment as a previous model

if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser(description='Enumerates Isolated Complementary Binary Linear Block Codes using Satisfiability Modulo Theories')
    argparser.add_argument('--num-bits', '-n', type=int, default=6, help='The number of bits in each codeword. Default is 6.')
    argparser.add_argument('--min-hd', '-d', type=int, default=2, help='The minimum Hamming distance allowed between any pair of codes.  Default is 2.')
    argparser.add_argument('--min-iso', '-i', type=int, default=3, help='Isolation: the minimum Hamming distance allowed between any pair of codes between the subcodes.  Default is 3.')
    argparser.add_argument('SIZE1', nargs=1, type=int, help='The number of codes in the first subcode.')
    argparser.add_argument('SIZE2', nargs=1, type=int, help='The number of codes in the second subcode.')

    args = argparser.parse_args()

    for code in find_codes(args.num_bits, args.SIZE1[0], args.SIZE2[0], args.min_hd, args.min_iso):
        print ", ".join(map(lambda c : str(sorted(map(lambda x : x.as_long(), c))), code))
