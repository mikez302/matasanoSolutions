import decimal

from hashlib import sha1
from itertools import cycle
from math import ceil, gcd
from random import SystemRandom

random = SystemRandom()

# prime number specified for 1536-bit modular exponential group in RFC
# at https://datatracker.ietf.org/doc/rfc3526/?include_text=1. Used for
# Diffie-Hellman and SRP.
IETF_PRIME = int("ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea"
                 "63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c2"
                 "45e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f2"
                 "4117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24"
                 "cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f17"
                 "46c08ca237327ffffffffffffffff", 16)


def xor_bytes(*bytes_objects):
    lengths = [len(b) for b in bytes_objects]
    if len(set(lengths)) > 1:
        raise ValueError("inputs must be of equal length")
    result = bytearray([0]) * lengths[0]
    for b in bytes_objects:
        for i, byte in enumerate(b):
            result[i] ^= byte
    return bytes(result)


def apply_repeating_xor_key(input_bytes, key):
    return bytes(a ^ b for a, b in zip(input_bytes, cycle(key)))


def chunks(x, chunk_size=16):
    return [x[i : i + chunk_size] for i in range(0, len(x), chunk_size)]


def int_to_bytes(x):
    return x.to_bytes(length=ceil(x.bit_length() / 8), byteorder="big")


def pretty_hex_bytes(x):
    return " ".join(chunks(x.hex(), 2))


def calculate_hmac(key, message, hash_fn=sha1):
    key_hash = hash_fn(key).digest()
    o_key_pad = apply_repeating_xor_key(key_hash, b"\x5c")
    i_key_pad = apply_repeating_xor_key(key_hash, b"\x36")
    return hash_fn(o_key_pad + hash_fn(i_key_pad + message).digest()).digest()


def mod_inv(a, m):
    """Return the integer x such that (a * x) % m == 1."""
    # This function uses the extended Euclidean algorithm.
    x0, x1, y0, y1 = 1, 0, 0, 1
    a1, m1 = a, m
    while m1:
        q = a1 // m1
        a1, m1 = m1, a1 % m1
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1

    assert a1 == gcd(a, m)
    assert a*x0 + m*y0 == a1

    if a1 != 1:
        raise ValueError("modular inverse does not exist")
    else:
        return x0 % m


def big_int_cube_root(x):
    """Return the cube root of the given number.

    This works with integers that would cause OverflowErrors when trying to
    calculate the cube root the more straightforward way (x ** (1/3)). It
    seems to reliably return the result with enough precision that cubing it
    and rounding the cube produces the original number, although I don't yet
    have any rigorous proof of this.
    """
    with decimal.localcontext() as context:
        # Guesstimate as to how much precision is needed to get the right result
        context.prec = len(str(x)) // 3 + 4
        return decimal.Decimal(x) ** (decimal.Decimal(1) / decimal.Decimal(3))
