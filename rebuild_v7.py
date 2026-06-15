import sys
import os
#!/usr/bin/env python3
"""
从 backup2 一次性正确重建, 纯文本插入, 保证格式和分组完美。
"""
import re, shutil

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

def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def lines_after(text, marker):
    """返回 marker 最后一次出现的行尾位置"""
    idx = text.rfind(marker)
    if idx == -1: return -1
    return text.find('\n', idx) + 1

def insert_newlines(lines, content):
    return '\n'.join(lines) + '\n' + content

def main():
    text = read(INPUT)
    
    # ===== 1. FSC APP53-56 插入到 fnd0_fsc 组内 =====
    # 找到最后一个 fnd0_fsc component 的 </component>
    pos = lines_after(text, '<component id="fnd0_fsc" machineName="APP20"')
    end = text.find('</component>', pos)
    end += len('</component>')
    if text[end] == '\n': end += 1
    
    fsc_block = ""
    for app in ['APP53','APP54','APP55','APP56']:
        fsc_block += f'''        <component id="fnd0_fsc" machineName="{app}" platform="wntx64" deploymentStatus="Pending Install">
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
        </component>
'''
    text = text[:end] + fsc_block + text[end:]
    print("✓ 1. FSC APP53-56")
    
    # ===== 2. Gateway APP55/56 插入到 gateway 组内 =====
    # 需要全量 FSC 连接
	
    # 收集所有 FSC 机器名
    all_fsc = set()
    for m in re.finditer(r'<component id="fnd0_fsc" machineName="([^"]+)"', text):
        all_fsc.add(m.group(1))
    # 手动加上 APP53-56 (可能还没在文本里)
    for a in ['APP53','APP54','APP55','APP56']:
        all_fsc.add(a)
    
    fsc_lines = '\n'.join([f'            <connectedTo component="fnd0_fsc" machineName="{f}"/>' for f in sorted(all_fsc)])
    
    for app in ['APP55','APP56']:
        vis = 'VIS01' if int(app[3:]) % 2 == 1 else 'VIS02'
        # 插入位置：最后一个 gateway component 的 </component> 之后
        pos = lines_after(text, '<component id="aws2_client_gateway_webtier" machineName="APP02"')
        end = text.find('</component>', pos)
        end += len('</component>')
        if text[end] == '\n': end += 1
        
        gw = f'''        <component id="aws2_client_gateway_webtier" machineName="{app}" platform="wntx64" deploymentStatus="Pending Install">
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
{fsc_lines}
            <connectedTo component="fnd0_j2ee_tcwebtier" machineName="{app}"/>
            <connectedTo component="fnd0_microservice" machineName="MSF01"/>
        </component>
'''
        text = text[:end] + gw + text[end:]
    print("✓ 2. Gateway APP55-56 (全量FSC)")
    
    # ===== 3. Gateway APP01/02/41/42 补 APP53-56 FSC =====
    for app in ['APP01','APP02','APP41','APP42']:
        # 找到该 gateway 的最后一条 fnd0_fsc connectedTo
        start = text.find(f'<component id="aws2_client_gateway_webtier" machineName="{app}"')
        end = text.find('</component>', start)
        block = text[start:end]
        
        # 找到最后一条 fnd0_fsc
        last_fsc_pos = 0
        for m in re.finditer(r'<connectedTo component="fnd0_fsc" machineName="[^"]+"/>', block):
            last_fsc_pos = m.end()
        
        if last_fsc_pos > 0:
            insert_pos = start + last_fsc_pos
            new_fsc = ''
            for a in ['APP53','APP54','APP55','APP56']:
                new_fsc += f'\n            <connectedTo component="fnd0_fsc" machineName="{a}"/>'
            text = text[:insert_pos] + new_fsc + text[insert_pos:]
    print("✓ 3. Gateway APP01/02/41/42 +FSC(APP53-56)")
    
    # ===== 写入 =====
    write(INPUT, text)
    
    # ===== 4. 后续用 lxml 处理 clients 和 全连接 =====
    print("✓ 文本阶段完成, 进入 lxml 阶段...")

if __name__ == '__main__':
    main()
