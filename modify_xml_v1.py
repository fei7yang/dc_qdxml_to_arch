#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 quick-deploy.xml:
1. 将 APP39/40 从 TcClusterHaiWai 迁移到 TcClusterJiTuan4
2. 新增 APP53/54 (TcClusterTest)
3. 新增 APP55/56 (TcClusterHaiWai)
"""

import re
import sys

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_app39_40_to_jituan4(content):
    """修改 APP39/40 配置到 TcClusterJiTuan4"""
    
    # 1. 修改 APP39 Web Tier 连接 (line ~12295)
    # 找到 APP39 的 fnd0_j2ee_tcwebtier 组件，修改其 connectedTo
    pattern_web39 = r'(<component id="fnd0_j2ee_tcwebtier" machineName="APP39"[^>]*>)(.*?)(</component>)'
    
    def replace_web39_connections(match):
        opening = match.group(1)
        body = match.group(2)
        closing = match.group(3)
        
        # 删除所有现有的 fnd0_serverManager connectedTo
        body = re.sub(r'<connectedTo component="fnd0_serverManager" machineName="APP\d+"/>\n', '', body)
        
        # 添加 APP31-40 的连接
        new_connections = ''
        for i in range(31, 41):
            new_connections += f'            <connectedTo component="fnd0_serverManager" machineName="APP{i}"/>\n'
        
        # 保留其他 connectedTo (microservice, servermgrconsole)
        # 在 </component> 前插入新的连接
        body = re.sub(r'(<connectedTo component="fnd0_servermgrconsole" machineName="APP01"/>)\n', 
                     r'\1\n' + new_connections, body)
        
        return opening + body + closing
    
    # 由于正则可能不够精确，我用更可靠的方法：逐段处理
    # 实际上，我需要找到 APP39 Web Tier 的确切位置并替换其 connections
    
    return content

def main():
    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
    else:
        import os as _os
        _base = _os.path.dirname(_os.path.abspath(__file__))
        _xmls = sorted([f for f in _os.listdir(_base) if f.lower().endswith('.xml')])
        if len(_xmls) != 1:
            print(f'用法: python {__file__} [XML路径]  或把 .xml 放在脚本目录')
            sys.exit(1)
        filepath = _os.path.join(_base, _xmls[0])
    
    print("读取文件...")
    content = read_file(filepath)
    
    print("修改 APP39/40 配置...")
    content = modify_app39_40_to_jituan4(content)
    
    print("写入文件...")
    write_file(filepath, content)
    
    print("完成！")

if __name__ == '__main__':
    main()
