val = "('a ',   'b')"

val = val.strip('\'\"').replace(' ', '')
is_tuple = False
if val.startswith('(') and val.endswith(')'):
    is_tuple = True
    val = val[1:-1]
elif val.startswith('[') and val.endswith(']'):
    val = val[1:-1]

print(val)