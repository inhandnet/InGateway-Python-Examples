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
    failed.append((cpppo.timer(), str(exc)))  # On Linux, the best timer is time.time. (cpppo.timer = time.time)


# Process the acquired data
def process(p, v):
    values[p] = (cpppo.timer(), v)


def enip_cpppo_example(args):
    process.done = False
    poller = []
    address = (args[1] if len(args) > 1 else 'localhost', 44818)
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
                    # the .parameter_substitution method deduces that you want one named parameter value.
                    # Provide a sequence of attributes to read more than one.
                    # Transforms bare names by stripping surrounding whitespace, lowering case, and substituting
                    # intervening whitespace with underscores, eg. iterable = ' Output Freq ' --> parameters['output_freq'].

                    # The .write method support writing to CIP Attributes.
                    # If parameters 'checking' is True, an Exception is raised if any erroneous reply status is detected,
                    # even if all operations completed without raising Exception.
                    val, = via.write(via.parameter_substitution(param), checking=True)
                    print("%s: %-32s == %s" % (time.ctime(), param, val))
            except Exception as exc:
                print("Exception writing Parameter: %s, %s", exc, traceback.format_exc())
                failure(exc)
    finally:
        process.done = True
        for p in poller:
            p.join()


if __name__ == '__main__':
    args = sys.argv
    enip_cpppo_example(args)
