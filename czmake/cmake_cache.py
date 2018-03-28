class ParseError(Exception):
    """Exception raised for errors during parse.

    Attributes:
        line -- number of the line that caused the error
        message -- explanation of the error
    """

    def __init__(self, line, message):
        self.line = line
        self.message = message

    def __repr__(self):
        return 'Error at line %d: %s' % (self.line, self.message)

class CMakeCache(dict):
    
    falsy_values = ['', '0', 'OFF', 'NO', 'FALSE', 'N', 'IGNORE', 'NOTFOUND']

    @staticmethod
    def to_bool(val):
        val = val.upper()
        for ref in CMakeCache.falsy_values:
            if ref == val:
                return False
        else:
            if val.endswith('NOTFOUND'):
                return False
            else:
                return True         

    def get(self, key, default):
        if key in self:
            if isinstance(default, bool):
                return CMakeCache.to_bool(self[key])
            else:
                return self[key]
        else:
            return default

# def parse_cache(cmake_cache_file):
#     result = CMakeCache()
#     line_index = 0
#     for line in cmake_cache_file:
#         line = line.strip()
#         if len(line) and line[0] != '#' and line[:2] != '//':
#             type_begin = line.find(':')
#             if type_begin < 0:
#                 raise ParseError(line_index, 'Cannot parse entry type')
#             type_end = line.find('=')
#             if type_end < 0:
#                 raise ParseError(line_index, 'Cannot parse entry value')
#             t = line[type_begin+1:type_end]
#             value = line[type_end+1:]
#             if t == 'BOOL':
#                 value = True if value in CMakeCache.truthy_values else False
#             result[line[:type_begin]] = (value, t)
#     return result

def read_cache(cmake_cache_file):
    result = CMakeCache()
    line_index = 0
    for line in cmake_cache_file:
        index = line.find(' = ')
        if index < 0:
            print(line)
            raise ParseError(line_index, 'Cannot parse entry') 
        key, value = line[:index], line[index+3:-1]
        result[key] = value
        line_index += 1
    return result

            