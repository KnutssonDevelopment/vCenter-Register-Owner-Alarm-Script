#!/bin/python3
import os
import base64
import pwd
import grp
from pathlib import Path

script_path=Path(os.path.abspath(__file__)).parent


SECRETS_FILE = Path(script_path, 'secrets.txt').as_posix()
MARKER = '^'
ITERATIONS = 3
DEBUG = False


def harden_file_permission(file):
    uid = pwd.getpwnam('root').pw_uid
    gid = grp.getgrnam('root').gr_gid
    os.chown(file, uid, gid)
    os.chmod(file, 384)


def obfuscate(data, i):
    i -= 1
    if i <= 0:
        return base64.b64encode(data.encode()).decode()
    return obfuscate(base64.b64encode(data.encode()).decode(), i)


def deobfuscate(data, c, i=10):
    i -= 1
    if i <= 0:
        raise ValueError('Cannot deobfuscate secret')
    else:
        data = base64.b64decode(data.encode()).decode()
        if data[0] == c:
            return data[1:]
        return deobfuscate(data, c, i)


def is_obfuscated(data, m=MARKER):
    try:
        deobfuscated_data = deobfuscate(data, m)
        return True
    except:
        return False


def manage_secrets():
    if not os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, 'w') as (f):
            f.write('USERNAME=your_username_here\n')
            f.write('PASSWORD=your_password_here\n')
        harden_file_permission(SECRETS_FILE)
        print(f"Credentials file created. Please update with correct credentials. File: {SECRETS_FILE}")
        exit(1)
    else:
        with open(SECRETS_FILE, 'r') as (f):
            lines = f.readlines()
        if not lines:
            print(f"ERROR: {SECRETS_FILE} is empty or incorrectly formatted. Please delete it.")
            exit(1)
        username_data = '='.join(lines[0].split('=')[1:]).strip()
        password_data = '='.join(lines[1].split('=')[1:]).strip()
        if DEBUG:
            print(f"username_data={username_data}")
            print(f"password_data={password_data}")
        if is_obfuscated(username_data):
            if is_obfuscated(password_data):
                if DEBUG:
                    print('Loading obfuscated credentials...')
                username = deobfuscate(username_data, MARKER)
                password = deobfuscate(password_data, MARKER)
                if DEBUG:
                    print(f"username={username}")
                    print(f"password={password}")
                return (username, password)
        if username_data == 'your_username_here' or password_data == 'your_password_here':
            print(f"Credentials file created. Please update with correct credentials. File: {SECRETS_FILE}")
            exit(1)
        print('Obfuscating credentials...')
        with open(SECRETS_FILE, 'w') as (f):
            for line in lines:
                parts = line.strip().split('=')
                if parts[0] in ('USERNAME', 'PASSWORD'):
                    f.write(parts[0] + '=' + obfuscate(MARKER + '='.join(parts[1:]), ITERATIONS) + '\n')

        harden_file_permission(SECRETS_FILE)
        print('Credentials have been obfuscated.')
        return (None, None)


if __name__ == '__main__':
    try:
        username, password = manage_secrets()
    except TypeError:
        username = None
        password = None

    if username:
        if password:
            print(f"Loaded credentials for {username}.")
