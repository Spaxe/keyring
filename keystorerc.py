#!/usr/bin/env python3
'''
  keystore - compress and encrypt your private keys
  author: Xavier Ho <contact@xavierho.com>

  License: MIT
'''
import os
import sys
import json

def read(filepath):
  path = None

  try:
    if os.path.isfile(os.path.expanuser(filepath)):
      path = os.path.expanuser(filepath)
    if os.path.isfile('./.keystorerc'):
      path = './.keystorerc'
    elif os.path.isfile('~/.keystorerc'):
      path = '~/.keystorerc'
    else:
      raise OSError('The config file .keystorerc is not found in home or local working directory.')

    with open(path) as f:
      conf = json.loads(f.read())
      return conf

  except OSError as err:
    print('Unable to open config: {}'.format(err), file=sys.stderr)
    return None

  except json.JSONDecodeError as err:
    print('Unable to parse config: {}'.format(err), file=sys.stderr)
    return None