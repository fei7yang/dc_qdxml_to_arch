import sys
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本级插入：恢复 backup2 后，用纯文本方式插入新组件，保证格式完美。
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

# ===== 模板 =====

def corp_template(app):
    """BL Server corporateserver 模板 (从 APP01 精确复制并替换)"""
    return f'''        <component id="fnd0_corporateserver" machineName="{app}" platform="wntx64" deploymentStatus="Pending Install">
            <property id="fnd0_ReadExprMgrEndTime" value=""/>
            <property id="fnd0_ReadExprMgrSleepTime" value="10"/>
            <property id="fnd0_ReadExprMgrStartTime" value=""/>
            <property id="fnd0_corporateserver_osUserName" value=".\\infodba"/>
            <property id="fnd0_corporateserver_osUserPassword" value="VuZeYRVHbwBt2q7ieWb20PBsHYTEkR2hpclHKKLssaE17Fa8wzzd+dUTCvniU29V" encrypted="true"/>
            <property id="fnd0_corporateserver_tcAdminPasswordChangeOptions" value="Deployment Center"/>
            <property id="fnd0_enableReadExpMgrService" value="true"/>
            <property id="fnd0_enableRevCfgAccService" value="true"/>
            <property id="fnd0_genClientCache" value="true"/>
            <property id="fnd0_genServerCache" value="true"/>
            <property id="fnd0_ms_tcoo_UseSponsoredAuth" value="false"/>
            <property id="fnd0_nxgraphicsbuilder_CorpServer_nxInstallationPath" value="C:\\Program Files\\Siemens\\NX"/>
            <property id="fnd0_nxgraphicsbuilder_basePorts" value="2300"/>
            <property id="fnd0_nxgraphicsbuilder_noOfPorts" value="1"/>
            <property id="fnd0_passwordSecurityDir" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root\\security"/>
            <property id="fnd0_tcAdminPassword" value="G+a/koyeHk2X0fYE76az+EaQYJHQe2V6NPvC2PfN5HedOa74R1t/7fiztsgDXdc0LbPHt9Ig0mcZkWV54B2zDw==" encrypted="true"/>
            <property id="fnd0_tcAdminUser" value="infodba"/>
            <property id="fnd0_tcCorporateServerInstallationPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root"/>
            <property id="fnd0_tcDataPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_data"/>
            <property id="fnd0_tcVolumeDirPath" value="C:\\Siemens\\Teamcenter2512\\volumes\\DefaultVolume"/>
            <property id="fnd0_tcVolumeName" value="DefaultVolume"/>
            <property id="fnd0_tcdata_datasetName" value="dc_delta_tc_data_Env_004"/>
            <property id="fnd0_unixClientTransientVolumeDir" value="/tmp/transientVolume"/>
            <property id="fnd0_windowsClientTransientVolumeDir" value="c:\\temp\\transientVolume"/>
            <connectedTo component="aws2_ftsIndexer" machineName="INDX01"/>
            <connectedTo component="aws2_indexingengine" machineName="SOLR02"/>
            <connectedTo component="aws2_indexingengine" machineName="SOLR03"/>
            <connectedTo component="aws2_indexingengine" machineName="SOLR01"/>
            <connectedTo component="fnd0_fsc" machineName="{app}"/>
            <connectedTo component="fnd0_fsc_keys" machineName="fsc">
                <property id="fnd0_fsc_keys_instance" value="FSC Keys Instance1"/>
            </connectedTo>
            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="{app}"/>
            <connectedTo component="fnd0_licensingserver" machineName="LIC01"/>
            <connectedTo component="fnd0_microservice" machineName="MSF01"/>
            <connectedTo component="fnd0_tcdbserver" machineName="DBSCAN"/>
        </component>'''

def fsc_template(app):
    """FSC 模板 (从 APP40 精确复制并替换)"""
    return f'''        <component id="fnd0_fsc" machineName="{app}" platform="wntx64" deploymentStatus="Pending Install">
            <property id="fnd0_backUpEncryptionKey" value=""/>
            <property id="fnd0_cloudVolumeName" value="DefaultCloudVolume"/>
            <property id="fnd0_cloudserviceID" value="10001"/>
            <property id="fnd0_dssAccessKeyId" value=""/>
            <property id="fnd0_dssAccountId" value=""/>
            <property id="fnd0_dssEndpointURL" value="dss.us-east-1.sws.siemens.com"/>
            <property id="fnd0_dssKeystorePassword" value="VuZeYRVHbwBt2q7ieWb20PBsHYTEkR2hpclHKKLssaGrZ5JizcCO4rxiG6RrknCn" encrypted="true"/>
            <property id="fnd0_dssSAMEndpointURL" value="sam.us-east-1.sws.siemens.com"/>
            <property id="fnd0_dssSamClientId" value=""/>
            <property id="fnd0_dssSamClientSecret" value=""/>
            <property id="fnd0_dssSecretAccessKey" value="Oz7gT+V3546ydwPEqsTxRMNNNkX2jRw5gMnWcNheLEV0f1e4IyG049DHrg1uT7+uXMpsprRTDaXyf6TertOzNA==" encrypted="true"/>
            <property id="fnd0_dssUserId" value=""/>
            <property id="fnd0_dssVaultID" value=""/>
            <property id="fnd0_enableDiffLoginURL" value="false"/>
            <property id="fnd0_enableEnhancedTicketAuth" value="false"/>
            <property id="fnd0_fccPartialFileReadCacheMaxSize" value="3000"/>
            <property id="fnd0_fccReadCacheMaxSize" value="1000"/>
            <property id="fnd0_fccToTcSSOverrideLoginURL" value=""/>
            <property id="fnd0_fccUNIXCacheDir" value="/tmp/$USER/FCCCache"/>
            <property id="fnd0_fccWindowsCacheDir" value="$HOME\\FCCCache"/>
            <property id="fnd0_fccWriteCacheMaxSize" value="1000"/>
            <property id="fnd0_fscAssignFilestoreGroup" value=""/>
            <property id="fnd0_fscHostAlias" value="{app}"/>
            <property id="fnd0_fscInstallationPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root"/>
            <property id="fnd0_fscReadCacheDir" value="$HOME\\FSCCache"/>
            <property id="fnd0_fscReadCacheMaxSize" value="10"/>
            <property id="fnd0_fscServerID" value="FSC_{app}_infodba"/>
            <property id="fnd0_fscServerPort" value="4544"/>
            <property id="fnd0_fscServerProtocol" value="http"/>
            <property id="fnd0_fscSingleAuthURL" value="http://{app}:4545"/>
            <property id="fnd0_fscToTcSSOverrideLoginURL" value=""/>
            <property id="fnd0_fscUNIXReadCacheDir" value="/tmp/FSCCache"/>
            <property id="fnd0_fscUNIXWriteCacheDir" value="/tmp/FSCCache"/>
            <property id="fnd0_fscURL" value="http://{app}:4544"/>
            <property id="fnd0_fscWriteCacheDir" value="$HOME\\FSCCache"/>
            <property id="fnd0_fscWriteCacheMaxSize" value="10"/>
            <property id="fnd0_fsc_machinePassword" value="Oz7gT+V3546ydwPEqsTxRMNNNkX2jRw5gMnWcNheLEUZtLFrRppSgdybUIigRVZG" encrypted="true"/>
            <property id="fnd0_fsc_machineUser" value=".\\infodba"/>
            <property id="fnd0_fsc_service" value="Teamcenter FSC Service FSC_{app}_infodba"/>
            <property id="fnd0_isCloudVolumeHost" value=""/>
            <property id="fnd0_isCustomKeysEnabledForCloud" value="false"/>
            <property id="fnd0_isMaster" value="false"/>
            <property id="fnd0_isSingleAuthFSC" value="false"/>
            <property id="fnd0_osUserOptions" value="thisAccount"/>
            <property id="fnd0_primaryEncryptionKey" value=""/>
            <property id="fnd0_singleAuthFSCPort" value="4545"/>
            <property id="fnd0_useDSSLite" value="false"/>
            <connectedTo component="fnd0_fsc" machineName="FSC08"/>
            <connectedTo component="fnd0_fsc" machineName="FSC05"/>
            <connectedTo component="fnd0_fsc" machineName="FSC06"/>
            <connectedTo component="fnd0_fsc" machineName="FSC02"/>
            <connectedTo component="fnd0_fsc" machineName="FSC03"/>
            <connectedTo component="fnd0_fsc" machineName="FSC01"/>
            <connectedTo component="fnd0_fsc" machineName="FSC07"/>
            <connectedTo component="fnd0_fsc" machineName="APP01"/>
            <connectedTo component="fnd0_fsc" machineName="FSC04"/>
            <connectedTo component="fnd0_fsc_group" machineName="fsc">
                <property id="fnd0_fsc_group_instance" value="FSC Group Instance1"/>
            </connectedTo>
            <connectedTo component="fnd0_fsc_keys" machineName="fsc">
                <property id="fnd0_fsc_keys_instance" value="FSC Keys Instance1"/>
            </connectedTo>
        </component>'''

def richclient_template(app):
    """2tierrichclient client 模板"""
    return f'''        <client id="fnd0_2tierrichclient" machineName="{app}" massDeploy="false" platform="wntx64" deploymentStatus="Pending Install" createTemplateClient="false" useTemplateClient="false">
            <property id="fnd0_2tierTempFolder" value="D:\\temp"/>
            <property id="fnd0_2tierrichclient.appSupportedList" value="selectedApps"/>
            <property id="fnd0_2tierrichclient.massDeployCheck" value="false"/>
            <property id="fnd0_rac2tEnvConnectionName" value="2512_2tier"/>
            <property id="fnd0_rac2tEnvConnectionTag" value=""/>
            <property id="fnd0_rac2tIsSingleServer" value="true"/>
            <property id="fnd0_rac2tPortalViewerLicenseLevel" value="Base"/>
            <property id="fnd0_tc2TierRACInstallationPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root"/>
            <connectedTo component="fnd0_serverManager" machineName="{app}"/>
            <connectedTo component="fnd0_corporateserver" machineName="{app}"/>
            <connectedTo component="fnd0_tcdbserver" machineName="DBSCAN"/>
            <package id="cfg0configurator" deploymentStatus="Pending Install"/>
            <package id="cfg1configurator" deploymentStatus="Pending Install"/>
            <package id="rac_ets" deploymentStatus="Pending Install"/>
            <package id="smc0psmcfgsupport" deploymentStatus="Pending Install"/>
            <package id="tm0tsm" deploymentStatus="Pending Install"/>
            <package id="vendormanagement" deploymentStatus="Pending Install"/>
        </client>'''

def gateway_template(app):
    """Gateway webtier 模板 - 基于 APP41 格式，替换关键字段"""
    vis = 'VIS01' if int(app[3:]) % 2 == 1 else 'VIS02'
    # 生成所有86个 FSC 连接
    fsc_list = [f'FSC0{i}' for i in range(1, 9)]
    fsc_list += [f'APP{i}' for i in range(1, 53)]  # APP01-52
    # 添加新增的 APP53-56
    cache_list = ['JNCache01', 'THCache02', 'INDCache02', 'USCache01', 'USCache02',
                  'XACACHE03', 'XACACHE04', 'XACACHE05', 'XACACHE06', 'ZZCache01',
                  'CSCache01', 'THCache01', 'HFCache01', 'BACache01', 'BACache02',
                  'CZCache01', 'HunCache02', 'FZCache01', 'XACache01', 'INDCache01',
                  'XACACHE02', 'HunCache01']
    fsc_list += cache_list
    fsc_list += ['APP53', 'APP54', 'APP55', 'APP56']  # 新增
    
    fsc_conns = '\n'.join([f'            <connectedTo component="fnd0_fsc" machineName="{f}"/>' for f in fsc_list])
    
    return f'''        <component id="aws2_client_gateway_webtier" machineName="{app}" platform="wntx64" deploymentStatus="Pending Install">
            <property id="aws2_Tc4TierConOptions" value="directConnectionToWebtier"/>
            <property id="aws2_client_gateway_HostAlias" value="{app}"/>
            <property id="aws2_client_gateway_app_url" value="http://:3000/"/>
            <property id="aws2_client_gateway_digitalProductExperience" value="true"/>
            <property id="aws2_client_gateway_enable_csp" value="true"/>
            <property id="aws2_client_gateway_ingress_url" value=""/>
            <property id="aws2_client_gateway_productExcellenceProgram" value="true"/>
            <property id="aws2_client_gateway_url_prefix" value="/"/>
            <property id="aws2_client_gateway_webtier_bootstrapClientIP" value=""/>
            <property id="aws2_client_gateway_webtier_gatewayPort" value="3000"/>
            <property id="aws2_client_gateway_webtier_installationPath" value="D:\\PLM\\Siemens\\Teamcenter2512\\tc_root"/>
            <property id="aws2_client_gateway_webtier_maxAge" value="6"/>
            <property id="aws2_client_gateway_webtier_unit" value="Months"/>
            <property id="aws2_client_gateway_webtier_url" value="http://{app}:3000/"/>
            <property id="aws2_client_gateway_webtier_useSSL" value="http"/>
            <property id="aws2_client_gateway_webtier_volumeConnectionOptions" value="useAsBootstrapUrlsOption"/>
            <property id="aws2_client_has_additional_customRoutes" value=""/>
            <property id="aws2_forceSecureAttributeOnCookies" value="false"/>
            <property id="aws2_lb_4tier_deployableFileName" value="tc"/>
            <connectedTo component="aws2_vispoolassigner" machineName="{vis}"/>
{fsc_conns}
            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="{app}"/>
            <connectedTo component="fnd0_microservice" machineName="MSF01"/>
        </component>'''


def insert_after_marker(text, marker, content):
    """在 text 中找到 marker 的最后一次出现位置，在其后插入 content"""
    idx = text.rfind(marker)
    if idx == -1:
        print(f"  ✗ 找不到标记: {marker[:80]}")
        return text
    # 找到 marker 行的结尾
    end_of_line = text.find('\n', idx)
    return text[:end_of_line + 1] + content + '\n' + text[end_of_line + 1:]

def insert_after_last(text, id_pattern, content):
    """找到包含 id_pattern 的最后一行的行尾，插入 content"""
    lines = text.split('\n')
    last_idx = -1
    for i, line in enumerate(lines):
        if id_pattern in line:
            last_idx = i
    if last_idx == -1:
        print(f"  ✗ 找不到: {id_pattern[:80]}")
        return text
    lines.insert(last_idx + 1, content)
    return '\n'.join(lines)

def main():
    print("=" * 60)
    print("文本级插入 — 保证格式完美")
    print("=" * 60)
    
    text = read_file(INPUT)
    
    # --- 1. corporateserver ---
    print("\n[1] fnd0_corporateserver (BL Server)")
    # 找到最后一个 corporateserver component 的 </component> 并在其后插入
    marker = 'fnd0_corporateserver" machineName="APP01"'
    marker_end = '</component>'  # 找到这个 component 的结束标签
    start = text.find(marker)
    # 从这个位置往后找到 </component>
    middle = text[start:]
    end = middle.find('</component>')
    insert_pos = start + end + len('</component>') + 1  # +1 for newline
    
    corps = ['APP39', 'APP40', 'APP53', 'APP54', 'APP55', 'APP56']
    corps_block = '\n'.join([corp_template(a) for a in corps]) + '\n'
    text = text[:insert_pos] + corps_block + text[insert_pos:]
    for a in corps:
        print(f"  ✓ {a}")
    
    # --- 2. fnd0_fsc ---
    print("\n[2] fnd0_fsc")
    # 找最后一个 fnd0_fsc component (APP20)
    marker = 'component id="fnd0_fsc" machineName="APP20"'
    marker_end = '</component>'
    start = text.rfind(marker)  # rfind 找最后一个
    middle = text[start:]
    end = middle.find('</component>')
    insert_pos = start + end + len('</component>') + 1
    
    fscs = ['APP53', 'APP54', 'APP55', 'APP56']
    fsc_block = '\n'.join([fsc_template(a) for a in fscs]) + '\n'
    text = text[:insert_pos] + fsc_block + text[insert_pos:]
    for a in fscs:
        print(f"  ✓ {a}")
    
    # --- 3. fnd0_2tierrichclient ---
    print("\n[3] fnd0_2tierrichclient (client)")
    # 找到 DISP01 的 2tierrichclient </client> 后插入
    marker = 'machineName="DISP01"'
    start = text.find(marker)
    middle = text[start:]
    end = middle.find('</client>')
    insert_pos = start + end + len('</client>') + 1
    
    richs = ['APP53', 'APP54', 'APP55', 'APP56']
    rich_block = '\n'.join([richclient_template(a) for a in richs]) + '\n'
    text = text[:insert_pos] + rich_block + text[insert_pos:]
    for a in richs:
        print(f"  ✓ {a}")
    
    # --- 4. aws2_client_gateway_webtier ---
    print("\n[4] aws2_client_gateway_webtier")
    marker = 'aws2_client_gateway_webtier" machineName="APP02"'
    marker_end = '</component>'
    start = text.find(marker)
    middle = text[start:]
    end = middle.find('</component>')
    insert_pos = start + end + len('</component>') + 1
    
    gws = ['APP55', 'APP56']
    gw_block = '\n'.join([gateway_template(a) for a in gws]) + '\n'
    text = text[:insert_pos] + gw_block + text[insert_pos:]
    for a in gws:
        print(f"  ✓ {a}")
    
    # --- 写入 ---
    print(f"\n[5] 写入: {INPUT}")
    write_file(INPUT, text)
    print(f"  文件大小: {len(text)} 字符")
    print("\n✅ 完成!")

if __name__ == '__main__':
    main()
