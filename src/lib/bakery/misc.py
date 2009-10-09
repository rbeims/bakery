from __future__ import with_statement # This isn't required in Python 2.6

def get_simple_config_line(filename, variable):
    if os.path.exists(filename):
        regex = re.compile(variable +'\s*=\s*[\"\'](.*)[\"\']')
        with open(filename) as file:
            for line in file.readlines():
                match = regex.match(line)
                if match:
                    return match.group(1)
    return None


def version_str_to_tuple(str):
    dash = str.rfind('-')
    if dash >= 0:
        str = str[dash+1:]
    list = string.split(str, '.')
    tuple = ()
    for number in list:
        tuple = tuple + (int(number),)
    return tuple
