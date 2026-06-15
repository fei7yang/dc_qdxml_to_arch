import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 backup2 干净重建 — 所有新增都用 lxml insert_after 保持在正确组内
- FSC APP53-56 (4), Gateway APP55-56 (2), 2tierrichclient APP53-56 (4), blserver APP53-56 (4)
- 全连接更新: servermgrconsole/microservice/dispatcherModule
- NO extra corps
"""

from lxml import etree
from copy import deepcopy
import shutil

# 自动检测 XML：有参数用参数，否则找脚本所在目录
if len(sys.argv) >= 2:
    INPUT = os.path.abspath(sys.argv[1])
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _xmls = sorted([f for f in os.listdir(_base) if f.lower().endswith(".xml")])
    if len(_xmls) != 1:
        print(f"用法: python {os.path.basename(__file__)} [XML路径]  或把 .xml 放在脚本目录")
        sys.exit(1)
    INPUT = os.path.join(_base, _xmls[0])

def parse_xml(fp):
    p = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    return etree.parse(fp, p)

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

def create_fsc(qdc, app_name):
    tmpl = None
    for c in qdc:
        if c.tag == 'component' and c.get('id') == 'fnd0_fsc' and c.get('machineName') == 'APP40':
            tmpl = deepcopy(c); break
    if tmpl is None: return None
    tmpl.set('machineName', app_name)
    set_prop(tmpl, 'fnd0_fscHostAlias', app_name)
    set_prop(tmpl, 'fnd0_fscServerID', f'FSC_{app_name}_infodba')
    set_prop(tmpl, 'fnd0_fscURL', f'http://{app_name}:4544')
    set_prop(tmpl, 'fnd0_fscSingleAuthURL', f'http://{app_name}:4545')
    set_prop(tmpl, 'fnd0_fsc_service', f'Teamcenter FSC Service FSC_{app_name}_infodba')
    return tmpl

def create_gateway(qdc, app_name):
    num = int(app_name[3:])
    tmpl_machine = 'APP41' if num % 2 == 1 else 'APP42'
    tmpl = None
    for c in qdc:
        if c.tag == 'component' and c.get('id') == 'aws2_client_gateway_webtier' and c.get('machineName') == tmpl_machine:
            tmpl = deepcopy(c); break
    if tmpl is None: return None
    tmpl.set('machineName', app_name)
    set_prop(tmpl, 'aws2_client_gateway_HostAlias', app_name)
    set_prop(tmpl, 'aws2_client_gateway_webtier_url', f'http://{app_name}:3000/')
    vis = 'VIS01' if num % 2 == 1 else 'VIS02'
    for ct in tmpl.findall('connectedTo'):
        if ct.get('component') == 'aws2_vispoolassigner':
            ct.set('machineName', vis)
        elif ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
    # 加新FSC连接
    for fsc_app in ['APP53', 'APP54', 'APP55', 'APP56']:
        ct = etree.Element('connectedTo')
        ct.set('component', 'fnd0_fsc')
        ct.set('machineName', fsc_app)
        ct.tail = '\n            '
        tmpl.append(ct)
    return tmpl

def create_richclient(qcl, app_name):
    tmpl = None
    for c in qcl:
        if c.tag == 'client' and c.get('id') == 'fnd0_2tierrichclient' and c.get('machineName') == 'APP44':
            tmpl = deepcopy(c); break
    if tmpl is None: return None
    tmpl.set('machineName', app_name)
    # 在已有connectedTo前插入新连接
    old_ct = tmpl.find('connectedTo')
    if old_ct is not None:
        ct1 = etree.Element('connectedTo')
        ct1.set('component', 'fnd0_serverManager')
        ct1.set('machineName', app_name)
        ct1.tail = '\n            '
        old_ct.addprevious(ct1)
        ct2 = etree.Element('connectedTo')
        ct2.set('component', 'fnd0_corporateserver')
        ct2.set('machineName', app_name)
        ct2.tail = '\n            '
        old_ct.addprevious(ct2)
    return tmpl

def create_blserver(qcl, app_name):
    tmpl = None
    for c in qcl:
        if c.tag == 'client' and c.get('id') == 'fnd0_blserver' and c.get('machineName') == 'APP40':
            tmpl = deepcopy(c); break
    if tmpl is None: return None
    tmpl.set('machineName', app_name)
    for ct in tmpl.findall('connectedTo'):
        if ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
    return tmpl

def add_full_connection(comp, comp_type, machine, count):
    """在comp内最后一个connectedTo后插入"""
    cts = comp.findall('connectedTo')
    last_ct = cts[-1] if cts else None
    if last_ct is not None:
        for i in range(53, 57):
            ct = etree.Element('connectedTo')
            ct.set('component', comp_type)
            ct.set('machineName', f'APP{i:02d}')
            ct.tail = '\n            '
            last_ct.addnext(ct)
            last_ct = ct
        return f'+{count} {comp_type}'
    return None

def main():
    print("=" * 60)
    print("从 backup2 干净重建")
    print("=" * 60)
    
    # 备份
    shutil.copy2(INPUT, INPUT.replace('.xml', '_fixbackup.xml'))
    
    tree = parse_xml(INPUT)
    root = tree.getroot()
    qdc = root.find('quickDeployComponents')
    qcl = root.find('quickDeployClients')
    
    # ===== 1. FSC (在 fnd0_fsc 组内) =====
    print("\n[1] FSC APP53-56")
    last_fsc = find_last_of(qdc, 'component', 'fnd0_fsc')
    for app in ['APP53','APP54','APP55','APP56']:
        comp = create_fsc(qdc, app)
        insert_after(qdc, last_fsc, comp)
        last_fsc = comp
        print(f"  ✓ {app}")
    
    # ===== 2. Gateway (在 aws2_client_gateway_webtier 组内) =====
    print("\n[2] Gateway APP55-56")
    last_gw = find_last_of(qdc, 'component', 'aws2_client_gateway_webtier')
    for app in ['APP55','APP56']:
        comp = create_gateway(qdc, app)
        insert_after(qdc, last_gw, comp)
        last_gw = comp
        print(f"  ✓ {app}")
    
    # ===== 3. 2tierrichclient (在 clients 中) =====
    print("\n[3] 2tierrichclient APP53-56")
    last_rich = find_last_of(qcl, 'client', 'fnd0_2tierrichclient')
    for app in ['APP53','APP54','APP55','APP56']:
        comp = create_richclient(qcl, app)
        insert_after(qcl, last_rich, comp)
        last_rich = comp
        print(f"  ✓ {app}")
    
    # ===== 4. blserver (在 clients 中) =====
    print("\n[4] blserver APP53-56")
    last_bls = find_last_of(qcl, 'client', 'fnd0_blserver')
    for app in ['APP53','APP54','APP55','APP56']:
        comp = create_blserver(qcl, app)
        insert_after(qcl, last_bls, comp)
        last_bls = comp
        print(f"  ✓ {app}")
    
    # ===== 5. 全连接更新 =====
    print("\n[5] 全连接更新")
    for cid, machine, ctype in [
        ('fnd0_servermgrconsole', 'APP01', 'fnd0_serverManager'),
        ('fnd0_servermgrconsole', 'APP01', 'fnd0_j2ee_tcwebtier'),
        ('fnd0_microservice', 'MSF01', 'fnd0_j2ee_tcwebtier'),
        ('fnd0_dispatcherModule', 'DISP01', 'fnd0_j2ee_tcwebtier'),
        ('fnd0_dispatcherModule', 'DISP02', 'fnd0_j2ee_tcwebtier'),
    ]:
        for c in qdc:
            if c.tag == 'component' and c.get('id') == cid and c.get('machineName') == machine:
                result = add_full_connection(c, ctype, machine, 4)
                if result:
                    print(f"  ✓ {cid} {machine} {result}")
                break
    
    # ===== 写入 =====
    print("\n[6] 写入...")
    tree.write(INPUT, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    print("✅ 完成!")

if __name__ == '__main__':
    main()
