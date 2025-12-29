"""Base62 encoding utilities for short code generation."""

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(BASE62_ALPHABET)


def encode(num: int) -> str:
    """
    Encode a number to Base62 string.
    
    Args:
        num: Integer to encode
        
    Returns:
        Base62 encoded string
    """
    if num == 0:
        return BASE62_ALPHABET[0]
    
    result = []
    while num > 0:
        result.append(BASE62_ALPHABET[num % BASE])
        num //= BASE
    
    return ''.join(reversed(result))


def decode(encoded: str) -> int:
    """
    Decode a Base62 string to number.
    
    Args:
        encoded: Base62 encoded string
        
    Returns:
        Decoded integer
    """
    num = 0
    for char in encoded:
        num = num * BASE + BASE62_ALPHABET.index(char)
    return num


def obfuscate(short_code: str) -> str:
    """
    Simple obfuscation using character rotation.
    This is a bijective function that makes codes less predictable.
    
    Args:
        short_code: Original short code
        
    Returns:
        Obfuscated short code
    """
    # Simple rotation-based obfuscation
    # In production, you might use a more sophisticated bijective function
    rotated = []
    for i, char in enumerate(short_code):
        char_idx = BASE62_ALPHABET.index(char)
        # Rotate based on position
        new_idx = (char_idx + i + 1) % BASE
        rotated.append(BASE62_ALPHABET[new_idx])
    return ''.join(rotated)


def deobfuscate(obfuscated: str) -> str:
    """
    Reverse the obfuscation.
    
    Args:
        obfuscated: Obfuscated short code
        
    Returns:
        Original short code
    """
    original = []
    for i, char in enumerate(obfuscated):
        char_idx = BASE62_ALPHABET.index(char)
        # Reverse rotation
        new_idx = (char_idx - i - 1) % BASE
        original.append(BASE62_ALPHABET[new_idx])
    return ''.join(original)



