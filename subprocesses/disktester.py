import time
import multiprocessing
import logging
import os
import mmap
from utilities.random_string_generator import id_generator


def open_file_with_random_name():
    # Open in O_DIRECT mode to try to more accurately asses the performance of the disk rather than OS buffering
    filename = id_generator(8)
    f = os.open(filename, os.O_CREAT | os.O_DIRECT | os.O_WRONLY | os.O_APPEND)
    return f



def disk_tester(msgs, logger, arguments):

    one_mebibyte = 2 ** 20

    # Create a 1 MiB 512k-aligned memory buffer with random bytes to be used to write to storage
    m = mmap.mmap(-1, one_mebibyte)
    m.write(os.urandom(one_mebibyte))

    t = time.time() + arguments.test_duration

    file_rollovers = 0
    chunk_size = arguments.write_chunk_size * one_mebibyte
    max_file_size = arguments.max_file_size * one_mebibyte


    f = open_file_with_random_name()
    bytes_remaining_in_file = max_file_size

    while True:
        #logger.debug('testing')
        if msgs.poll() is True:
            msg = msgs.recv()
            if msg and msg[0] == 'stop':
                break

        if time.time() > t and file_rollovers > 2:
            break

        size_of_this_chunk = min(chunk_size, bytes_remaining_in_file)

        bytes_remaining_in_chunk = size_of_this_chunk
        while bytes_remaining_in_chunk:
            #num = os.write(f, m[:min(bytes_remaining, one_mebibyte)])
            num = os.write(f, m)
            bytes_remaining_in_chunk -= num
            bytes_remaining_in_file -= num

        if bytes_remaining_in_file <= 0:
            os.close(f)
            f = open_file_with_random_name()
            file_rollovers += 1
            bytes_remaining_in_file = max_file_size


    os.close(f)

    msgs.send(('test_completed',))
    msg = msgs.recv()