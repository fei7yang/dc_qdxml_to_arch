import sys
import os
#!/usr/bin/env python3
"""
全面检查 quick-deploy.xml 的连接问题
基于 Validation.logic 规则 + Eric 提出的6个问题
"""
from lxml import etree
from collections import defaultdict
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

# ===== Cluster 定义 =====
CLUSTERS = {
    'TcClusterJiTuan1':      [f'APP{i:02d}' for i in range(1, 11)],
    'TcClusterJiTuan2':      [f'APP{i:02d}' for i in range(11, 21)],
    'TcClusterJiTuan3':      [f'APP{i:02d}' for i in range(21, 31)],
    'TcClusterJiTuan4':      [f'APP{i:02d}' for i in range(31, 41)],
    'TcClusterXinJishuYuan': [f'APP{i:02d}' for i in range(41, 43)],
    'TcClusterJiChuYuan':    [f'APP{i:02d}' for i in range(43, 45)],
    'TcClusterJieKou':       [f'APP{i:02d}' for i in range(45, 53)],
    'TcClusterTest':         [f'APP{i:02d}' for i in range(53, 55)],
    'TcClusterHaiWai':       [f'APP{i:02d}' for i in range(55, 57)],
}
ALL_APPS = []
for apps in CLUSTERS.values():
    ALL_APPS.extend(apps)

def get_cluster(app):
    for cn, apps in CLUSTERS.items():
        if app in apps:
            return cn
    return None

def parse():
    p = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    return etree.parse(INPUT, p)

def get_components(tree, cid):
    qdc = tree.getroot().find('quickDeployComponents')
    if qdc is None: return []
    return [c for c in qdc if c.tag == 'component' and c.get('id') == cid]

def get_clients(tree, cid):
    qcl = tree.getroot().find('quickDeployClients')
    if qcl is None: return []
    return [c for c in qcl if c.tag == 'client' and c.get('id') == cid]

def get_cts(elem, comp_type=None):
    """获取 elem 的 connectedTo 列表，可选过滤 component 类型"""
    result = []
    for ct in elem.findall('connectedTo'):
        ct_comp = ct.get('component', '')
        ct_mn = ct.get('machineName', '')
        if comp_type is None or ct_comp == comp_type:
            result.append((ct_comp, ct_mn))
    return result

def condense(machines):
    """将机器名列表压缩为范围表示"""
    if not machines: return '(空)'
    # 分组：按前缀
    groups = defaultdict(list)
    for m in sorted(machines):
        m2 = re.search(r'(\D+)(\d+)', m)
        if m2:
            groups[m2.group(1)].append(int(m2.group(2)))
        else:
            groups[m].append(0)
    
    parts = []
    for prefix in sorted(groups.keys()):
        nums = sorted(groups[prefix])
        if isinstance(nums[0], str):
            parts.append(prefix)
            continue
        ranges = []
        start = end = nums[0]
        for n in nums[1:]:
            if n == end + 1:
                end = n
            else:
                if start == end:
                    ranges.append(f'{prefix}{start:02d}')
                else:
                    ranges.append(f'{prefix}{start:02d}-{end:02d}')
                start = end = n
        if start == end:
            ranges.append(f'{prefix}{start:02d}')
        else:
            ranges.append(f'{prefix}{start:02d}-{end:02d}')
        parts.extend(ranges)
    return ', '.join(parts)

def main():
    tree = parse()
    root = tree.getroot()
    
    print("=" * 80)
    print("quick-deploy.xml 全面连接检查")
    print("=" * 80)
    
    # ═══ 先统计全量组件 ═══
    qdc = root.find('quickDeployComponents')
    qcl = root.find('quickDeployClients')
    
    comp_counts = defaultdict(int)
    comp_machines = defaultdict(list)
    client_counts = defaultdict(int)
    client_machines = defaultdict(list)
    
    for c in qdc:
        if c.tag == 'component':
            cid = c.get('id', '')
            mn = c.get('machineName', '')
            comp_counts[cid] += 1
            comp_machines[cid].append(mn)
    
    for c in qcl:
        if c.tag == 'client':
            cid = c.get('id', '')
            mn = c.get('machineName', '')
            client_counts[cid] += 1
            client_machines[cid].append(mn)
    
    print("\n═══ 组件数量统计 ═══")
    print(f"  quickDeployComponents:")
    for cid in sorted(comp_counts.keys()):
        print(f"    {cid:45s} {comp_counts[cid]:3d}")
    print(f"  quickDeployClients:")
    for cid in sorted(client_counts.keys()):
        print(f"    {cid:45s} {client_counts[cid]:3d}")
    
    # ═══ FSC 完整统计 ═══
    print("\n\n═══ 问题1: Gateway connectedTo FSC 合并检查 ═══")
    fsc_comps = get_components(tree, 'fnd0_fsc')
    all_fsc_machines = sorted([c.get('machineName') for c in fsc_comps])
    master_fscs = sorted([c.get('machineName') for c in fsc_comps 
                         if c.get('machineName') and any(p.get('id') == 'fnd0_isMaster' and p.get('value', '').lower() == 'true' for p in c.findall('property'))])
    nonmaster_fscs = sorted(set(all_fsc_machines) - set(master_fscs))
    
    print(f"  FSC 总数: {len(all_fsc_machines)}")
    print(f"  Master FSC ({len(master_fscs)}): {condense(master_fscs)}")
    print(f"  Non-Master FSC ({len(nonmaster_fscs)}): {condense(nonmaster_fscs)}")
    
    gateways = get_components(tree, 'aws2_client_gateway_webtier')
    print(f"\n  Gateway 总数: {len(gateways)}")
    
    for gw in sorted(gateways, key=lambda x: x.get('machineName', '')):
        mn = gw.get('machineName')
        fsc_cts = [m for t, m in get_cts(gw, 'fnd0_fsc')]
        missing = set(all_fsc_machines) - set(fsc_cts)
        extra = set(fsc_cts) - set(all_fsc_machines)
        status = '✅' if not missing and not extra else '❌'
        print(f"  {status} {mn}: connectedTo fnd0_fsc = {len(fsc_cts)}/{len(all_fsc_machines)}", end='')
        if missing:
            print(f"  缺{len(missing)}: {condense(sorted(missing))}", end='')
        if extra:
            print(f"  多{len(extra)}: {condense(sorted(extra))}", end='')
        print()
        
        # 检查 R8: Gateway→自己Web
        web_cts = [m for t, m in get_cts(gw, 'fnd0_j2ee_tcwebtier')]
        if mn not in web_cts:
            print(f"    ❌ R8: Gateway 未连接自己的Web (缺 {mn})")
        
        # 检查 R2: Gateway→VisPoolAssigner
        vis_cts = [m for t, m in get_cts(gw, 'aws2_vispoolassigner')]
        expected_vis = 'VIS01' if int(mn[3:]) % 2 == 1 else 'VIS02'
        if vis_cts != [expected_vis]:
            print(f"    ❌ R2: Gateway→VIS 应为{expected_vis}, 实际{vis_cts}")
    
    # ═══ 问题2: dispatcherModule connectedTo blserver ═══
    print("\n\n═══ 问题2: fnd0_dispatcherModule connectedTo blserver 检查 ═══")
    
    # 先看 blserver 到底在哪
    blserver_comps = get_components(tree, 'fnd0_blserver')
    blserver_clients = get_clients(tree, 'fnd0_blserver')
    print(f"  fnd0_blserver 在 components 中: {len(blserver_comps)} 个")
    print(f"  fnd0_blserver 在 clients 中: {len(blserver_clients)} 个")
    
    if blserver_clients:
        bl_machines = sorted([c.get('machineName') for c in blserver_clients])
        print(f"  BL Server 机器名 ({len(bl_machines)}): {condense(bl_machines)}")
    
    dispatchers = get_components(tree, 'fnd0_dispatcherModule')
    for disp in sorted(dispatchers, key=lambda x: x.get('machineName', '')):
        mn = disp.get('machineName')
        bl_cts = [m for t, m in get_cts(disp, 'fnd0_blserver')]
        web_cts = [m for t, m in get_cts(disp, 'fnd0_j2ee_tcwebtier')]
        
        # R9: dispatcher 应连接所有 Web + 所有 BL Server
        web_comps = get_components(tree, 'fnd0_j2ee_tcwebtier')
        expected_web_machines = sorted([c.get('machineName') for c in web_comps])
        
        print(f"\n  {mn}:")
        print(f"    connectedTo fnd0_blserver: {len(bl_cts)} 个 → {condense(bl_cts)}")
        print(f"    connectedTo fnd0_j2ee_tcwebtier: {len(web_cts)}/{len(expected_web_machines)}")
        
        # 检查 Web 连接
        web_missing = set(expected_web_machines) - set(web_cts)
        web_extra = set(web_cts) - set(expected_web_machines)
        if web_missing:
            print(f"    ❌ Web缺{len(web_missing)}: {condense(sorted(web_missing))}")
        if web_extra:
            print(f"    ⚠️ Web多{len(web_extra)}: {condense(sorted(web_extra))}")
        
        # 检查 BL 连接
        if blserver_clients:
            expected_bl_machines = sorted([c.get('machineName') for c in blserver_clients])
            bl_missing = set(expected_bl_machines) - set(bl_cts)
            bl_extra = set(bl_cts) - set(expected_bl_machines)
            if bl_missing:
                print(f"    ❌ BL缺{len(bl_missing)}: {condense(sorted(bl_missing))}")
            if bl_extra:
                print(f"    ⚠️ BL多{len(bl_extra)}: {condense(sorted(bl_extra))}")
        else:
            print(f"    ❌ XML中无 fnd0_blserver 组件/客户端，无法验证BL连接")
            print(f"       当前 dispatcher 引用的 blserver: {condense(bl_cts)}")
    
    # ═══ 问题3: 渲染逻辑检查 — dc_qdxml_to_arch.py 如何处理 connectedTo ═══
    print("\n\n═══ 问题3: dc_qdxml_to_arch.py 渲染逻辑分析 ═══")
    print("  dc_qdxml_to_arch.py 的 parse_xml() 提取 connectedTo:")
    print("    info['connectedTo'].append({'component': ..., 'machineName': ...})")
    print("  但 classify() 中对 connectedTo 的使用仅限于:")
    print("    - WT→SM (fnd0_serverManager) 用于画线和full-mesh检测")
    print("    - 其他 connectedTo **并未在架构图中渲染**")
    print("  ⚠️ Eric说的'blserver渲染不对'可能指的是 validator 报告页面")
    print("  report_core.py 的 format_cts() 使用 condense_machines() 压缩显示")
    print("  该函数只做范围压缩，不做内容校验，因此如果XML里值不全，显示也不会全")
    
    # ═══ 问题4: Master FSC connectedTo fnd0_fsc 数量 ═══
    print("\n\n═══ 问题4: Master FSC connectedTo fnd0_fsc 数量检查 ═══")
    
    for fsc in fsc_comps:
        mn = fsc.get('machineName')
        is_master = any(p.get('id') == 'fnd0_isMaster' and p.get('value', '').lower() == 'true' 
                       for p in fsc.findall('property'))
        if not is_master:
            continue
        
        fsc_cts = [m for t, m in get_cts(fsc, 'fnd0_fsc')]
        
        # Master FSC 应连接所有 Non-Master FSC（不连自己和其他Master）
        expected = nonmaster_fscs
        missing = set(expected) - set(fsc_cts)
        extra = set(fsc_cts) - set(expected)
        
        status = '✅' if not missing and not extra else '❌'
        print(f"  {status} {mn} (Master): connectedTo fnd0_fsc = {len(fsc_cts)}/{len(expected)}", end='')
        
        # 检查是否连接了自己
        self_conn = mn in fsc_cts
        if self_conn:
            print(f"  ⚠️ 自连接!", end='')
        
        # 检查是否连接了其他Master
        master_conns = [m for m in fsc_cts if m in master_fscs]
        if master_conns:
            print(f"  ⚠️ 连了其他Master: {master_conns}", end='')
        
        if missing:
            print(f"  缺{len(missing)}: {condense(sorted(missing))}", end='')
        if extra:
            extra_non_master = [m for m in extra if m not in master_fscs]
            extra_master = [m for m in extra if m in master_fscs]
            if extra_master:
                print(f"  多Master{len(extra_master)}: {condense(sorted(extra_master))}", end='')
            if extra_non_master:
                print(f"  多其他{len(extra_non_master)}: {condense(sorted(extra_non_master))}", end='')
        print()
        
        # 检查 fsc_group 和 fsc_keys
        fsc_group = [m for t, m in get_cts(fsc, 'fnd0_fsc_group')]
        fsc_keys = [m for t, m in get_cts(fsc, 'fnd0_fsc_keys')]
        print(f"       connectedTo fnd0_fsc_group: {fsc_group}")
        print(f"       connectedTo fnd0_fsc_keys: {fsc_keys}")
    
    # ═══ 问题5: APP01 FSC 详细检查 ═══
    print("\n\n═══ 问题5: APP01 FSC 详细检查 ═══")
    app01_fsc = [fsc for fsc in fsc_comps if fsc.get('machineName') == 'APP01']
    if app01_fsc:
        fsc = app01_fsc[0]
        is_master = any(p.get('id') == 'fnd0_isMaster' and p.get('value', '').lower() == 'true' 
                       for p in fsc.findall('property'))
        print(f"  APP01 FSC: isMaster={is_master}")
        all_cts = get_cts(fsc)
        for ct_type in sorted(set(t for t, m in all_cts)):
            machines = [m for t, m in all_cts if t == ct_type]
            print(f"    connectedTo {ct_type}: {len(machines)} → {condense(machines)}")
    else:
        print("  ❌ APP01 没有 FSC 组件!")
    
    # ═══ 问题6: 全文档 connected 连接完整性检查 ═══
    print("\n\n═══ 问题6: 全文档 connected 连接完整性检查 ═══")
    
    # R9: 全连接组件
    print("\n  --- R9: 全连接组件检查 ---")
    
    # fnd0_servermgrconsole@APP01 → 所有SM + 所有Web
    console = get_components(tree, 'fnd0_servermgrconsole')
    if console:
        c = console[0]
        sm_cts = [m for t, m in get_cts(c, 'fnd0_serverManager')]
        web_cts = [m for t, m in get_cts(c, 'fnd0_j2ee_tcwebtier')]
        sm_comps = get_components(tree, 'fnd0_serverManager')
        web_comps = get_components(tree, 'fnd0_j2ee_tcwebtier')
        expected_sm = sorted([sc.get('machineName') for sc in sm_comps])
        expected_web = sorted([wc.get('machineName') for wc in web_comps])
        
        sm_missing = set(expected_sm) - set(sm_cts)
        web_missing = set(expected_web) - set(web_cts)
        sm_status = '✅' if not sm_missing else '❌'
        web_status = '✅' if not web_missing else '❌'
        print(f"  {sm_status} fnd0_servermgrconsole@APP01 → SM: {len(sm_cts)}/{len(expected_sm)}", end='')
        if sm_missing:
            print(f"  缺{len(sm_missing)}: {condense(sorted(sm_missing))}", end='')
        print()
        print(f"  {web_status} fnd0_servermgrconsole@APP01 → Web: {len(web_cts)}/{len(expected_web)}", end='')
        if web_missing:
            print(f"  缺{len(web_missing)}: {condense(sorted(web_missing))}", end='')
        print()
    
    # fnd0_microservice@MSF01 → 所有Web
    msf = get_components(tree, 'fnd0_microservice')
    if msf:
        c = msf[0]
        web_cts = [m for t, m in get_cts(c, 'fnd0_j2ee_tcwebtier')]
        web_missing = set(expected_web) - set(web_cts)
        status = '✅' if not web_missing else '❌'
        print(f"  {status} fnd0_microservice@MSF01 → Web: {len(web_cts)}/{len(expected_web)}", end='')
        if web_missing:
            print(f"  缺{len(web_missing)}: {condense(sorted(web_missing))}", end='')
        print()
    
    # R1: WT→SM 全连接
    print("\n  --- R1: WT→SM 集群内全连接检查 ---")
    web_comps_list = get_components(tree, 'fnd0_j2ee_tcwebtier')
    r1_errors = 0
    for web in sorted(web_comps_list, key=lambda x: x.get('machineName', '')):
        mn = web.get('machineName')
        cluster = get_cluster(mn)
        if not cluster:
            continue
        sm_cts = [m for t, m in get_cts(web, 'fnd0_serverManager')]
        expected = CLUSTERS[cluster]
        missing = set(expected) - set(sm_cts)
        extra = set(sm_cts) - set(expected)
        if missing or extra:
            r1_errors += 1
            print(f"  ❌ {mn} ({cluster}): SM连接{len(sm_cts)}/{len(expected)}", end='')
            if missing:
                print(f"  缺: {condense(sorted(missing))}", end='')
            if extra:
                print(f"  多: {condense(sorted(extra))}", end='')
            print()
    if r1_errors == 0:
        print(f"  ✅ 所有56个WT的SM连接都正确")
    
    # R11: connectedTo 类型分组
    print("\n  --- R11: 同组件内 connectedTo 类型分组检查 ---")
    r11_errors = 0
    for parent in [qdc, qcl]:
        if parent is None: continue
        for c in parent:
            tag = c.tag
            if tag not in ('component', 'client'): continue
            cid = c.get('id', '')
            mn = c.get('machineName', '')
            cts = c.findall('connectedTo')
            if len(cts) < 3: continue
            
            last_seen = {}
            for i, ct in enumerate(cts):
                ct_type = ct.get('component', '')
                if ct_type in last_seen and last_seen[ct_type] < i - 1:
                    # 检查中间是否有同类型
                    has_same_between = any(cts[j].get('component', '') == ct_type 
                                         for j in range(last_seen[ct_type] + 1, i))
                    if not has_same_between:
                        r11_errors += 1
                        print(f"  ❌ {cid}@{mn}: {ct_type} 不连续 (idx {last_seen[ct_type]}→{i})")
                        break
                last_seen[ct_type] = i
    if r11_errors == 0:
        print(f"  ✅ 所有组件的 connectedTo 同类型连续")
    
    # fnd0_tccs 存在性
    print("\n  --- fnd0_tccs 检查 ---")
    tccs_comps = get_components(tree, 'fnd0_tccs')
    tccs_clients = get_clients(tree, 'fnd0_tccs')
    print(f"  fnd0_tccs 在 components 中: {len(tccs_comps)} 个")
    print(f"  fnd0_tccs 在 clients 中: {len(tccs_clients)} 个")
    
    # visservermanager 引用了 tccs
    viss = get_components(tree, 'aws2_visservermanager')
    for vis in viss:
        mn = vis.get('machineName')
        tccs_cts = [m for t, m in get_cts(vis, 'fnd0_tccs')]
        if tccs_cts:
            print(f"  {mn} VIS 引用了 fnd0_tccs: {tccs_cts}")
    
    # fnd0_blserver 在 clients 中详细检查
    print("\n  --- fnd0_blserver (client) 详细检查 ---")
    if blserver_clients:
        for bl in sorted(blserver_clients, key=lambda x: x.get('machineName', '')):
            mn = bl.get('machineName')
            all_cts = get_cts(bl)
            ct_summary = []
            for ct_type in sorted(set(t for t, m in all_cts)):
                machines = [m for t, m in all_cts if t == ct_type]
                ct_summary.append(f"{ct_type}→{condense(machines)}")
            print(f"    {mn}: {'; '.join(ct_summary)}")
    else:
        print("    ❌ 无 fnd0_blserver 客户端！")
        # 检查被谁引用
        for parent in [qdc, qcl]:
            if parent is None: continue
            for c in parent:
                if c.tag not in ('component', 'client'): continue
                bl_cts = [m for t, m in get_cts(c, 'fnd0_blserver')]
                if bl_cts:
                    cid = c.get('id', '')
                    cmn = c.get('machineName', '')
                    print(f"    被 {cid}@{cmn} 引用: {condense(bl_cts)}")
    
    # ═══ 总结 ═══
    print("\n\n" + "=" * 80)
    print("检查总结")
    print("=" * 80)

if __name__ == '__main__':
    main()
