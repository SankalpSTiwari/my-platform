"""Tests for Base62 encoding utilities."""

import pytest
from urlshortener.shared.utils.base62 import encode, decode, obfuscate, deobfuscate


def test_encode_zero():
    """Test encoding zero."""
    assert encode(0) == "0"


def test_encode_small_numbers():
    """Test encoding small numbers."""
    assert encode(1) == "1"
    assert encode(10) == "A"
    assert encode(35) == "Z"
    assert encode(36) == "a"
    assert encode(61) == "z"
    assert encode(62) == "10"


def test_decode_small_strings():
    """Test decoding small strings."""
    assert decode("0") == 0
    assert decode("1") == 1
    assert decode("A") == 10
    assert decode("Z") == 35
    assert decode("a") == 36
    assert decode("z") == 61
    assert decode("10") == 62


def test_encode_decode_roundtrip():
    """Test that encode and decode are inverse operations."""
    test_numbers = [0, 1, 10, 100, 1000, 10000, 100000, 1000000, 999999999]
    for num in test_numbers:
        encoded = encode(num)
        decoded = decode(encoded)
        assert decoded == num, f"Failed for {num}: encoded={encoded}, decoded={decoded}"


def test_obfuscate_deobfuscate_roundtrip():
    """Test that obfuscate and deobfuscate are inverse operations."""
    test_codes = ["Ab3x9Q", "123abc", "XYZ789", "0aBcDeF"]
    for code in test_codes:
        obfuscated = obfuscate(code)
        deobfuscated = deobfuscate(obfuscated)
        assert deobfuscated == code, f"Failed for {code}: obfuscated={obfuscated}, deobfuscated={deobfuscated}"


def test_obfuscate_changes_output():
    """Test that obfuscation actually changes the output."""
    code = "Ab3x9Q"
    obfuscated = obfuscate(code)
    assert obfuscated != code, "Obfuscation should change the code"



