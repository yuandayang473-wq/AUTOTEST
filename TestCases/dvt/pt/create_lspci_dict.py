import os 
import re
import time


from json import dumps
reports_path = os.path.split(os.path.realpath(__file__))[0] 
def fopen(file='', content='', mode='r', json=False, path=None):
    '''
    description: read or write file
    author: zhuang zhao
    params: file, the file want to operate.
            content, the msg that want to be written to file.
            mode, the open file mode, choose from [r, w, a]
            json, use when deal json date, choices:[True, False]
    return: data, the file's reading date
    '''
    # transfer dat file to dat_dict
    now = time.strftime("%a %b %d %H:%M:%S %Y",time.localtime())
    data = ''
    if path == None:
        file = reports_path + '/' +file
    else:
        file = path + '/' + file
    f = open(file, mode, encoding='UTF-8')
    if mode == 'w' or mode == 'a':
        if json:
            f.write(dumps(content, indent=4, sort_keys=False) + '\n')
        else:
            f.write(now + " : " + content + "\n")
    else:
        if json:
            data = eval(f.read())
        else:
            data = f.read()
    f.close()
    return data


dict_list = {}
cmd = " lspci"
output = os.popen(cmd).read().strip().split('\n')
print(output)
for info in output:
    dict_info = {}
    id = info.split(" ")[0]
    # dict_info["busid"] = id
    cmd = f"lspci -s {id} -vvv  "
    pci_info = os.popen(cmd).read()
    output = re.findall(f"{id}.*", pci_info, re.I)[0]
    name = output.split(': ')[0]
    dict_info["name"] = name
    lnkcap = re.findall(f"LnkCap:.*", pci_info, re.I)
    if lnkcap:
        dict_info["lnkcap"] = lnkcap[0].split(":\t")[1]
    lnksta = re.findall(f"LnkSta:.*", pci_info, re.I)
    if lnksta:
        dict_info["lnksta"] = lnksta[0].split(":\t")[1]
    uesta = re.findall(f"UESta:.*", pci_info, re.I)
    if uesta:
        dict_info["uesta"] = uesta[0].split(":\t")[1]
    cesta = re.findall(f"CESta:.*", pci_info, re.I)
    if cesta:
        dict_info["cesta"] = cesta[0].split(":\t")[1]
    dict_list[id] = dict_info
print(dict_list)
fopen("lspci.json", dict_list, 'w', True)
