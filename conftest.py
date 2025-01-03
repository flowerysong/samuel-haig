#!/usr/bin/env python3

import datetime
import errno
import json
import os
import smtplib
import socket
import subprocess
import sys
import time

import pytest

def openport(port):
    # Find a usable port by iterating until there's an unconnectable port
    while True:
        try:
            socket.create_connection(('localhost', port), 0.1)
            port += 1
            if port > 65535:
                raise ValueError("exhausted TCP port range without finding a free one")
        except socket.error:
            return port


@pytest.fixture(scope="session")
def dnsserver(tmp_path_factory):
    port = openport(10053)

    tmpdir = tmp_path_factory.mktemp('yadifa')
    for subdir in ['keys', 'log', 'xfr']:
        tmpdir.joinpath(subdir).mkdir()

    conf = str(tmpdir.joinpath('yadifad.conf'))
    datadir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dns')

    with open(conf, 'w') as f:
        f.write('<main>\n')
        f.write('    port {}\n'.format(port))
        f.write('    pidfile {}\n'.format(os.path.join(tmpdir, 'pid')))
        f.write('    datapath {}\n'.format(datadir))
        f.write('    keyspath {}\n'.format(os.path.join(tmpdir, 'keys')))
        f.write('    logpath {}\n'.format(os.path.join(tmpdir, 'log')))
        f.write('    xfrpath {}\n'.format(os.path.join(tmpdir, 'xfr')))
        f.write('</main>\n')
        f.write('<zone>\n')
        f.write('    domain test\n')
        f.write('    file test.zone\n')
        f.write('    type master\n')
        f.write('</zone>\n')
        f.write('<zone>\n')
        f.write('    domain arpa\n')
        f.write('    file arpa.zone\n')
        f.write('    type master\n')
        f.write('</zone>\n')
        f.write('<zone>\n')
        f.write('    domain example.com\n')
        f.write('    file example.com.zone\n')
        f.write('    type master\n')
        f.write('</zone>\n')
        f.write('<zone>\n')
        f.write('    domain example.edu\n')
        f.write('    file example.edu.zone\n')
        f.write('    type master\n')
        f.write('</zone>\n')

    result = {
        'enabled': True,
        'port': port,
    }

    devnull = open(os.devnull, 'w')
    dns_proc = None
    try:
        dns_proc = subprocess.Popen(['yadifad', '-c', conf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        result['enabled'] = False
        result['skip_reason'] = 'yadifad not found'

    yield result

    if dns_proc:
        dns_proc.terminate()
        raise Exception(str(dns_proc.stderr.readlines()))


@pytest.fixture
def req_dnsserver(dnsserver):
    if not dnsserver['enabled']:
        pytest.skip(dnsserver['skip_reason'])
