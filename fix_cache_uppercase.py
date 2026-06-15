"""统一 Quick Deploy XML 中所有 cache 机器名为大写"""
import sys, os, re, shutil
from pathlib import Path

# 自动检测 XML
if len(sys.argv) >= 2:
    xml_path = Path(os.path.abspath(sys.argv[1]))
else:
    _base = Path(__file__).parent
    _xmls = sorted(_base.glob('*.xml'))
    if len(_xmls) != 1:
        print(f'用法: python {Path(__file__).name} [XML路径]  或把 .xml 放在脚本目录')
        sys.exit(1)
    xml_path = _xmls[0]

backup_path = xml_path.with_suffix('.xml_backup_uppercase')

# 备份
if not backup_path.exists():
    shutil.copy2(xml_path, backup_path)
    print(f'已备份: {backup_path}')

content = xml_path.read_text(encoding='utf-8')

# 需要大写化的 cache 名称模式（混合大小写的）
# 匹配: XACache01, BACache01, HunCache01, JNCache01, USCache01, FZCache01,
#       INDCache01, THCache01, CSCache01, CZCache01, HFCache01, ZZCache01
# 不匹配已经是全大写的: XACACHE02-06, BACACHE01-02

cache_prefixes = [
    'XACache', 'BACache', 'HunCache', 'JNCache', 'USCache',
    'FZCache', 'INDCache', 'THCache', 'CSCache', 'CZCache',
    'HFCache', 'ZZCache'
]

total_replacements = 0

# 1. 替换 machineName="XxxCacheNN" 属性值
for prefix in cache_prefixes:
    upper_prefix = prefix.upper()
    pattern = f'machineName="{prefix}(\\d+)"'
    matches = re.findall(pattern, content)
    if matches:
        new_content = re.sub(pattern, f'machineName="{upper_prefix}\\1"', content)
        count = len(matches)
        total_replacements += count
        print(f'  machineName: {prefix}NN → {upper_prefix}NN ({count}处)')
        content = new_content

# 2. 替换 FSC_XxxCacheNN_infodba (fnd0_fscServerID 和 fnd0_fsc_service)
for prefix in cache_prefixes:
    upper_prefix = prefix.upper()
    pattern = f'FSC_{prefix}(\\d+)_infodba'
    matches = re.findall(pattern, content)
    if matches:
        new_content = re.sub(pattern, f'FSC_{upper_prefix}\\1_infodba', content)
        count = len(matches)
        total_replacements += count
        print(f'  FSC_ServerID: FSC_{prefix}NN → FSC_{upper_prefix}NN ({count}处)')
        content = new_content

# 3. 替换 http://XxxCacheNN:port URL (fnd0_fscHostAlias, fnd0_fscSingleAuthURL, fnd0_fscURL)
for prefix in cache_prefixes:
    upper_prefix = prefix.upper()
    pattern = f'http://{prefix}(\\d+)'
    matches = re.findall(pattern, content)
    if matches:
        new_content = re.sub(pattern, f'http://{upper_prefix}\\1', content)
        count = len(matches)
        total_replacements += count
        print(f'  URL: http://{prefix}NN → http://{upper_prefix}NN ({count}处)')
        content = new_content

# 4. 替换 fnd0_fscHostAlias value="XxxCacheNN"
for prefix in cache_prefixes:
    upper_prefix = prefix.upper()
    pattern = f'value="{prefix}(\\d+)"'
    matches = re.findall(pattern, content)
    if matches:
        new_content = re.sub(pattern, f'value="{upper_prefix}\\1"', content)
        count = len(matches)
        total_replacements += count
        print(f'  HostAlias/URL value: {prefix}NN → {upper_prefix}NN ({count}处)')
        content = new_content

# 写回
xml_path.write_text(content, encoding='utf-8')
print(f'\n完成！共替换 {total_replacements} 处')
print(f'输出: {xml_path}')

# 验证：检查是否还有混合大小写的 cache 名称
remaining = []
for prefix in cache_prefixes:
    pattern = f'{prefix}\\d+'
    found = re.findall(pattern, content)
    if found:
        remaining.extend(found)

if remaining:
    print(f'\n⚠️ 仍有混合大小写 cache 名称: {set(remaining)}')
else:
    print('\n✅ 所有 cache 机器名已统一为大写')

# 验证全大写 cache 名称
all_cache = re.findall(r'[A-Z]+CACHE\d+', content)
unique_cache = sorted(set(all_cache))
print(f'\n全大写 cache 名称 ({len(unique_cache)} 个): {unique_cache}')
