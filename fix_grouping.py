import sys
import os
#!/usr/bin/env python3
"""修复所有 connectedTo 分组问题 - 同类型必须连续"""
from lxml import etree
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

def parse(path):
    p = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    return etree.parse(path, p)

def fix_component_group(comp, ctype):
    """修复一个component内指定类型的connectedTo连续性"""
    cts = comp.findall('connectedTo')
    if len(cts) < 2: return 0
    
    # 找到该类型的第一个和最后一个位置
    type_cts = [(i, ct) for i, ct in enumerate(cts) if ct.get('component') == ctype]
    if len(type_cts) < 2: return 0
    
    # 检查连续性：每个后续的同类型是否紧跟前一个
    prev_idx = type_cts[0][0]
    fixed = 0
    to_move = []
    
    for i, ct in type_cts[1:]:
        if i != prev_idx + 1:
            # 不连续，需要移到 prev_idx+1 位置
            to_move.append((i, ct))
        prev_idx = i
    
    if not to_move:
        return 0
    
    # 收集要移动的元素并按原始位置排序
    to_move.sort(key=lambda x: x[0])
    
    # 找到该类型的最终连续块应该开始的位置
    first_ct = type_cts[0][1]
    ref = type_cts[0][1]  # 以第一个该类型的元素为参考
    
    for orig_idx, ct in reversed(to_move):
        comp.remove(ct)
        ref.addnext(ct)
        ref = ct
        fixed += 1
    
    return fixed

def main():
    print("修复 connectedTo 分组连续性")
    print("=" * 50)
    
    shutil.copy2(INPUT, INPUT.replace('.xml', '_pre_groupfix.xml'))
    
    tree = parse(INPUT)
    qdc = tree.getroot().find('quickDeployComponents')
    
    # 需要修复的组件列表 (从R11输出)
    to_fix = {
        'APP55': {'aws2_client_gateway_webtier': ['fnd0_fsc']},
        'APP56': {'aws2_client_gateway_webtier': ['fnd0_fsc']},
        'DISP01': {'fnd0_dispatcherModule': ['fnd0_j2ee_tcwebtier']},
        'DISP02': {'fnd0_dispatcherModule': ['fnd0_j2ee_tcwebtier']},
        'MSF01': {'fnd0_microservice': ['fnd0_j2ee_tcwebtier']},
    }
    # Web Tiers APP31-38
    for i in range(31, 39):
        to_fix[f'APP{i:02d}'] = {'fnd0_j2ee_tcwebtier': ['fnd0_serverManager']}
    
    total = 0
    for machine, cid_map in to_fix.items():
        for cid, ctypes in cid_map.items():
            for c in qdc:
                if c.tag == 'component' and c.get('id') == cid and c.get('machineName') == machine:
                    for ctype in ctypes:
                        n = fix_component_group(c, ctype)
                        if n:
                            print(f'  ✓ {cid} {machine} → {ctype} 修复{n}处')
                            total += n
                    break
    
    # 写回
    tree.write(INPUT, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    print(f'\n✅ 修复 {total} 处, 写入完成')

if __name__ == '__main__':
    main()
