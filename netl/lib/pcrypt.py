from passlib.hash import pbkdf2_sha512 as pb

def hash(cleartext):
    """
    Hash using PBKDF2 scheme over SHA-512

    :param cleartext:
    :return: hash string
    """
    return pb.encrypt(cleartext,rounds=10001)

def verify(cleartext, ciphertext):
    """
    Match cleartext against a hash

    :param cleartext:
    :param ciphertext:
    :return:
    """
    return pb.verify(cleartext, ciphertext)