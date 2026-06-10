# dc_qdxml_to_arch

Teamcenter Quick Deploy XML → Architecture Visualization Tool

Parse a TC Quick Deploy XML file and generate a self-contained interactive HTML architecture diagram with component statistics, cluster topology, and full-mesh connection visualization.

## Features

- **One-command generation**: Drop an XML, run the tool, get a rich HTML page
- **Smart classification**: Auto-categorizes 30+ component types into 14 infrastructure groups (FSC, DB, Dispatcher, VIS, TCCS, Rich Client, etc.)
- **Cluster topology**: Renders 8 predefined clusters (JiTuan1-4, HaiWai, XinJishuYuan, JiChuYuan, JieKou) with SM/WT layout
- **Full-mesh detection**: Identifies full-mesh WT→SM connections within clusters; displays as a collapsed band ("Full Connection NxN") instead of spaghetti lines
- **Interactive click-to-reveal**: Click a Web Tier node to reveal its individual SM connections; click again or click outside to hide
- **Pure BL Server extraction**: Automatically extracts BL servers without SM/WT (e.g. DC01, DISP01, DISP02) into a separate "Single BL Server" group
- **Statistics dashboard**: Infra Overview, Component Details (with category row-span), and Cluster summary tables
- **Light/Dark theme**: Toggle with button; preference saved to localStorage
- **Cache FSC display**: Non-master FSC cache servers shown in a sorted grid
- **JSON data export**: Also outputs `arch_data.json` for downstream tool consumption
- **Zero dependencies**: Pure Python stdlib — no pip install needed

## Usage

### Python Script

```bash
# Auto-detect single .xml in current directory
python dc_qdxml_to_arch.py

# Specify input XML
python dc_qdxml_to_arch.py path/to/config.xml

# Specify input and output
python dc_qdxml_to_arch.py config.xml my_arch.html
```

### Standalone EXE

```bash
# Same interface, no Python needed
dc_qdxml_to_arch.exe config.xml
```

### Output

| File | Description |
|------|-------------|
| `arch.html` | Self-contained interactive architecture diagram |
| `arch_data.json` | Structured classification data (JSON) |

## Architecture Diagram Layout

```
┌──────────────────────────────────────────────────────────┐
│ Infrastructure Groups (FSC, DB, AW, Solr, Dispatcher,   │
│   VIS, TCCS, Rich Client 2/4-Tier, Mass, Single BL,    │
│   MSF, License, Vault)                                   │
├──────────────────────────────────────────────────────────┤
│ Clusters                                                 │
│  ┌─ TcClusterJiTuan1 ─────────────────────────────────┐ │
│  │  SM: [APP01] [APP02] ... [APP10]                    │ │
│  │  ┌──── Full Connection 10x10 ────┐                  │ │
│  │  │  (click WT to reveal links)   │                  │ │
│  │  └───────────────────────────────┘                  │ │
│  │  WT: [APP01] [APP02] ... [APP10]                    │ │
│  └─────────────────────────────────────────────────────┘ │
│  ...more clusters...                                     │
├──────────────────────────────────────────────────────────┤
│ Cache FSC (Non-Master, sorted A-Z)                       │
└──────────────────────────────────────────────────────────┘
```

## Cluster Definitions

| Cluster | APP Range | Color |
|---------|-----------|-------|
| TcClusterJiTuan1 | APP01-10 | Teal |
| TcClusterJiTuan2 | APP11-20 | Red |
| TcClusterJiTuan3 | APP21-30 | Blue |
| TcClusterJiTuan4 | APP31-38 | Sage |
| TcClusterHaiWai | APP39-40 | Gold |
| TcClusterXinJishuYuan | APP41-42 | Plum |
| TcClusterJiChuYuan | APP43-44 | Mint |
| TcClusterJieKou | APP45-52 | Amber |

## Component Categories

| Category | Key | Components |
|----------|-----|------------|
| FSC | fsc | FSC Server (Master), FSC Keys, FSC Group |
| Database | db | TCDB Server, Pool DB Config |
| AW/Client | aw | HTTPS Config, Client Builder, Gateway |
| Solr/Search | solr | Indexing Engine, ZooKeeper, FTS Indexer |
| Dispatcher | dispatcher | Dispatcher Module, Scheduler, Client |
| VIS | vis | VIS Pool Assigner, VIS Server Manager |
| TCCS | tccs | TCCS Client (matched with Rich Client machines) |
| 2-Tier Client | client_2tier | 2-Tier Rich Client |
| 4-Tier Client | client_4tier | 4-Tier Rich Client |
| Mass Client | client_mass | EDA Client |
| Single BL | single_bl | Pure BL Servers (no SM/WT) |
| MSF | msf | Microservice, Container Config |
| License | license | License Server |
| Vault | vault | Vault Server |

## Building the EXE

Requires Python 3.13+ and PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile dc_qdxml_to_arch.py
```

Output: `output/dc_qdxml_to_arch.exe` (~8MB)

To customize the output directory:

```bash
pyinstaller --onefile --distpath output dc_qdxml_to_arch.py
```

## File Structure

```
dc_qdxml_to_arch/
├── dc_qdxml_to_arch.py    # Main Python script (zero dependencies)
├── output/
│   └── dc_qdxml_to_arch.exe   # Standalone Windows EXE
└── README.md
```

## Related Projects

- **[dc_qdxml_validator](https://github.com/fei7yang/dc_qdxml_validator)** — Connection validation rules and XML config checker for TC Quick Deploy

## License

Internal tool — for Teamcenter deployment architecture review.
