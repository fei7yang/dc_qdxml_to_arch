#!/usr/bin/env python3
"""修复 visservermanager 缺失的 FSC 连接（新增 APP 时遗漏的全连接更新）"""
import sys, os, xml.etree.ElementTree as ET, shutil
from pathlib import Path

# 自动检测 XML
if len(sys.argv) >= 2:
    xml_path = Path(os.path.abspath(sys.argv[1]))
else:
    _base = Path(__file__).parent
    _xmls = sorted(_base.glob('*.xml'))
    if len(_xmls) != 1:
        print(f'用法: python {Path(__file__).name} [XML路径]  或把 .xml 放在脚本目录')
        sys.exit(1)
    xml_path = _xmls[0]

backup_path = xml_path.with_suffix('.xml_backup_visserver_fsc')

# 备份
if not backup_path.exists():
    shutil.copy2(xml_path, backup_path)
    print(f'已备份: {backup_path}')

tree = ET.parse(xml_path)
root = tree.getroot()

# 需要补充的 FSC 机器名
missing_fsc = ['APP53', 'APP54', 'APP55', 'APP56']

# 找到 aws2_visservermanager 的两个组件，补充缺失的 FSC 连接
fixed = 0
for comp in root.findall('.//component'):
    cid = comp.get('id', '')
    if cid == 'aws2_visservermanager':
        machine = comp.get('machineName')
        # 检查是否已存在这些连接
        existing = set()
        for ct in comp.findall('.//connectedTo'):
            if ct.get('component') == 'fnd0_fsc':
                existing.add(ct.get('machineName'))
        
        for fsc_machine in missing_fsc:
            if fsc_machine not in existing:
                new_ct = ET.SubElement(comp, 'connectedTo')
                new_ct.set('component', 'fnd0_fsc')
                new_ct.set('machineName', fsc_machine)
                fixed += 1
                print(f'  + {machine} -> fnd0_fsc@{fsc_machine}')
        
        # 按 machineName 排序 connectedTo（可选，保持整洁）
        connected = comp.findall('connectedTo')
        connected_sorted = sorted(connected, key=lambda x: (x.get('component',''), x.get('machineName','')))
        # 重新插入（先删后加）
        for ct in connected:
            comp.remove(ct)
        for ct in connected_sorted:
            comp.append(ct)

print(f'\n共补充 {fixed} 个 connectedTo')
tree.write(xml_path, encoding='utf-8', xml_declaration=True)
print(f'已写入: {xml_path}')
