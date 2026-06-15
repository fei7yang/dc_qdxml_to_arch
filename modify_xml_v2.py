import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改 quick-deploy.xml
1. 将 APP39/40 迁移到 TcClusterJiTuan4 (APP31~40, 10台全连接)
2. 新增 APP53/54 (TcClusterTest)
3. 新增 APP55/56 (TcClusterHaiWai)
"""

from lxml import etree

def parse_xml(filepath):
    """解析 XML 文件"""
    parser = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    tree = etree.parse(filepath, parser)
    return tree

def get_component(root, component_id, machine_name):
    """获取指定的 component 元素"""
    xpath = f'//component[@id="{component_id}" and @machineName="{machine_name}"]'
    elements = root.xpath(xpath)
    return elements[0] if elements else None

def remove_connectedTo(component, target_component=None, target_machine=None):
    """删除 component 的 connectedTo 子元素"""
    for ct in component.findall('connectedTo'):
        if target_component and ct.get('component') != target_component:
            continue
        if target_machine and ct.get('machineName') != target_machine:
            continue
        component.remove(ct)

def add_connectedTo(component, target_component, target_machine):
    """添加 connectedTo 子元素"""
    ct = etree.SubElement(component, 'connectedTo')
    ct.set('component', target_component)
    ct.set('machineName', target_machine)
    return ct

def modify_app39_40_to_jituan4(root):
    """修改 APP39/40 到 TcClusterJiTuan4"""
    print("  修改 APP39/40 到 TcClusterJiTuan4...")
    
    # APP31~40 列表
    jituan4_apps = [f'APP{i}' for i in range(31, 41)]
    
    for app in ['APP39', 'APP40']:
        # 1. 修改 Web Tier 连接
        web = get_component(root, 'fnd0_j2ee_tcwebtier', app)
        if web is not None:
            # 删除所有 fnd0_serverManager 连接
            remove_connectedTo(web, target_component='fnd0_serverManager')
            
            # 添加 APP31~40 的连接
            for target_app in jituan4_apps:
                add_connectedTo(web, 'fnd0_serverManager', target_app)
            print(f"    ✓ {app} Web Tier → 连接 APP31~40 ({len(jituan4_apps)}个)")
        
        # 2. 修改 Pool Cluster ID
        pool = get_component(root, 'fnd0_serverManager', app)
        if pool is not None:
            for prop in pool.findall('property'):
                if prop.get('id') == 'fnd0_serverManagerDisplayClusterId':
                    prop.set('value', 'TcClusterJiTuan4')
                    print(f"    ✓ {app} Pool → ClusterId = TcClusterJiTuan4")
            
            # 同时更新 serverPoolId 和 service name (可选，保持一致性)
            for prop in pool.findall('property'):
                if prop.get('id') == 'fnd0_serverPoolId':
                    prop.set('value', f'Pool{app}')
                elif prop.get('id') == 'fnd0_serverPoolManager_service':
                    prop.set('value', f'Teamcenter Server Manager config1_Pool{app}')

def create_web_component(app_name, cluster_id, pool_apps):
    """创建 Web Tier 组件"""
    comp = etree.Element('component')
    comp.set('id', 'fnd0_j2ee_tcwebtier')
    comp.set('machineName', app_name)
    comp.set('platform', 'wntx64')
    comp.set('deploymentStatus', 'Pending Install')
    
    props = {
        'fnd0_j2ee_4tierURI': f'http://{app_name}:7001/tc',
        'fnd0_j2ee_JMXRMIPort': '8089',
        'fnd0_j2ee_LogVolumeName': 'LogVol1',
        'fnd0_j2ee_applicationName': f'TcWeb{app_name[3:]}',
        'fnd0_j2ee_deployableFileName': 'tc',
        'fnd0_j2ee_serviceName': 'Teamcenter WebTier',
        'fnd0_j2ee_sessionTimeOut': '1440',
        'fnd0_j2ee_tcwebtier.port': '7001',
        'fnd0_j2ee_tcwebtier.protocol': 'http',
        'fnd0_j2ee_tcwebtierInstallationPath': 'D:\\PLM\\Siemens\\Teamcenter2512\\tc_root',
        'fnd0_j2ee_treeCachePeersHost': app_name,
        'fnd0_tcJavaConnectionName': f'TcWeb{app_name[3:]}',
        'fnd0_tcJavaConnectionTag': 'Tag1',
        'fnd0_webTierCustomBaseLogFileLocation': '%USERPROFILE%\\Siemens\\logs',
        'fnd0_webTierCustomBaseUnixLogFileLocation': '$HOME/Siemens/logs'
    }
    
    for pid, pval in props.items():
        prop = etree.SubElement(comp, 'property')
        prop.set('id', pid)
        prop.set('value', pval)
    
    # 连接: microservice + serverManagers + servermgrconsole
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_microservice')
    ct.set('machineName', 'MSF01')
    
    for pool_app in pool_apps:
        ct = etree.SubElement(comp, 'connectedTo')
        ct.set('component', 'fnd0_serverManager')
        ct.set('machineName', pool_app)
    
    ct = etree.SubElement(comp, 'connectedTo')
    ct.set('component', 'fnd0_servermgrconsole')
    ct.set('machineName', 'APP01')
    
    return comp

def create_pool_component(app_name, cluster_id):
    """创建 Pool (Server Manager) 组件"""
    comp = etree.Element('component')
    comp.set('id', 'fnd0_serverManager')
    comp.set('machineName', app_name)
    comp.set('platform', 'wntx64')
    comp.set('deploymentStatus', 'Pending Install')
    
    props = {
        'fnd0_SSLConfigured': 'false',
        'fnd0_TECSAdminPort': '8084',
        'fnd0_assignmentServicePort': '8086',
        'fnd0_availableServerAt': '0700 3,1700 2',
        'fnd0_config_id': 'config1',
        'fnd0_customBaseLogFileLocation': '%USERPROFILE%\\Siemens\\logs',
        'fnd0_customBaseUnixLogFileLocation': '$HOME/Siemens/logs',
        'fnd0_isFirstInstance': 'false',
        'fnd0_jmxAdaptorPort': '8088',
        'fnd0_loginsPerMinute': '0',
        'fnd0_maxServersCount': '30',
        'fnd0_minWarmServersCount': '1',
        'fnd0_muxPort': '8087',
        'fnd0_serverHost': app_name,
        'fnd0_serverManagerDisplayClusterId': cluster_id,
        'fnd0_serverManagerInstallationPath': 'D:\\PLM\\Siemens\\Teamcenter2512\\tc_root',
        'fnd0_serverManagerMUXUrl': f'http://{app_name}:8087',
        'fnd0_serverManagerProtocol': 'http',
        'fnd0_serverManagerTECSHostAlias': app_name,
        'fnd0_serverPoolId': f'Pool{app_name}',
        'fnd0_serverPoolManager_service': f'Teamcenter Server Manager config1_Pool{app_name}',
        'fnd0_startUpMode': 'fnd0_commandLine'
    }
    
    for pid, pval in props.items():
        prop = etree.SubElement(comp, 'property')
        prop.set('id', pid)
        prop.set('value', pval)
    
    # 连接: servermgrconsole + serverpool_DBConfig + tcdbserver
    for target_comp, target_machine in [
        ('fnd0_servermgrconsole', 'APP01'),
        ('fnd0_serverpool_DBConfig', 'DBSCAN'),
        ('fnd0_tcdbserver', 'DBSCAN')
    ]:
        ct = etree.SubElement(comp, 'connectedTo')
        ct.set('component', target_comp)
        ct.set('machineName', target_machine)
    
    return comp

def add_new_cluster(root, app_list, cluster_id):
    """为新的集群添加 Web 和 Pool 组件"""
    print(f"  添加集群 {cluster_id} ({', '.join(app_list)})...")
    
    for app in app_list:
        # 创建 Web Tier
        web_comp = create_web_component(app, cluster_id, app_list)
        root.append(web_comp)
        
        # 创建 Pool
        pool_comp = create_pool_component(app, cluster_id)
        root.append(pool_comp)
        
        print(f"    ✓ 创建 {app} Web Tier + Pool")
    
    print(f"    ✓ 已添加 {len(app_list)*2} 个新组件")
    return root

def main():
    import os as _os
    if len(sys.argv) >= 2:
        input_file = _os.path.abspath(sys.argv[1])
    else:
        _base = _os.path.dirname(_os.path.abspath(__file__))
        _xmls = sorted([f for f in _os.listdir(_base) if f.lower().endswith('.xml')])
        if len(_xmls) != 1:
            print(f'用法: python {__file__} [XML路径]  或把 .xml 放在脚本目录')
            sys.exit(1)
        input_file = _os.path.join(_base, _xmls[0])
    output_file = input_file.replace('.xml', '_modified.xml')
    
    print("=" * 60)
    print("修改 quick-deploy.xml")
    print("=" * 60)
    
    print("\n[1/3] 解析 XML...")
    tree = parse_xml(input_file)
    root = tree.getroot()
    
    print("\n[2/3] 修改 APP39/40 → TcClusterJiTuan4")
    modify_app39_40_to_jituan4(root)
    
    print("\n[3/3] 添加新集群组件...")
    # APP53/54 → TcClusterTest
    add_new_cluster(root, ['APP53', 'APP54'], 'TcClusterTest')
    
    # APP55/56 → TcClusterHaiWai
    add_new_cluster(root, ['APP55', 'APP56'], 'TcClusterHaiWai')
    
    print("\n写入文件...")
    tree.write(output_file, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！输出文件: {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
