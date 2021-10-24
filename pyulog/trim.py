""" Module with trimming functionality for ULog file"""

import struct
from .core import ULog

__author__ = "Jonathan Hahn"


class _ULogTrim(ULog):

    MAX_READ_BUFFER_SIZE = 512

    def __init__(self):
        self._debug = False

        self._file_corrupt = False

        self._start_timestamp = 0
        self._last_timestamp = 0
        self._msg_info_dict = {}
        self._msg_info_multiple_dict = {}
        self._initial_parameters = {}
        self._default_parameters = {}
        self._changed_parameters = []
        self._message_formats = {}
        self._logged_messages = []
        self._logged_messages_tagged = {}
        self._dropouts = []
        self._data_list = []

        self._subscriptions = {} # dict of key=msg_id, value=_MessageAddLogged
        self._filtered_message_ids = set() # _MessageAddLogged id's that are filtered
        self._missing_message_ids = set() # _MessageAddLogged id's that could not be found
        self._file_version = 0
        self._compat_flags = [0] * 8
        self._incompat_flags = [0] * 8
        self._appended_offsets = [] # file offsets for appended data
        self._has_sync = True # set to false when first file search for sync fails
        self._sync_seq_cnt = 0 # number of sync packets found in file

        ULog._disable_str_exceptions = True

    def trim(self, ulog_in, ulog_out, start_timestamp, end_timestamp):
        """ create trimmed copy of ULog file """

        self._outfile_name = ulog_out

        if isinstance(ulog_in, str):
            with open(ulog_in, 'rb') as log:
                self._file_handle = log
                self._trim(start_timestamp, end_timestamp)
        else:
            # assuming file
            self._file_handle = ulog_in
            self._trim(start_timestamp, end_timestamp)


    def _trim(self, start_timestamp, end_timestamp):
        self._read_file_header()
        self._read_file_definitions()

        with open(self._outfile_name, 'wb') as self._outfile:
            self._copy_header(start=0, end=self._file_handle.tell(), start_ts=start_timestamp)

            header = self._MessageHeader()
            msg_data = self._MessageData()

            while True:
                header_data = self._file_handle.read(3)

                if not header_data:
                    break

                header.initialize(header_data)

                data = self._file_handle.read(header.msg_size)

                if len(data) < header.msg_size:
                    break # probably out of data

                if header.msg_type == self.MSG_TYPE_ADD_LOGGED_MSG:
                    msg_add_logged = self._MessageAddLogged(data, header,
                                                            self._message_formats)

                    self._subscriptions[msg_add_logged.msg_id] = msg_add_logged
                elif header.msg_type == self.MSG_TYPE_DATA:
                    try:
                        msg_data.initialize(data, header, self._subscriptions, self)
                    except:
                        break
                    if msg_data.timestamp / 1e6 < start_timestamp:
                        continue                
                    elif msg_data.timestamp / 1e6 > end_timestamp:
                        break

                self._outfile.write(header_data)
                self._outfile.write(data)

    def _copy_header(self, start, end, start_ts):
        reader_pos = self._file_handle.tell()

        bytes_to_read = end-start

        self._file_handle.seek(start)

        buffer = self._file_handle.read(bytes_to_read)

        buffer = buffer[:8] + struct.pack("<Q", start_ts*1000000) + buffer[16:]
        
        self._outfile.write(buffer)

        self._file_handle.seek(reader_pos)


def trim(ulog_in, ulog_out, start, end):
    ulg = _ULogTrim()
    ulg.trim(ulog_in, ulog_out, start, end)


def main():
    trim('test/test.ulg', 'test/output.ulg', 0, 10000000)
