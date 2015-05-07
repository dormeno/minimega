'''
Copyright (2015) Sandia Corporation.
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
the U.S. Government retains certain rights in this software.

Devin Cook <devcook@sandia.gov>

Minimega bindings for Python

**************************************************************************
* THIS FILE IS AUTOMATICALLY GENERATED. DO NOT MODIFY THIS FILE BY HAND. *
**************************************************************************

This API uses a Unix domain socket to communicate with a running instance of
minimega. The protocol is documented here, under "Command Port and the Local
Command Flag":
http://minimega.org/articles/usage.article#TOC_2.2.

This file is automatically generated from the output of "minimega -cli". See
the documentation for genapi.py for details on how to regenerate this file.

This API *should* work for both python2.7 and python3. Please report any issues
to the bug tracker:
https://github.com/sandia-minimega/minimega/issues
'''


import json
import socket
import inspect
from threading import Lock
from collections import namedtuple


# This version is specific to the python API. It is not indicative of the
#  versions of minimega that it can talk with.
__version__ = '{{ version }}'


class Error(Exception): pass
class ValidationError(Error): pass


DEFAULT_TIMEOUT = 60
MSG_BLOCK_SIZE = 4096

# HAX: python 2/3 hack
try:
    basestring
    def _isstr(obj):
        return isinstance(obj, basestring)
except NameError:
    def _isstr(obj):
        return isinstance(obj, str)


def connect(path):
    '''
    Connect to the minimega instance with UNIX socket at <path> and return
    a new minimega API object.
    '''
    return minimega(path)

Command = namedtuple('Command', ['cmd', 'args'])

class SubCommand:
    def __init__(self, mm):
        self.mm = mm


def serializeCommand(command):
    '''
    Returns a string representation of the Command object passed.
    '''
    if not isinstance(command, Command):
        raise TypeError('command must be an instance of Command')
    args = ' '.join(map(str, command.args))
    return '{} {}'.format(command.cmd.shared_prefix, args)


class minimega:
    '''
    This class communicates with a running instance of minimega using a Unix
    domain socket. The protocol is specified here:
    https://code.google.com/p/minimega/wiki/UserGuide#Command_Port_and_the_Local_Command_Flag

    Each minimega command can be called from this object, and the response will
    be returned unless an Exception is thrown.
    '''

    def __init__(self, path, timeout=None):
        '''Connects to the minimega instance with Unix socket at <path>.'''
        self.mm = self
        self._linkCommands(self)
        self.lock = Lock()
        self._debug = False
        self._path = path
        self._timeout = timeout
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.settimeout(timeout if timeout != None else DEFAULT_TIMEOUT)
        self._socket.connect(path)

    def _linkCommands(self, subcommand):
        '''
        Recursively instantiate all subcommand classes and link them with the
        current instance of mm.
        '''
        for name, cmd in inspect.getmembers(subcommand,
                                            predicate=inspect.isclass):
            if name.startswith('_'):
                continue
            setattr(subcommand, name, cmd(self))
            self._linkCommands(getattr(subcommand, name))

    def _reconnect(self):
        try:
            self._socket.close()
        except:
            pass

        self.__init__(self._path, self._timeout)

    def _send(self, cmd, *args):
        msg = json.dumps({'Original': cmd + ' ' + ' '.join(map(str, args))},
                         separators=(',', ':'))
        if self._debug:
            print('[debug] sending cmd: ' + msg)
        with self.lock:
            if len(msg) != self._socket.send(msg.encode('utf-8')):
                raise Error('failed to write message to minimega')

            moreResponses = True
            responses = []
            while moreResponses:
                msg = ''
                more = self._socket.recv(MSG_BLOCK_SIZE).decode('utf-8')
                response = None
                while response is None and more:
                    msg += more
                    try:
                        response = json.loads(msg)
                    except ValueError as e:
                        if self._debug:
                            print(e)
                        more = self._socket.recv(MSG_BLOCK_SIZE).decode('utf-8')

                if not msg:
                    raise Error('Expected response, socket closed')

                if self._debug:
                    print('[debug] response: ' + msg)
                if response['Resp'] and response['Resp'][0]['Error']:
                    raise Error(response['Resp'][0]['Error'])

                responses.extend(response['Resp'])
                moreResponses = response['More']

            return responses

{% for cmd, info in cmds.items() recursive %}
    {% if info.subcommands %}
{{ '    ' * loop.depth }}class {{ cmd }}(SubCommand):
        {{ loop(info.subcommands.items()) }}
    {% else %}
{{ '    ' * loop.depth }}def {{ cmd }}(self, *args):
{{ '    ' * loop.depth }}    '''{{ info.help_long or info.help_short }}'''
{{ '    ' * loop.depth }}    args = list(args)
{{ '    ' * loop.depth }}    #validate the args
{{ '    ' * loop.depth }}    candidates = {{ info.candidates }}
{{ '    ' * loop.depth }}    for candidate in candidates:
{{ '    ' * loop.depth }}        argNum = 0
{{ '    ' * loop.depth }}        try:
{{ '    ' * loop.depth }}            for arg in candidate:
{{ '    ' * loop.depth }}                if arg['type'] == 'stringItem' and not _isstr(args[argNum]):
{{ '    ' * loop.depth }}                    if self.mm._debug:
{{ '    ' * loop.depth }}                        print('expected string for "{}", received {}'.format(arg['text'], type(args[argNum])))
{{ '    ' * loop.depth }}                    break
{{ '    ' * loop.depth }}                if arg['type'] == 'listItem':
{{ '    ' * loop.depth }}                    if not isinstance(args[argNum], list):
{{ '    ' * loop.depth }}                        if self.mm._debug:
{{ '    ' * loop.depth }}                            print('expected list for "{}", received {}'.format(arg['text'], type(args[argNum])))
{{ '    ' * loop.depth }}                        break
{{ '    ' * loop.depth }}                    args[argNum] = ' '.join(map(str, args[argNum]))
{{ '    ' * loop.depth }}                if arg['type'] == 'commandItem':
{{ '    ' * loop.depth }}                    if not isinstance(args[argNum], Command):
{{ '    ' * loop.depth }}                        if self.mm._debug:
{{ '    ' * loop.depth }}                            print('expected Command object for "{}", received {}'.format(arg['text'], type(args[argNum])))
{{ '    ' * loop.depth }}                        break
{{ '    ' * loop.depth }}                    args[argNum] = serializeCommand(args[argNum])
{{ '    ' * loop.depth }}                if arg['type'] == 'choiceItem' and args[argNum] not in arg['options']:
{{ '    ' * loop.depth }}                    if self.mm._debug:
{{ '    ' * loop.depth }}                        print('expected one of "{}" for "{}", received {}'.format(arg['options'], arg['text'], args[argNum]))
{{ '    ' * loop.depth }}                    break
{{ '    ' * loop.depth }}                argNum += 1
{{ '    ' * loop.depth }}        except IndexError:
{{ '    ' * loop.depth }}            if not candidate[argNum]['optional']:
{{ '    ' * loop.depth }}                if self.mm._debug:
{{ '    ' * loop.depth }}                    print('"{}" required but not provided'.format(arg['text']))
{{ '    ' * loop.depth }}                continue #skip to next candidate
{{ '    ' * loop.depth }}        if not args[argNum:]:
{{ '    ' * loop.depth }}            #passed validation, exact match for this candidate
{{ '    ' * loop.depth }}            #if we break in the loop above, argNum doesn't get incremented and args[argNum:] will never be empty, so we don't need a "valid" flag
{{ '    ' * loop.depth }}            return self.mm._send('{{ info.shared_prefix }}', *args)
{{ '    ' * loop.depth }}    raise ValidationError('could not understand command', args)
{{ '    ' * loop.depth }}{{ cmd }}.shared_prefix = '{{ info.shared_prefix }}'
    {% endif %}
{% endfor %}

