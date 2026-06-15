import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 quick-deploy.xml (原地修改)
1. 将 APP39/40 迁移到 TcClusterJiTuan4 (APP31~40, 10台全连接)
2. 新增 APP53/54 (TcClusterTest)
3. 新增 APP55/56 (TcClusterHaiWai)

新组件插入在对应类型组内，保持整洁。
"""

from lxml import etree
import os, shutil
from datetime import datetime

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

def find_components_by_type(qdc, ctype):
    """找到 quickDeployComponents 下所有指定类型的 component"""
    return [c for c in qdc if c.tag == 'component' and c.get('id') == ctype]

def find_component_by_machine(qdc, ctype, machine):
    """找到指定类型的特定 machine 的 component"""
    for c in qdc:
        if c.tag == 'component' and c.get('id') == ctype and c.get('machineName') == machine:
            return c
    return None

def remove_connectedBy_type(comp, target_type):
    """删除 comp 中所有指定类型的 connectedTo"""
    for ct in list(comp.findall('connectedTo')):
        if ct.get('component') == target_type:
            comp.remove(ct)

def add_connectedTo(comp, target_type, target_machine):
    """添加 connectedTo"""
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', target_type)
    ct.set('machineName', target_machine)

def set_property(comp, prop_id, prop_value):
    """设置 property 值，如不存在则创建"""
    for p in comp.findall('property'):
        if p.get('id') == prop_id:
            p.set('value', prop_value)
            return
    # 不存在则创建
    p = etree.SubElement(comp, 'property')
    p.set('id', prop_id)
    p.set('value', prop_value)

def get_property(comp, prop_id):
    """获取 property 值"""
    for p in comp.findall('property'):
        if p.get('id') == prop_id:
            return p.get('value')
    return None

def modify_app39_40(qdc):
    """修改 APP39/40: Web连接改为 APP31~40, Pool ClusterID改为TcClusterJiTuan4"""
    print("  修改 APP39/40 → TcClusterJiTuan4...")
    
    jituan4_pools = [f'APP{i}' for i in range(31, 41)]
    
    for app in ['APP39', 'APP40']:
        # 1. 修改 Web Tier
        web = find_component_by_machine(qdc, 'fnd0_j2ee_tcwebtier', app)
        if web is not None:
            # 删除所有 fnd0_serverManager 连接
            remove_connectedBy_type(web, 'fnd0_serverManager')
            # 添加 APP31~40 的连接
            for pool in jituan4_pools:
                add_connectedTo(web, 'fnd0_serverManager', pool)
            print(f"    ✓ {app} Web Tier → {len(jituan4_pools)}个Pool (APP31~40)")
        
        # 2. 修改 Pool
        pool = find_component_by_machine(qdc, 'fnd0_serverManager', app)
        if pool is not None:
            set_property(pool, 'fnd0_serverManagerDisplayClusterId', 'TcClusterJiTuan4')
            print(f"    ✓ {app} Pool → ClusterId=TcClusterJiTuan4")

def create_web_tier(app_name, cluster_id, pool_apps):
    """创建 Web Tier 组件 (fnd0_j2ee_tcwebtier)"""
    comp = etree.SubElement(etree.Element('dummy'), 'component')
    comp = etree.Element('component')
    comp.set('id', 'fnd0_j2ee_tcwebtier')
    comp.set('machineName', app_name)
    comp.set('platform', 'wntx64')
    comp.set('deploymentStatus', 'Pending Install')
    
    # Space for pretty formatting
    comp.text = '\n            '
    
    num = app_name[3:]
    props = {
        'fnd0_j2ee_4tierURI': f'http://{app_name}:7001/tc',
        'fnd0_j2ee_JMXRMIPort': '8089',
        'fnd0_j2ee_LogVolumeName': 'LogVol1',
        'fnd0_j2ee_applicationName': f'TcWeb{num}',
        'fnd0_j2ee_deployableFileName': 'tc',
        'fnd0_j2ee_serviceName': 'Teamcenter WebTier',
        'fnd0_j2ee_sessionTimeOut': '1440',
        'fnd0_j2ee_tcwebtier.port': '7001',
        'fnd0_j2ee_tcwebtier.protocol': 'http',
        'fnd0_j2ee_tcwebtierInstallationPath': r'D:\PLM\Siemens\Teamcenter2512\tc_root',
        'fnd0_j2ee_treeCachePeersHost': app_name,
        'fnd0_tcJavaConnectionName': f'TcWeb{num}',
        'fnd0_tcJavaConnectionTag': 'Tag1',
        'fnd0_webTierCustomBaseLogFileLocation': r'%USERPROFILE%\Siemens\logs',
        'fnd0_webTierCustomBaseUnixLogFileLocation': '$HOME/Siemens/logs'
    }
    
    for pid, pval in props.items():
        p = etree.SubElement(comp, 'property')
        p.set('id', pid)
        p.set('value', pval)
        p.tail = '\n            '
    
    # connectedTo
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_microservice')
    ct.set('machineName', 'MSF01')
    ct.tail = '\n            '
    
    for pool_app in pool_apps:
        ct = etree.SubElement(comp, 'connectedTo')
        ct.set('component', 'fnd0_serverManager')
        ct.set('machineName', pool_app)
        ct.tail = '\n            '
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_servermgrconsole')
    ct.set('machineName', 'APP01')
    ct.tail = '\n        '
    
    comp[-1].tail = '\n        '  # last connectedTo
    
    return comp

def create_server_manager(app_name, cluster_id):
    """创建 Pool (Server Manager) 组件"""
    comp = etree.Element('component')
    comp.set('id', 'fnd0_serverManager')
    comp.set('machineName', app_name)
    comp.set('platform', 'wntx64')
    comp.set('deploymentStatus', 'Pending Install')
    comp.text = '\n            '
    
    props = {
        'fnd0_SSLConfigured': 'false',
        'fnd0_TECSAdminPort': '8084',
        'fnd0_assignmentServicePort': '8086',
        'fnd0_availableServerAt': '0700 3,1700 2',
        'fnd0_config_id': 'config1',
        'fnd0_customBaseLogFileLocation': r'%USERPROFILE%\Siemens\logs',
        'fnd0_customBaseUnixLogFileLocation': '$HOME/Siemens/logs',
        'fnd0_isFirstInstance': 'false',
        'fnd0_jmxAdaptorPort': '8088',
        'fnd0_loginsPerMinute': '0',
        'fnd0_maxServersCount': '30',
        'fnd0_minWarmServersCount': '1',
        'fnd0_muxPort': '8087',
        'fnd0_serverHost': app_name,
        'fnd0_serverManagerDisplayClusterId': cluster_id,
        'fnd0_serverManagerInstallationPath': r'D:\PLM\Siemens\Teamcenter2512\tc_root',
        'fnd0_serverManagerMUXUrl': f'http://{app_name}:8087',
        'fnd0_serverManagerProtocol': 'http',
        'fnd0_serverManagerTECSHostAlias': app_name,
        'fnd0_serverPoolId': f'Pool{app_name}',
        'fnd0_serverPoolManager_service': f'Teamcenter Server Manager config1_Pool{app_name}',
        'fnd0_startUpMode': 'fnd0_commandLine'
    }
    
    for pid, pval in props.items():
        p = etree.SubElement(comp, 'property')
        p.set('id', pid)
        p.set('value', pval)
        p.tail = '\n            '
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_servermgrconsole')
    ct.set('machineName', 'APP01')
    ct.tail = '\n            '
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_serverpool_DBConfig')
    ct.set('machineName', 'DBSCAN')
    ct.tail = '\n            '
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_tcdbserver')
    ct.set('machineName', 'DBSCAN')
    ct.tail = '\n        '
    
    return comp

def insert_after(last_comp, new_comp):
    """在 last_comp 后插入 new_comp"""
    parent = last_comp.getparent()
    idx = list(parent).index(last_comp)
    parent.insert(idx + 1, new_comp)
    return new_comp

def add_new_clusters(qdc):
    """添加新集群组件到正确的位置"""
    
    # 找到最后一个 fnd0_j2ee_tcwebtier
    all_webs = find_components_by_type(qdc, 'fnd0_j2ee_tcwebtier')
    last_web = all_webs[-1]
    
    # 找到最后一个 fnd0_serverManager
    all_pools = find_components_by_type(qdc, 'fnd0_serverManager')
    last_pool = all_pools[-1]
    
    # 新增 APP53/54 (TcClusterTest) + APP55/56 (TcClusterHaiWai)
    new_clusters = [
        (['APP53', 'APP54'], 'TcClusterTest'),
        (['APP55', 'APP56'], 'TcClusterHaiWai'),
    ]
    
    for app_list, cluster_id in new_clusters:
        print(f"  添加集群 {cluster_id} ({', '.join(app_list)})...")
        for app in app_list:
            web_comp = create_web_tier(app, cluster_id, app_list)
            last_web = insert_after(last_web, web_comp)
            
            pool_comp = create_server_manager(app, cluster_id)
            last_pool = insert_after(last_pool, pool_comp)
            
            print(f"    ✓ {app} Web + Pool 已插入")

def verify_modifications(qdc):
    """验证修改结果"""
    print("\n  === 验证 ===")
    
    # 检查 APP39/40 的 Web 连接
    for app in ['APP39', 'APP40']:
        web = find_component_by_machine(qdc, 'fnd0_j2ee_tcwebtier', app)
        if web is not None:
            sm_connections = [ct.get('machineName') for ct in web.findall('connectedTo') 
                            if ct.get('component') == 'fnd0_serverManager']
            cluster = get_property(find_component_by_machine(qdc, 'fnd0_serverManager', app), 
                                  'fnd0_serverManagerDisplayClusterId')
            print(f"  {app} Web → Pool: {sm_connections}")
            print(f"  {app} Pool ClusterId: {cluster}")
    
    # 检查 APP53-56
    for app in ['APP53', 'APP54', 'APP55', 'APP56']:
        web = find_component_by_machine(qdc, 'fnd0_j2ee_tcwebtier', app)
        pool = find_component_by_machine(qdc, 'fnd0_serverManager', app)
        if web is not None:
            sm_connections = [ct.get('machineName') for ct in web.findall('connectedTo') 
                            if ct.get('component') == 'fnd0_serverManager']
            cluster = get_property(pool, 'fnd0_serverManagerDisplayClusterId') if pool is not None else 'N/A'
            print(f"  {app} Web → Pool: {sm_connections}, Pool ClusterId: {cluster}")
    
    # 统计
    web_count = len(find_components_by_type(qdc, 'fnd0_j2ee_tcwebtier'))
    pool_count = len(find_components_by_type(qdc, 'fnd0_serverManager'))
    print(f"\n  Web Tier 总数: {web_count} (应为56)")
    print(f"  Pool 总数: {pool_count} (应为56)")

def main():
    print("=" * 60)
    print(f"修改 {INPUT_FILE}")
    print("=" * 60)
    
    # 备份
    backup_file = INPUT_FILE.replace('.xml', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml')
    print(f"\n[0] 备份: {backup_file}")
    shutil.copy2(INPUT_FILE, backup_file)
    
    # 解析
    print("\n[1] 解析 XML...")
    tree = parse_xml(INPUT_FILE)
    root = tree.getroot()
    qdc = root.find('quickDeployComponents')
    
    # 修改
    print("\n[2] 修改 APP39/40 → TcClusterJiTuan4")
    modify_app39_40(qdc)
    
    print("\n[3] 新增 APP53-56")
    add_new_clusters(qdc)
    
    # 验证
    verify_modifications(qdc)
    
    # 写入
    print("\n[4] 写入文件...")
    tree.write(INPUT_FILE, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print(f"   备份: {backup_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
