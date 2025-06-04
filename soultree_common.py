TYPE_SECTION = 0
TYPE_VALUE = 1
TYPE_OTHER = 2

def read_constsize_str(file, length):
    str_bytes = bytearray(file.read(length))
    for b in range(len(str_bytes)):
      if str_bytes[b] > 126:
        str_bytes[b] = 0
    
    return str_bytes.decode("utf-8").rstrip('\x00')