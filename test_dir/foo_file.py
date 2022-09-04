import math

_str = '17-10'
list_str = list(_str)
first_num = 0
second_num = 0
result = 0

if _str.find('+') != -1:
    #print('+')
    idx = _str.find('+')
    for i in range(idx):
        first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
    for i in range(idx+1, len(list_str)):
        second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
    result = int(first_num + second_num)

elif _str.find('-') != -1:
    #print('-')
    idx = _str.find('-')
    for i in range(idx):
        first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
    for i in range(idx + 1, len(list_str)):
        second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
    result = int(first_num - second_num)

elif _str.find('*') != -1:
    #print('*')
    idx = _str.find('*')
    for i in range(idx):
        first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
    for i in range(idx + 1, len(list_str)):
        second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
    result = int(first_num * second_num)

elif _str.find('/') != -1:
    #print('/')
    idx = _str.find('/')
    for i in range(idx):
        first_num += int(list_str[i]) * math.pow(10, idx - 1 - i)
    for i in range(idx + 1, len(list_str)):
        second_num += int(list_str[i]) * math.pow(10, len(list_str) - 1 - i)
    result = int(first_num / second_num)

print(result)