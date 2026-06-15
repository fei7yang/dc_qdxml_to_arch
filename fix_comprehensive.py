import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合修复 modified12.xml:
1. 删除多余 6 个 corporateserver (只保留 APP01)
2. 修复格式: </xxx><yyy → </xxx>\n<yyy
3. 新增 APP53-56 的 fnd0_blserver client
"""

import re

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

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("=" * 50)
    print("综合修复 modified12.xml")
    print("=" * 50)
    
    text = read_file(INPUT)
    orig_len = len(text)
    
    # ===== 1. 删除多余 corporateserver =====
    print("\n[1] 删除多余 fnd0_corporateserver...")
    # 删除 corp 除了 APP01 以外的所有（APP39/40/53-56）
    # 找到所有 corp 组件并删除
    pattern = r'\n\s*<component id="fnd0_corporateserver" machineName="(APP(?:39|40|53|54|55|56))"[^>]*>.*?</component>'
    
    for app in ['APP39', 'APP40', 'APP53', 'APP54', 'APP55', 'APP56']:
        # 使用更精确的匹配
        start_marker = f'<component id="fnd0_corporateserver" machineName="{app}"'
        pos = text.find(start_marker)
        if pos == -1:
            print(f"  ⚠ {app} 未找到")
            continue
        
        # 往前找换行
        nl_before = text.rfind('\n', 0, pos)
        if nl_before == -1:
            nl_before = pos
        
        # 往后找 </component>
        end_pos = text.find('</component>', pos)
        if end_pos == -1:
            continue
        end_pos += len('</component>')
        # 检查后面是否有换行，有的话一起删
        if end_pos < len(text) and text[end_pos] == '\n':
            end_pos += 1
        
        text = text[:nl_before] + text[end_pos:]
        print(f"  ✓ 删除 {app}")
    
    # ===== 2. 修复格式: </xxx><yyy → </xxx>\n<yyy =====
    print("\n[2] 修复格式...")
    # 找所有 </xxx><yyy 并替换为 </xxx>\n<yyy
    # 但要保留正确的缩进
    lines = text.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        m = re.search(r'(</\w+>)(\s*)(<\w+)', line)
        if m and '<?xml' not in line:
            # 分割
            idx = m.start(2)
            before = line[:idx]
            after = line[idx:]
            # 获取前一行的缩进
            indent = '    '  # 默认4空格
            if i > 0:
                prev = lines[i-1]
                indent_match = re.match(r'^(\s*)', prev)
                if indent_match:
                    indent = indent_match.group(1)
            
            new_lines.append(before + m.group(1))
            new_lines.append(indent + after.lstrip())
            print(f"  修复行{i+1}: </{m.group(1)[2:]}><{m.group(3)[1:]}")
        else:
            new_lines.append(line)
    
    text = '\n'.join(new_lines)
    
    # ===== 3. 新增 blserver for APP53-56 =====
    print("\n[3] 新增 fnd0_blserver for APP53-56...")
    # blserver 模板
    bls = {'APP53', 'APP54', 'APP55', 'APP56'}
    
    for app in sorted(bls):
        # 找最后一个 blserver </client> 后插入
        last_bl = text.rfind('client id="fnd0_blserver"')
        if last_bl == -1:
            print(f"  ✗ 找不到 blserver")
            break
        
        # 找到这个 client 的 </client>
        end = text.find('</client>', last_bl)
        insert_pos = end + len('</client>')
        if insert_pos < len(text) and text[insert_pos] == '\n':
            insert_pos += 1
        
        bl_template = f'''        <client id="fnd0_blserver" machineName="{app}" massDeploy="false" platform="wntx64" deploymentStatus="Pending Install" createTemplateClient="false" useTemplateClient="false">
            <property id="fnd0_blserver.appSupportedList" value="selectedApps"/>
            <property id="fnd0_blserver.massDeployCheck" value="false"/>
            <property id="fnd0_racblapplicationConnectionName" value="2512"/>
            <property id="fnd0_racblapplicationConnectionTag" value=""/>
            <property id="fnd0_tcblInstallationPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root"/>
            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="{app}"/>
            <package id="cfg0configurator" deploymentStatus="Pending Install"/>
            <package id="cfg1configurator" deploymentStatus="Pending Install"/>
            <package id="smc0psmcfgsupport" deploymentStatus="Pending Install"/>
            <package id="tm0tsm" deploymentStatus="Pending Install"/>
            <package id="vendormanagement" deploymentStatus="Pending Install"/>
        </client>
'''
        text = text[:insert_pos] + bl_template + text[insert_pos:]
        print(f"  ✓ {app}")
    
    # ===== 写入 =====
    write_file(INPUT, text)
    print(f"\n✅ 完成! {orig_len} → {len(text)} 字符")

if __name__ == '__main__':
    main()
