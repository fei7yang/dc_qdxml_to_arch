# dc_qdxml_to_arch

Teamcenter Quick Deploy XML → Architecture Visualization Tool

Parse any TC Quick Deploy XML file and generate a self-contained interactive HTML architecture diagram. **No hardcoded cluster definitions** — clusters, component roles, and topology are all discovered dynamically from XML attributes.

## Features

- **One-command generation**: Drop an XML, run the tool, get a rich HTML page
- **Smart classification**: Auto-categorizes 30+ component types into 14 infrastructure groups (FSC, DB, AW, Dispatcher, VIS, TCCS, Rich Client, etc.)
- **Solr grouping**: ZooKeeper + Indexing Engine on the same server are merged into one row ("ZK+Indexing"), FTS Indexer shown separately
- **Cluster topology**: Dynamically discovers clusters from `fnd0_serverManagerDisplayClusterId` with SM/WT layout
- **Full-mesh detection**: Identifies full-mesh WT→SM connections within clusters; displays as a collapsed band ("Full Connection NxN") instead of spaghetti lines
- **Interactive click-to-reveal**: Click a Web Tier node to reveal its individual SM connections; click again or click outside to hide
- **Pure BL Server extraction**: Automatically extracts BL servers without SM/WT (e.g. DC01, DISP01, DISP02) into a separate "Single BL Server" group
- **Statistics dashboard**: Infra Overview, Component Details (with category row-span), and Cluster summary tables
- **Light/Dark theme**: Toggle with button; preference saved to localStorage
- **Cache FSC display**: Non-master FSC cache servers shown in a sorted grid
- **JSON data export**: Also outputs `arch_data.json` for downstream tool consumption
- **Compact layout**: Infrastructure items wrap at 6 columns; cluster columns are compact; no horizontal scrollbar needed
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

All output files are generated in `./arch/` subdirectory relative to the XML file location:

| File | Description |
|------|-------------|
| `arch/arch.html` | Self-contained interactive architecture diagram |
| `arch/arch_data.json` | Structured classification data (JSON) |

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

## Dynamic Discovery

No hardcoded values — everything is inferred from XML content:

- **Clusters** are discovered from `fnd0_serverManagerDisplayClusterId` attributes on SM components. Colors are auto-assigned from a palette.
- **FSC master/cache** is detected via `fnd0_isMaster` property (TC standard)
- **Corporate server** is detected via `fnd0_corporateserver` component
- **Pure BL servers** are detected as BL components without SM/WT on the same machine
- **Full-mesh detection** checks if every WT connects to all SMs within the same cluster
- **Solr grouping** merges ZooKeeper + Indexing Engine on the same machine into one row

## Component Categories

| Category | Key | Components |
|----------|-----|------------|
| FSC | fsc | FSC Server (Master), FSC Keys, FSC Group |
| Database | db | TCDB Server, Pool DB Config |
| AW | aw | HTTPS Config, AW Client, Gateway |
| Solr/Search | solr | ZK+Indexing (merged), FTS Indexer |
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
pyinstaller --onefile --distpath output --workpath build dc_qdxml_to_arch.py
```

Output: `output/dc_qdxml_to_arch.exe` (~8MB)

## File Structure

```
dc_qdxml_to_arch/
├── dc_qdxml_to_arch.py      # Main Python script (zero dependencies)
├── output/
│   └── dc_qdxml_to_arch.exe # Standalone Windows EXE
└── README.md
```

## Related Projects

- **[dc_qdxml_validator](https://github.com/fei7yang/dc_qdxml_validator)** — Connection validation rules and XML config checker for TC Quick Deploy
- **[dc_qdxml_replace](https://github.com/fei7yang/dc_qdxml_replace)** — Hostname replacement tool for TC Quick Deploy XML

## License

Internal tool — for Teamcenter deployment architecture review.
