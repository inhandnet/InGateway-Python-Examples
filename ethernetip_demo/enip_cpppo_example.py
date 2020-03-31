#! /usr/bin/env python

# Poll a ControlLogix at IP (or DNS name) "<hostname>" (default: localhost)
#
# Multiple Threads are used to poll at differing rates, with occasional writes, all
# using to the same cpppo.server.enip.get_attribute 'proxy' instance.


from cpppo.server.enip.get_attribute import proxy as device  # ControlLogix
from cpppo.server.enip import poll
import logging
import random
import sys
import time
import threading
import traceback

import cpppo
logging.basicConfig(**cpppo.log_cfg)

address = (sys.argv[1] if len(sys.argv) > 1 else 'localhost', 44818)
# Set rate and point information
targets = {
    1.0: ['INHAND:O.Data[0-3]', 'T3'],
    5.0: ['INHAND:I.Data[0-3]', 'T1', 'T2'],
}   # format: { <rate>: [<symbol>, <@class/instance/attribute>, ...], ... }

timeout = .5
values = {}  # format: { <parameter>: (<timer>, <value>), ... }
failed = []  # format: [ (<timer>, <exc>), ... ]


# Capture a timestamp with each event
def failure(exc):
    failed.append((cpppo.timer(), str(exc)))


# Process the acquired data
def process(p, v):
    values[p] = (cpppo.timer(), v)


process.done = False
poller = []
# Initialize an EtherNet/IP CIP proxy instance
via = device(host=address[0], port=address[1], timeout=timeout)
# Start polling thread
for cycle, params in targets.items():
    poller += [threading.Thread(target=poll.run, kwargs={
        'via': via,
        'cycle': cycle,
        'process': process,
        'failure': failure,
        'params': params,
    })]
    poller[-1].start()

# Monitor the values and failed containers (updated in another Thread)
try:
    while True:
        # Get the data read by the thread
        while values:
            par, (tmr, val) = values.popitem()
            print("%s: %-32s == %r" % (time.ctime(tmr), par, val))
        # Thread exception print
        while failed:
            tmr, exc = failed.pop(0)
            print("%s: %s" % (time.ctime(tmr), exc))
        time.sleep(.1)
        # Write parameter
        try:
            # Write a random data to T3
            param = 'T3 = (DINT)%s' % (random.randint(0, 100))  # format: '<symbol>=(<data type>)<value>'
            with via:  # Establish gateway, detects Exception (closing gateway)
                val, = via.write(via.parameter_substitution(param), checking=True)
                print("%s: %-32s == %s" % (time.ctime(), param, val))
        except Exception as exc:
            print("Exception writing Parameter: %s, %s", exc, traceback.format_exc())
            failure(exc)
finally:
    process.done = True
    for p in poller:
        p.join()
