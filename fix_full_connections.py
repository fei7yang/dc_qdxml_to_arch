import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充全连接组件的 APP53-56 连接
- fnd0_servermgrconsole: +SM(4) +Web(4)
- fnd0_microservice: +Web(4)
- fnd0_dispatcherModule DISP01/DISP02: +Web(4)
"""

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

def add_web_conns(text, component_id, machine):
    """在指定component的最后一个connectedTo后插入4个Web连接"""
    marker = f'component id="{component_id}" machineName="{machine}"'
    pos = text.find(marker)
    if pos == -1:
        print(f'  ✗ 找不到 {component_id} {machine}')
        return text
    
    # 找到该component的 </component>
    end = text.find('</component>', pos)
    if end == -1:
        return text
    
    # 在最后一个 connectedTo 后插入
    # 找到该component内最后一个 <connectedTo
    search_end = end
    last_ct = pos
    while True:
        ct_pos = text.find('<connectedTo', last_ct, search_end)
        if ct_pos == -1:
            break
        last_ct = ct_pos + 1
    
    if last_ct == pos:
        print(f'  ✗ {component_id} {machine} 没有connectedTo')
        return text
    
    # 找到这个connectedTo行的结尾
    ct_line_end = text.find('\n', last_ct - 1)
    
    new_lines = '\n'.join([
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP53"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP54"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP55"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP56"/>',
    ])
    
    return text[:ct_line_end + 1] + new_lines + '\n' + text[ct_line_end + 1:]

def add_sm_and_web_conns(text, component_id, machine):
    """servermgrconsole: 添加SM和Web连接"""
    marker = f'component id="{component_id}" machineName="{machine}"'
    pos = text.find(marker)
    if pos == -1:
        return text
    
    end = text.find('</component>', pos)
    
    # 找最后一个connectedTo
    last_ct = pos
    while True:
        ct_pos = text.find('<connectedTo', last_ct, end)
        if ct_pos == -1:
            break
        last_ct = ct_pos + 1
    
    ct_line_end = text.find('\n', last_ct - 1)
    
    new_lines = '\n'.join([
        f'            <connectedTo component="fnd0_serverManager" machineName="APP53"/>',
        f'            <connectedTo component="fnd0_serverManager" machineName="APP54"/>',
        f'            <connectedTo component="fnd0_serverManager" machineName="APP55"/>',
        f'            <connectedTo component="fnd0_serverManager" machineName="APP56"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP53"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP54"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP55"/>',
        f'            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="APP56"/>',
    ])
    
    return text[:ct_line_end + 1] + new_lines + '\n' + text[ct_line_end + 1:]

def main():
    print("补充全连接组件的 APP53-56 连接")
    print("=" * 50)
    
    text = read_file(INPUT)
    orig_len = len(text)
    
    # 1. servermgrconsole: +SM +Web
    print("\n[1] fnd0_servermgrconsole APP01 → +SM(4) +Web(4)")
    text = add_sm_and_web_conns(text, 'fnd0_servermgrconsole', 'APP01')
    print(f"  ✓ 已添加")
    
    # 2. microservice: +Web
    print("\n[2] fnd0_microservice MSF01 → +Web(4)")
    text = add_web_conns(text, 'fnd0_microservice', 'MSF01')
    print(f"  ✓ 已添加")
    
    # 3. dispatcherModule DISP01: +Web
    print("\n[3] fnd0_dispatcherModule DISP01 → +Web(4)")
    text = add_web_conns(text, 'fnd0_dispatcherModule', 'DISP01')
    print(f"  ✓ 已添加")
    
    # 4. dispatcherModule DISP02: +Web
    print("\n[4] fnd0_dispatcherModule DISP02 → +Web(4)")
    text = add_web_conns(text, 'fnd0_dispatcherModule', 'DISP02')
    print(f"  ✓ 已添加")
    
    write_file(INPUT, text)
    print(f"\n✅ 完成!  {orig_len} → {len(text)} 字符")

if __name__ == '__main__':
    main()
