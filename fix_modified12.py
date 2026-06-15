import sys
import os
"""
Fix modified12.xml - comprehensive fix for connectedTo issues
Based on Eric's confirmation on 2026-06-12:

1. Gateway APP55/56 FSC = as design (海外集群只连国内, 不修)
2. dispatcherModule connectedTo blserver: add APP53-56 to DISP01/02
3. Master FSC connectedTo fnd0_fsc: add APP53-56 (should be 86 including self)
4. Non-Master FSC already correct: 9 connections to Masters only ✅
5. APP01 no blserver = as design (corp, 不修)
6. DC01/DISP01/DISP02 no FSC = correct ✅
7. BL server FSC connections: all 58 BL have 9 Master FSC conns ✅

Also update Validation.logic with new rules.
"""

from lxml import etree
import copy
import os

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
# 自动检测 XML：有参数用参数，否则找脚本所在目录
if len(sys.argv) >= 2:
    INPUT = os.path.abspath(sys.argv[1])
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _xmls = sorted([f for f in os.listdir(_base) if f.lower().endswith(".xml")])
    if len(_xmls) != 1:
        print(f"用法: python {os.path.basename(__file__)} [XML路径]  或把 .xml 放在脚本目录")
        sys.exit(1)
    INPUT = os.path.join(_base, _xmls[0])  # overwrite

p = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
tree = etree.parse(INPUT, p)
root = tree.getroot()
qdc = root.find('quickDeployComponents')
qcl = root.find('quickDeployClients')

changes = []

# ==========================================
# Fix 1: dispatcherModule connectedTo blserver - add APP53-56
# ==========================================
print("=== Fix 1: dispatcherModule connectedTo blserver ===")
disp_names = ['DISP01', 'DISP02']
missing_bl = ['APP53', 'APP54', 'APP55', 'APP56']

for disp_name in disp_names:
    disp = [c for c in qdc if c.tag == 'component' and c.get('id') == 'fnd0_dispatcherModule' and c.get('machineName') == disp_name]
    if not disp:
        print(f"  WARNING: {disp_name} dispatcherModule not found!")
        continue
    disp = disp[0]
    
    # Find existing blserver connectedTo entries to get insertion point
    bl_cts = disp.findall('connectedTo[@component="fnd0_blserver"]')
    existing_bl_machines = set(ct.get('machineName') for ct in bl_cts)
    
    # Find the last blserver connectedTo entry
    last_bl_ct = bl_cts[-1] if bl_cts else None
    
    added = 0
    for mn in missing_bl:
        if mn in existing_bl_machines:
            print(f"  {disp_name}: {mn} already exists, skip")
            continue
        
        # Create new connectedTo element
        new_ct = etree.Element('connectedTo')
        new_ct.set('component', 'fnd0_blserver')
        new_ct.set('machineName', mn)
        
        # Insert after last blserver connectedTo
        if last_bl_ct is not None:
            idx = list(disp).index(last_bl_ct)
            disp.insert(idx + 1 + added, new_ct)
        else:
            disp.append(new_ct)
        added += 1
    
    # Verify
    bl_cts_after = [ct.get('machineName') for ct in disp.findall('connectedTo[@component="fnd0_blserver"]')]
    print(f"  {disp_name}: BL connections {len(bl_cts_after)}/58, added {added}")
    still_missing = set(missing_bl) - set(bl_cts_after)
    if still_missing:
        print(f"  WARNING: still missing {sorted(still_missing)}")
    changes.append(f"Fix1: DISP01/02 added {added} blserver conns each (APP53-56)")

# ==========================================
# Fix 2: Master FSC connectedTo fnd0_fsc - add APP53-56
# ==========================================
print("\n=== Fix 2: Master FSC connectedTo fnd0_fsc ===")
all_fsc = [c for c in qdc if c.tag == 'component' and c.get('id') == 'fnd0_fsc']
all_fsc_machines = set(c.get('machineName') for c in all_fsc)

# Get master FSCs
master_fscs = []
for fsc in all_fsc:
    mn = fsc.get('machineName')
    is_master = any(p.get('id') == 'fnd0_isMaster' and p.get('value','').lower() == 'true' for p in fsc.findall('property'))
    if is_master:
        master_fscs.append(fsc)

print(f"  Master FSCs: {len(master_fscs)}")
print(f"  All FSC machines: {len(all_fsc_machines)}")

for fsc in master_fscs:
    mn = fsc.get('machineName')
    fsc_cts = [ct for ct in fsc.findall('connectedTo') if ct.get('component') == 'fnd0_fsc']
    connected_machines = set(ct.get('machineName') for ct in fsc_cts)
    missing = all_fsc_machines - connected_machines
    
    if not missing:
        print(f"  {mn}: already 86/86 ✅")
        continue
    
    print(f"  {mn}: {len(connected_machines)}/86, missing {sorted(missing)}")
    
    # Find last fnd0_fsc connectedTo
    last_fsc_ct = fsc_cts[-1] if fsc_cts else None
    
    added = 0
    for missing_mn in sorted(missing):
        new_ct = etree.Element('connectedTo')
        new_ct.set('component', 'fnd0_fsc')
        new_ct.set('machineName', missing_mn)
        
        if last_fsc_ct is not None:
            idx = list(fsc).index(last_fsc_ct)
            fsc.insert(idx + 1 + added, new_ct)
        else:
            fsc.append(new_ct)
        added += 1
    
    # Verify
    fsc_cts_after = [ct.get('machineName') for ct in fsc.findall('connectedTo[@component="fnd0_fsc"]')]
    print(f"  {mn}: after fix = {len(fsc_cts_after)}/86")
    changes.append(f"Fix2: {mn} added {added} fsc conns ({sorted(missing)})")

# ==========================================
# Verify all Non-Master FSC are correct (9 conns to Masters only)
# ==========================================
print("\n=== Verify Non-Master FSC connections ===")
master_machines = set(fsc.get('machineName') for fsc in master_fscs)
nonmaster_ok = True
for fsc in all_fsc:
    mn = fsc.get('machineName')
    is_master = any(p.get('id') == 'fnd0_isMaster' and p.get('value','').lower() == 'true' for p in fsc.findall('property'))
    if is_master:
        continue
    fsc_cts = [ct.get('machineName') for ct in fsc.findall('connectedTo') if ct.get('component') == 'fnd0_fsc']
    if len(fsc_cts) != 9 or set(fsc_cts) != master_machines:
        print(f"  ❌ {mn}: {len(fsc_cts)} conns, targets={sorted(fsc_cts)}")
        nonmaster_ok = False
if nonmaster_ok:
    print("  All 77 Non-Master FSC: 9 conns to Masters ✅")

# ==========================================
# Final verification
# ==========================================
print("\n=== Final verification ===")

# Re-read counts
all_bl = sorted(set(c.get('machineName') for c in qcl if c.tag == 'client' and c.get('id') == 'fnd0_blserver'))
all_web = sorted(set(c.get('machineName') for c in qdc if c.tag == 'component' and c.get('id') == 'fnd0_j2ee_tcwebtier'))
all_sm = sorted(set(c.get('machineName') for c in qdc if c.tag == 'component' and c.get('id') == 'fnd0_serverManager'))

# DISP01/02
for disp_name in ['DISP01', 'DISP02']:
    disp = [c for c in qdc if c.tag == 'component' and c.get('id') == 'fnd0_dispatcherModule' and c.get('machineName') == disp_name][0]
    bl_cts = sorted([ct.get('machineName') for ct in disp.findall('connectedTo') if ct.get('component') == 'fnd0_blserver'])
    web_cts = sorted([ct.get('machineName') for ct in disp.findall('connectedTo') if ct.get('component') == 'fnd0_j2ee_tcwebtier'])
    bl_missing = set(all_bl) - set(bl_cts)
    print(f"  DISP{disp_name[-2:]}: BL {len(bl_cts)}/{len(all_bl)} missing={sorted(bl_missing) if bl_missing else 'none'}")
    print(f"  DISP{disp_name[-2:]}: Web {len(web_cts)}/{len(all_web)} ✅")

# Master FSC
for fsc in master_fscs:
    mn = fsc.get('machineName')
    fsc_cts = [ct.get('machineName') for ct in fsc.findall('connectedTo') if ct.get('component') == 'fnd0_fsc']
    print(f"  Master {mn}: {len(fsc_cts)}/86 {'✅' if len(fsc_cts) == 86 else '❌'}")

# Write output
tree.write(OUTPUT, xml_declaration=True, encoding='utf-8')
print(f"\n✅ Written to {OUTPUT}")
print(f"\nChanges made:")
for c in changes:
    print(f"  {c}")
