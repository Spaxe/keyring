#!/usr/bin/env python3
'''keystore - compress and encrypt your private keys
  author: Xavier Ho <contact@xavierho.com>

Usage:
  save.py [options] [--copy-to <folder>] --keystorerc <keystorerc>
  save.py [options] [--copy-to <folder>] <keystore>
  save.py (-h | --help)
  save.py --version

Options:
  --keystorerc <keystorerc>   Specify .keystorerc file path.
  --copy-to <folder>          If specified, writes files to one folder.
  -v --verbose                Print out extra information.
  -h --help                   Show this screen.
  --version                   Show version.
'''
import io
import os
import sys
import json
import gzip
import base64
import pathlib
import getpass

import simplecrypt
from docopt import docopt

from keystore import config_reader, __version__

def load(keystorerc=None, keystore=None, copyto=None, verbose=False):
  '''decrypt and write out a keystore'''

  config = None
  if keystorerc:
    config = config_reader.read(keystorerc)
    if not config:
      print('No configuration found.', file=sys.stderr)
      sys.exit(-1)
  elif keystore:
    config = {
      'keystore': keystore,
      'files': []
    }

  if 'verbose' in config and config['verbose']:
    verbose = True

  keystore_path = None
  if 'keystore' not in config:
    print('.keystorerc needs to specify a keystore file path.', file=sys.stderr)
    sys.exit(-1)
  elif not pathlib.Path(os.path.expanduser(config['keystore'])).is_file():
    # If keystore file does not exist, nothing to load and exits
    print('keystore does not exist: {}'.format(config['keystore']), file=sys.stderr)
    sys.exit(-1)
  else:
    keystore_path = config['keystore']

  if copyto and not pathlib.Path(os.path.expanduser(copyto)).is_dir():
    print('The folder to copy to does not exist: {}'.format(copyto), file=sys.stderr)
    sys.exit(-1)

  # load and attempt to unencrypt keystore by passphrase

  encrypted_keystore = None
  try:
    with open(os.path.expanduser(keystore_path), 'rb') as keystore_file:
      encrypted_keystore = keystore_file.read()

    if verbose: print('Located encrypted keystore at {}.'.format(keystore_path))

    decrypted = False
    decrypted_keystore = None
    while not decrypted:
      try:
        passphrase = getpass.getpass('Please enter the passphrase: ')
        decrypted_keystore = simplecrypt.decrypt(passphrase, encrypted_keystore)
        decrypted = True
      except simplecrypt.DecryptionException as err:
        print('Invalid passphrase. Please try again.')
      except UnicodeDecodeError as err:
        print('Keyring cannot be decrypted.\nError: {}'.format(err), file=sys.stderr)
        sys.exit(-1)

  except OSError as err:
    print('keystore cannot be opened: {}'.format(err), file=sys.stderr)
    sys.exit(-1)

  # attempt to uncompress the keystore

  decompressed_keystore = gzip.decompress(decrypted_keystore)

  # attempt to unserialise the keystore

  try:
    keystore = json.loads(decompressed_keystore)
  except json.decoder.JSONDecodeError as err:
    print('Please contact the author about this as this is a serious problem. {}'.format(err), file=sys.stderr)
    sys.exit(-1)

  if verbose: print('Keystore decrypted successfully.')

  count = 0
  for filepath, key in keystore.items():
    expanded_filepath = os.path.expanduser(filepath)
    if copyto:
      expanded_filepath = os.path.join(copyto, os.path.basename(filepath))

    confirmed = False
    overwrite = False
    if not pathlib.Path(expanded_filepath).exists():
      confirmed = True
      overwrite = True

    while not confirmed:
      overwrite = input('File {} exists. Are you sure you want to overwrite? (y)/n: '.format(expanded_filepath))
      if overwrite == '' or overwrite == 'y' or overwrite == 'Y':
        overwrite = True
        confirmed = True
      elif overwrite == 'n' or overwrite == 'N':
        overwrite = False
        confirmed = True
      else:
        print('Please enter y or n.')
    if not overwrite:
      continue

    # key ready to be created
    if verbose: print('Writing key to {} ...'.format(expanded_filepath))
    try:
      with open(expanded_filepath, 'wb') as keyfile:
        b64_decoded = base64.decodebytes(key.encode('utf-8'))
        keyfile.write(b64_decoded)
      count += 1
    except OSError as err:
      print('File system threw an error: {}'.format(err), file=sys.stderr)
      print('Skipping {}'.format(expanded_filepath))

  if verbose: print('Keystore restored {} keys.'.format(count))

if __name__ == '__main__':
  arguments = docopt(__doc__, version=__version__)

  if arguments['<keystore>']:
    load(
      keystore=arguments['<keystore>'],
      copyto=arguments['--copy-to'],
      verbose=arguments['--verbose']
    )
  elif arguments['--keystorerc']:
    load(
      keystorerc=arguments['--keystorerc'],
      copyto=arguments['--copy-to'],
      verbose=arguments['--verbose']
    )