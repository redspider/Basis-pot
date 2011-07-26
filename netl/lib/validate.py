"""
Validation package

This set of functions is designed to validate for security purposes only. User-friendly validation should occur
client-side.

Each validator is designed to be chained:

username = validator.username(validator.ascii(request.POST['username']))

although for the most part that shouldn't be necessary.

In the event that the validation fails, a ValidationError will be raised

"""

import re

class ValidationError(Exception):
    pass

def ascii(s):
    """
    Check a string can be encoded as ascii
    """
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        raise ValidationError()

    return s
        

def username(s):
    """
    Basic username validity check. No unicode, no non-url/filesafe chars, NO UPPERCASE
    """
    if not ascii(s):
        raise ValidationError()

    if len(s) < 3:
        raise ValidationError()

    if len(s) > 63:
        raise ValidationError()

    if not re.match(r'[a-z0-9\-_]+', s):
        raise ValidationError()

    return s

def password(s):
    """
    Basic password validity check. No unicode
    """
    if not ascii(s):
        raise ValidationError()

    if len(s) < 8:
        raise ValidationError()

    return s

def email(s):
    """
    Permissive email check, since honestly...how can you even validate the bastards.
    """
    if not ascii(s):
        raise ValidationError()

    if not re.match(r'\S+?@[^@\.]+\.[^@]', s):
        raise ValidationError()

    return s

def number(s):
    """
    Paranoid number check. ONLY digits, no leading zero.
    """
    if len(s) < 1:
        raise ValidationError()

    if not re.match(r'[1-9][0-9]*', s):
        raise ValidationError()

    try:
        int(s)
    except ValueError:
        raise ValidationError()

    return s

    