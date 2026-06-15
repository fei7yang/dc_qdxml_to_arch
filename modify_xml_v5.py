import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版: 从 backup2 正确重建
1. fnd0_corporateserver: 新增 APP39/40/53-56 (6个, deepcopy from APP01)
2. fnd0_fsc: 新增 APP53-56 (4个, deepcopy from APP40) 
3. fnd0_2tierrichclient: 新增 APP53-56 (4个, 作为 client 元素)
4. aws2_client_gateway_webtier: 新增 APP55/56 (2个, deepcopy from APP41/42)
"""

from lxml import etree
import shutil
from datetime import datetime
from copy import deepcopy

# 自动检测 XML：有参数用参数，否则找脚本所在目录
if len(sys.argv) >= 2:
    INPUT_FILE = os.path.abspath(sys.argv[1])
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _xmls = sorted([f for f in os.listdir(_base) if f.lower().endswith(".xml")])
    if len(_xmls) != 1:
        print(f"用法: python {os.path.basename(__file__)} [XML路径]  或把 .xml 放在脚本目录")
        sys.exit(1)
    INPUT_FILE = os.path.join(_base, _xmls[0])
# 自动检测 XML：有参数用参数，否则找脚本所在目录
if len(sys.argv) >= 2:
    INPUT_FILE = os.path.abspath(sys.argv[1])
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _xmls = sorted([f for f in os.listdir(_base) if f.lower().endswith(".xml")])
    if len(_xmls) != 1:
        print(f"用法: python {os.path.basename(__file__)} [XML路径]  或把 .xml 放在脚本目录")
        sys.exit(1)
    INPUT_FILE = os.path.join(_base, _xmls[0])

def parse_xml(filepath):
    parser = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    return etree.parse(filepath, parser)

def find_by_id_machine(parent, tag, eid, machine):
    for c in parent:
        if c.tag == tag and c.get('id') == eid and c.get('machineName') == machine:
            return c
    return None

def find_last_of(parent, tag, eid):
    last = None
    for c in parent:
        if c.tag == tag and c.get('id') == eid:
            last = c
    return last

def insert_after(parent, ref, new):
    idx = list(parent).index(ref)
    parent.insert(idx + 1, new)

def set_prop(comp, pid, pval):
    for p in comp.findall('property'):
        if p.get('id') == pid:
            p.set('value', pval)
            return p
    return None

def create_corporateserver(qdc, app_name):
    """deepcopy from APP01 corporateserver"""
    tmpl = find_by_id_machine(qdc, 'component', 'fnd0_corporateserver', 'APP01')
    comp = deepcopy(tmpl)
    comp.set('machineName', app_name)
    for ct in comp.findall('connectedTo'):
        if ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
        elif ct.get('component') == 'fnd0_fsc':
            ct.set('machineName', app_name)
    return comp

def create_fsc(qdc, app_name):
    """deepcopy from APP40 FSC"""
    tmpl = find_by_id_machine(qdc, 'component', 'fnd0_fsc', 'APP40')
    comp = deepcopy(tmpl)
    comp.set('machineName', app_name)
    set_prop(comp, 'fnd0_fscHostAlias', app_name)
    set_prop(comp, 'fnd0_fscServerID', f'FSC_{app_name}_infodba')
    set_prop(comp, 'fnd0_fscURL', f'http://{app_name}:4544')
    set_prop(comp, 'fnd0_fscSingleAuthURL', f'http://{app_name}:4545')
    set_prop(comp, 'fnd0_fsc_service', f'Teamcenter FSC Service FSC_{app_name}_infodba')
    return comp

def create_richclient(qcl, app_name):
    """deepcopy from APP44 2tierrichclient (client element)"""
    tmpl = find_by_id_machine(qcl, 'client', 'fnd0_2tierrichclient', 'APP44')
    comp = deepcopy(tmpl)
    comp.set('machineName', app_name)
    # 修改 connectedTo: 连接本地 serverManager 和 corporateserver
    # 先删除旧的 connectedTo
    for ct in list(comp.findall('connectedTo')):
        comp.remove(ct)
    # 添加新的
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_serverManager')
    ct.set('machineName', app_name)
    ct.tail = '\n            '
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_corporateserver')
    ct.set('machineName', app_name)
    ct.tail = '\n            '
    # 同时连接 DB
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_tcdbserver')
    ct.set('machineName', 'DBSCAN')
    ct.tail = '\n        '
    return comp

def create_gateway(qdc, app_name):
    """deepcopy from APP41/42 gateway"""
    if int(app_name[3:]) % 2 == 1:
        tmpl = find_by_id_machine(qdc, 'component', 'aws2_client_gateway_webtier', 'APP41')
    else:
        tmpl = find_by_id_machine(qdc, 'component', 'aws2_client_gateway_webtier', 'APP42')
    comp = deepcopy(tmpl)
    comp.set('machineName', app_name)
    set_prop(comp, 'aws2_client_gateway_HostAlias', app_name)
    set_prop(comp, 'aws2_client_gateway_webtier_url', f'http://{app_name}:3000/')
    
    vis = 'VIS01' if int(app_name[3:]) % 2 == 1 else 'VIS02'
    for ct in comp.findall('connectedTo'):
        if ct.get('component') == 'aws2_vispoolassigner':
            ct.set('machineName', vis)
        elif ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
    
    # 添加新 FSC (APP53-56) 连接
    for fsc_app in ['APP53', 'APP54', 'APP55', 'APP56']:
        ct = etree.SubElement(comp, 'connectedTo')
        ct.set('component', 'fnd0_fsc')
        ct.set('machineName', fsc_app)
        ct.tail = '\n            '
    
    return comp

def main():
    print("=" * 60)
    print("修复: 从 backup2 重建 + 补充组件")
    print("=" * 60)
    
    # 读取 backup2
    print(f"\n读取: {BACKUP_FILE}")
    tree = parse_xml(BACKUP_FILE)
    root = tree.getroot()
    qdc = root.find('quickDeployComponents')
    qcl = root.find('quickDeployClients')
    
    # --- 1. corporateserver ---
    print("\n[1] fnd0_corporateserver (BL Server)")
    last = find_last_of(qdc, 'component', 'fnd0_corporateserver')
    for app in ['APP39', 'APP40', 'APP53', 'APP54', 'APP55', 'APP56']:
        comp = create_corporateserver(qdc, app)
        insert_after(qdc, last, comp)
        last = comp
        print(f"  ✓ {app}")
    
    # --- 2. fnd0_fsc ---
    print("\n[2] fnd0_fsc")
    last = find_last_of(qdc, 'component', 'fnd0_fsc')
    for app in ['APP53', 'APP54', 'APP55', 'APP56']:
        comp = create_fsc(qdc, app)
        insert_after(qdc, last, comp)
        last = comp
        print(f"  ✓ {app}")
    
    # --- 3. fnd0_2tierrichclient (as client!) ---
    print("\n[3] fnd0_2tierrichclient (client元素)")
    last = find_last_of(qcl, 'client', 'fnd0_2tierrichclient')
    for app in ['APP53', 'APP54', 'APP55', 'APP56']:
        comp = create_richclient(qcl, app)
        insert_after(qcl, last, comp)
        last = comp
        print(f"  ✓ {app}")
    
    # --- 4. aws2_client_gateway_webtier ---
    print("\n[4] aws2_client_gateway_webtier")
    last = find_last_of(qdc, 'component', 'aws2_client_gateway_webtier')
    for app in ['APP55', 'APP56']:
        comp = create_gateway(qdc, app)
        insert_after(qdc, last, comp)
        last = comp
        print(f"  ✓ {app}")
    
    # --- 写入到 modified12.xml ---
    print(f"\n[5] 写入: {INPUT_FILE}")
    tree.write(INPUT_FILE, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    
    # 验证
    print("\n=== 验证 ===")
    tree2 = parse_xml(INPUT_FILE)
    from collections import Counter
    
    # Components
    qdc2 = tree2.getroot().find('quickDeployComponents')
    types = Counter()
    for c in qdc2:
        if c.tag == 'component':
            types[c.get('id')] += 1
    print("quickDeployComponents:")
    for t, n in sorted(types.items()):
        print(f"  {t:40s} {n}")
    
    # Clients  
    qcl2 = tree2.getroot().find('quickDeployClients')
    ctypes = Counter()
    for c in qcl2:
        if c.tag == 'client':
            ctypes[c.get('id')] += 1
    print("\nquickDeployClients:")
    for t, n in sorted(ctypes.items()):
        print(f"  {t:40s} {n}")
    
    print("\n✅ 完成!")

if __name__ == '__main__':
    main()
