"""A set of socket wrappers to support various modes of reading/writing.

Classes:
Int32Socket -- A socket wrapper for in32 prefixed strings
LineSocket -- A socket wrapper for CRLF terminated strings
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import socket
import struct

class Int32Socket(object):
    """A wrapper for a socket that reads/writes int32 prefixed strings.
    
    This sends and receives strings over a socket, prefixing them with 
    a 4 byte integer specifying the length of the string.  This 4 byte
    integer is encoded in network byte order.
    
    Notes:
    
    - If extra data is received by this class it is discarded.
    - This class might work with blocking/timeout'd sockets.
    - No socket related exceptions are caught.
    """
    
    MAX_LENGTH = 99999999
    
    def __init__(self,sock):
        """Wrap a socket object for int32 prefixed reading/writing.
        
        The wrapped socket must be setup already.
        """
        self.sock = sock
        self.remainder = ''
        
    def write_string(self,data):
        """Writes data to the socket.
        
        Notes:
        - This method uses buffers so substrings are not copied.
        - No errors are caught currently.
        """
        prefix = struct.pack("!i",len(data))
        
        offset = 0
        lengthToSend = len(prefix)
        while offset < lengthToSend:
            slice = buffer(prefix, offset, lengthToSend - offset)
            amountWritten = self.sock.send(slice)
            offset += amountWritten

        offset = 0
        lengthToSend = len(data)
        while offset < lengthToSend:
            slice = buffer(data, offset, lengthToSend - offset)
            amountWritten = self.sock.send(slice)
            offset += amountWritten
        
    def read_string(self, size=2048):
        """Reads an int32 prefixed string from the socket.
        
        THIS IS BROKEN RIGHT NOW!!
        
        Notes"
        - If there is an error, an error message is printed and
          an empty string is returned.  Change over to using exceptions.
        - The received data is stored in a list to avoid copying strings.
        - No socket related errors are caught currently.
        """
        recvd = self.remainder # From the last read_string call
        
        # Read until we have at least 4 bytes
        while len(recvd) < 4:
            buf = self.sock.recv(size)
            recvd = recvd + buf
            
        # Compute the length, extract the rest back into recvd
        total, = struct.unpack("!i",recvd[:4])
        recvd = [recvd[4:]]
        soFar = len(recvd[0])
        if total > self.MAX_LENGTH:
            print "Too large a message"
            return ""
            
        # Now read the rest, discarding any extra
        while soFar < total:
            buf = self.sock.recv(size)
            justRecvd = len(buf)
            if justRecvd == 0:
                print "Not all bytes came through."
                return ""
            else:
                recvd.append(buf)
                soFar = soFar + justRecvd
        
            
        if justRecvd + soFar > total:
            leftover = (justRecvd + soFar) - total
            recvd.append(buf[:-leftover])   
            
        return "".join(recvd)
          
    def write_string_slow(self,data):
        """Writes data to the socket.
        
        Notes:
        - Uses sendall so it won't work with timeouts or non-blocking sockets.
        """
        self.sock.sendall(struct.pack("!i",len(data)))
        self.sock.sendall(data)

    def read_string_slow(self, size=2048):
        """Reads an int32 prefixed string from the socket.
        
        If there is an error, an error message is printed and
        an empty string is returned.  Change over to using exceptions.
        """
        recvd = ""
        
        # Read until we have at least 4 bytes
        while len(recvd) < 4: 
            buf = self.sock.recv(size)
            recvd = recvd + buf
            
        # Compute the length, extract the rest back into recvd
        total, = struct.unpack("!i",recvd[:4])
        recvd = recvd[4:]
        soFar = len(recvd)
        if total > self.MAX_LENGTH:
            print "Too large a message"
            return ""
            
        # Now read the rest, discarding any extra
        while soFar < total:
            buf = self.sock.recv(size)
            justRecvd = len(buf)
            if justRecvd == 0:
                print "Not all bytes came through."
                return ""
            if justRecvd + soFar > total:
                leftover = (justRecvd + soFar) - total
                recvd = recvd + buf[:-leftover]
            else:
                recvd = recvd + buf
            soFar = soFar + justRecvd
            
        return recvd
   
class LineSocket(object):
    """A socket wrapper to read and write terminated lines.
    
    I need to add the capability to handle timeouts.
    """

    delimeter = '\r\n'

    def __init__(self, sock):
        self.sock = sock
        
    def read_line(self, extra="", size=8192):
        buf = extra
        new_extra = ""
        found = False
        
        # See if extra already has a line
        offset = buf.find(self.delimeter)
        if not offset == -1:
            line = buf[:offset]
            new_extra = buf[offset+len(self.delimeter):]
            found = True
        
        # Read until you find a line
        while not found:
            data = self.sock.recv(size)
            buf = buf + data
            offset = buf.find(self.delimeter)
            if not offset == -1:
                line = buf[:offset]
                new_extra = buf[offset+len(self.delimeter):]
                found = True
                
        return (line, new_extra)
        
    def write_line(self, line):
        self.sock.sendall(line + self.delimeter)

    def read_bytes(self, bytes, extra='', size=8192):
        """Read a certain number of bytes.
        
        This doesn't handle timeouts yet.
        """
        buf = []
        new_extra = ''
        if extra:
            buf.append(extra)
        sofar = len(extra)
        
        while sofar < bytes:
            data = self.sock.recv(size)
            thistime = len(data)
            if thistime > 0:
                sofar += thistime
                buf.append(data)
            else:
                print "Socket closed unexpectedly"
                return ""
                
        if sofar > bytes:
            leftover = sofar - bytes
            new_extra = buf[-1][-leftover:]
            buf[-1] = buf[-1][:-leftover]

        return "".join(buf), new_extra
        
    def write_bytes(self, data):
        self.sock.sendall(data)
                            
def testesocket(times, length):
    print "Total bytes to send = ", times*length*4 
    for t in range(times):
        #print "Running time: ", t+1
        s = socket.socket()
        s.connect(('trestles.scu.edu',10000))
        es = Int32Socket(s)
        es.writeString(length*'a')
        result = es.readString()
        
        