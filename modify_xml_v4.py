import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 quick-deploy.xml — 补充 BL Server / FSC / 2tierrichclient / gateway
1. fnd0_corporateserver: 新增 APP39/40/53/54/55/56 (6个)
2. fnd0_fsc: 新增 APP53/54/55/56 (4个), APP39/40已有不改造
3. fnd0_2tierrichclient: 新增 APP53/54/55/56 (4个)
4. aws2_client_gateway_webtier: 新增 APP55/56 (2个)
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

def parse_xml(filepath):
    parser = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    return etree.parse(filepath, parser)

def find_component_by_machine(qdc, ctype, machine):
    for c in qdc:
        if c.tag == 'component' and c.get('id') == ctype and c.get('machineName') == machine:
            return c
    return None

def find_last_of_type(qdc, ctype):
    """找到指定类型的最后一个 component"""
    last = None
    for c in qdc:
        if c.tag == 'component' and c.get('id') == ctype:
            last = c
    return last

def insert_after(qdc, ref_comp, new_comp):
    """在 ref_comp 后插入 new_comp"""
    idx = list(qdc).index(ref_comp)
    qdc.insert(idx + 1, new_comp)

def set_property(comp, pid, pval):
    for p in comp.findall('property'):
        if p.get('id') == pid:
            p.set('value', pval)
            return p
    return None

# ===== 1. fnd0_corporateserver (BL Server) =====
def create_corporateserver(qdc, app_name):
    """基于 APP01 模板创建 corporateserver"""
    template = find_component_by_machine(qdc, 'fnd0_corporateserver', 'APP01')
    if template is None:
        print(f"  ✗ 找不到模板!")
        return None
    
    comp = deepcopy(template)
    comp.set('machineName', app_name)
    
    # 修改关键属性
    set_property(comp, 'fnd0_tcCorporateServerInstallationPath', 
                 r'D:\PLM\Siemens\Teamcenter2512\tc_root')
    set_property(comp, 'fnd0_tcDataPath', r'D:\PLM\Siemens\Teamcenter2512\tc_data')
    
    # 修改 connectedTo: fnd0_j2ee_tcwebtier 指向本地
    for ct in comp.findall('connectedTo'):
        if ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
        # FSC 连接指向本地 FSC
        elif ct.get('component') == 'fnd0_fsc':
            ct.set('machineName', app_name)
    
    return comp

# ===== 2. fnd0_fsc =====
def create_fsc(qdc, app_name):
    """基于 APP40 模板创建 FSC"""
    template = find_component_by_machine(qdc, 'fnd0_fsc', 'APP40')
    if template is None:
        print(f"  ✗ 找不到 FSC 模板!")
        return None
    
    comp = deepcopy(template)
    comp.set('machineName', app_name)
    
    # 修改机器特定属性
    num = app_name[3:]
    set_property(comp, 'fnd0_fscHostAlias', app_name)
    set_property(comp, 'fnd0_fscServerID', f'FSC_{app_name}_infodba')
    set_property(comp, 'fnd0_fscURL', f'http://{app_name}:4544')
    set_property(comp, 'fnd0_fscSingleAuthURL', f'http://{app_name}:4545')
    set_property(comp, 'fnd0_fsc_service', f'Teamcenter FSC Service FSC_{app_name}_infodba')
    
    return comp

# ===== 3. fnd0_2tierrichclient =====
def create_2tierrichclient(app_name):
    """创建 2-tier Rich Client 组件"""
    ns = 'http://www.w3.org/XML/1998/namespace'
    comp = etree.Element('component')
    comp.set('id', 'fnd0_2tierrichclient')
    comp.set('machineName', app_name)
    comp.set('platform', 'wntx64')
    comp.set('deploymentStatus', 'Pending Install')
    
    props = {
        'fnd0_2tierrichclientInstallationPath': r'D:\PLM\Siemens\Teamcenter2512\tc_root\portal\richclient',
        'fnd0_2tierrichclient_installType': 'Full',
        'fnd0_2TIERRICHCLIENT_TC_DATA_DIR': r'D:\PLM\Siemens\Teamcenter2512\tc_data',
        'fnd0_2TIERRICHCLIENT_TC_ROOT_DIR': r'D:\PLM\Siemens\Teamcenter2512\tc_root',
        'fnd0_clientArchitecture': 'wntx64',
        'fnd0_osUserOptions': 'thisAccount',
        'fnd0_2tierrichclient_machineUser': r'.\infodba',
        'fnd0_2tierrichclient_machinePassword': 'VuZeYRVHbwBt2q7ieWb20PBsHYTEkR2hpclHKKLssaE17Fa8wzzd+dUTCvniU29V',
    }
    
    for pid, pval in props.items():
        p = etree.SubElement(comp, 'property')
        p.set('id', pid)
        p.set('value', pval)
    
    # 连接
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_serverManager')
    ct.set('machineName', app_name)
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_corporateserver')
    ct.set('machineName', app_name)
    
    return comp

# ===== 4. aws2_client_gateway_webtier =====
def create_gateway_webtier(qdc, app_name):
    """基于 APP41 模板创建 gateway webtier"""
    if int(app_name[3:]) % 2 == 1:
        template = find_component_by_machine(qdc, 'aws2_client_gateway_webtier', 'APP41')
    else:
        template = find_component_by_machine(qdc, 'aws2_client_gateway_webtier', 'APP42')
    
    if template is None:
        print(f"  ✗ 找不到 gateway 模板!")
        return None
    
    comp = deepcopy(template)
    comp.set('machineName', app_name)
    
    # 修改属性
    set_property(comp, 'aws2_client_gateway_HostAlias', app_name)
    set_property(comp, 'aws2_client_gateway_webtier_url', f'http://{app_name}:3000/')
    
    # 修改 VIS 连接 (奇偶配对)
    vis_target = 'VIS01' if int(app_name[3:]) % 2 == 1 else 'VIS02'
    for ct in comp.findall('connectedTo'):
        if ct.get('component') == 'aws2_vispoolassigner':
            ct.set('machineName', vis_target)
        elif ct.get('component') == 'fnd0_j2ee_tcwebtier':
            ct.set('machineName', app_name)
    
    # 添加新 FSC 的连接 (APP53-56)
    for new_fsc in ['APP53', 'APP54', 'APP55', 'APP56']:
        ct = etree.SubElement(comp, 'connectedTo')
        ct.set('component', 'fnd0_fsc')
        ct.set('machineName', new_fsc)
    
    return comp

def main():
    print("=" * 60)
    print(f"修改 {INPUT_FILE} — 补充组件")
    print("=" * 60)
    
    # 备份
    backup = INPUT_FILE.replace('.xml', f'_backup2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml')
    shutil.copy2(INPUT_FILE, backup)
    print(f"\n备份: {backup}")
    
    tree = parse_xml(INPUT_FILE)
    root = tree.getroot()
    qdc = root.find('quickDeployComponents')
    
    changes = 0
    
    # --- 1. corporateserver ---
    print("\n[1] fnd0_corporateserver (BL Server)")
    cs_apps = ['APP39', 'APP40', 'APP53', 'APP54', 'APP55', 'APP56']
    last_cs = find_last_of_type(qdc, 'fnd0_corporateserver')
    if last_cs is None:
        print("  ✗ 找不到现有 corporateserver!")
    else:
        for app in cs_apps:
            comp = create_corporateserver(qdc, app)
            if comp:
                insert_after(qdc, last_cs, comp)
                last_cs = comp
                print(f"  ✓ {app}")
                changes += 1
    
    # --- 2. fnd0_fsc ---
    print("\n[2] fnd0_fsc")
    fsc_apps = ['APP53', 'APP54', 'APP55', 'APP56']
    last_fsc = find_last_of_type(qdc, 'fnd0_fsc')
    if last_fsc:
        for app in fsc_apps:
            comp = create_fsc(qdc, app)
            if comp:
                insert_after(qdc, last_fsc, comp)
                last_fsc = comp
                print(f"  ✓ {app}")
                changes += 1
    
    # --- 3. fnd0_2tierrichclient ---
    print("\n[3] fnd0_2tierrichclient")
    rich_apps = ['APP53', 'APP54', 'APP55', 'APP56']
    # 找到合适的插入位置 (在 fnd0_schdmgmt 后或类似位置)
    # 由于这是新类型, 插在最后一个 component 之前
    last_any = list(qdc)[-1]
    for app in rich_apps:
        comp = create_2tierrichclient(app)
        insert_after(qdc, last_any, comp)
        last_any = comp
        print(f"  ✓ {app}")
        changes += 1
    
    # --- 4. aws2_client_gateway_webtier ---
    print("\n[4] aws2_client_gateway_webtier")
    gw_apps = ['APP55', 'APP56']
    last_gw = find_last_of_type(qdc, 'aws2_client_gateway_webtier')
    if last_gw:
        for app in gw_apps:
            comp = create_gateway_webtier(qdc, app)
            if comp:
                insert_after(qdc, last_gw, comp)
                last_gw = comp
                print(f"  ✓ {app}")
                changes += 1
    
    # --- 写入 ---
    print(f"\n[5] 写入文件... ({changes} 个新组件)")
    tree.write(INPUT_FILE, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    
    # 验证
    print("\n=== 验证 ===")
    from collections import Counter
    types = Counter()
    for c in qdc:
        if c.tag == 'component':
            types[c.get('id')] += 1
    for t, n in sorted(types.items()):
        print(f"  {t:40s} {n}")
    
    print(f"\n✅ 完成!")

if __name__ == '__main__':
    main()
