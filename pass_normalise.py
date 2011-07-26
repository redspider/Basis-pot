from netl.lib.pass_check import passwords

def norm(p):
    new_p = p.lower()
    if new_p[-1] == '1' or new_p[-1] == '!':
        new_p = new_p[:-1]
    return new_p

seen = {}

for p in passwords.split('\n'):
    if p:
        np = norm(p)
        if len(np) >= 7 and not seen.has_key(np):
            seen[np] = 1
            print np