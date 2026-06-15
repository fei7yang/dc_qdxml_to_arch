#!/usr/bin/env python3
"""
dc_qdxml_to_arch.py -- Teamcenter Quick Deploy XML -> Architecture Visualization

Output: self-contained HTML with light/dark theme toggle, component stats table, interactive SVG.

Clusters are discovered dynamically from SM component attributes — no hardcoded definitions.
"""

import xml.etree.ElementTree as ET
import json, sys, os, re
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════════
# Category / Component definitions (TC standard — generic for any deployment)
# ══════════════════════════════════════════════════════════════════════

CAT_COLORS = {
    "fsc": "#1ABC9C", "db": "#F39C12", "aw": "#8E44AD", "solr": "#E67E22",
    "dispatcher": "#2ECC71", "vis": "#E91E63", "tccs": "#00BCD4",
    "client_2tier": "#FF9800", "client_4tier": "#FF7043", "client_mass": "#FFA726",
    "single_bl": "#9C27B0",
    "msf": "#3498DB", "license": "#95A5A6", "vault": "#D35400",
}
CAT_LABELS = {
    "fsc": "FSC", "db": "DB", "aw": "AW/Client", "solr": "Solr/Search",
    "dispatcher": "Dispatcher", "vis": "VIS", "tccs": "TCCS",
    "client_2tier": "2-Tier Rich Client", "client_4tier": "4-Tier Rich Client",
    "client_mass": "Mass Client (EDA)",
    "single_bl": "Single BL Server",
    "msf": "MSF", "license": "License", "vault": "Vault",
}
CAT_ORDER = ["fsc", "db", "aw", "solr", "dispatcher", "vis", "tccs",
             "client_2tier", "client_4tier", "client_mass", "single_bl",
             "msf", "license", "vault"]

COMP_CAT = {cid: (cat, lbl) for cid, (cat, lbl) in [
    ("fnd0_fsc_keys",               ("fsc",  "FSC Keys")),
    ("fnd0_fsc_group",              ("fsc",  "FSC Group")),
    ("fnd0_tcdbserver",             ("db",   "TCDB")),
    ("fnd0_serverpool_DBConfig",    ("db",   "PoolDB")),
    ("fnd0_httpsconfig",            ("aw",   "HTTPS")),
    ("aws2_client_builder",         ("aw",   "ClientBldr")),
    ("aws2_client_gateway_webtier", ("aw",   "Gateway")),
    ("aws2_indexingengine",         ("solr", "Indexing")),
    ("aws2_zookeeper",              ("solr", "ZK")),
    ("aws2_ftsIndexer",             ("solr", "FTS Idx")),
    ("fnd0_dispatcherModule",       ("dispatcher", "DispModule")),
    ("fnd0_dispatcherScheduler",    ("dispatcher", "DispScheduler")),
    ("fnd0_dispatcherclient",       ("dispatcher", "DispClient")),
    ("aws2_vispoolassigner",        ("vis",  "VIS Pool")),
    ("aws2_visservermanager",       ("vis",  "VIS Mgr")),
    ("fnd0_2tierrichclient",        ("client_2tier", "2-Tier")),
    ("fnd0_4tierrichclient",        ("client_4tier", "4-Tier")),
    ("eda0_client",                 ("client_mass", "EDA")),
    ("fnd0_vault",                  ("vault", "Vault")),
    ("fnd0_microservice",           ("msf",   "MicroSvc")),
    ("fnd0_licensingserver",        ("license", "LicenseSrv")),
]}

COMP_DESC = {
    "fnd0_fsc": "FSC Server", "fnd0_fsc_keys": "FSC Keys", "fnd0_fsc_group": "FSC Group",
    "fnd0_blserver": "BL Server", "fnd0_corporateserver": "Corporate Server",
    "fnd0_serverManager": "Server Manager", "fnd0_j2ee_tcwebtier": "Web Tier",
    "fnd0_tcdbserver": "TC DB Server", "fnd0_serverpool_DBConfig": "Pool DB Config",
    "fnd0_httpsconfig": "HTTPS Config", "fnd0_licensingserver": "License Server",
    "fnd0_microservice": "Microservice", "fnd0_containerconfig": "Container Config",
    "fnd0_vault": "Vault Server", "fnd0_schdmgmt": "Schedule Mgmt",
    "fnd0_servermgrconsole": "Server Mgr Console",
    "fnd0_dispatcherModule": "Dispatcher Module",
    "fnd0_dispatcherScheduler": "Dispatcher Scheduler",
    "fnd0_dispatcherclient": "Dispatcher Client",
    "fnd0_tccs": "TCCS Client",
    "fnd0_2tierrichclient": "2-Tier Rich Client",
    "fnd0_4tierrichclient": "4-Tier Rich Client",
    "eda0_client": "EDA Client",
    "aws2_indexingengine": "Indexing Engine", "aws2_zookeeper": "ZooKeeper",
    "aws2_ftsIndexer": "FTS Indexer", "aws2_client_builder": "Client Builder",
    "aws2_client_gateway_webtier": "Gateway Web Tier",
    "aws2_vispoolassigner": "VIS Pool Assigner", "aws2_visservermanager": "VIS Server Manager",
}

CAT_COMPONENT_IDS = {
    "fsc":         [("fnd0_fsc", "FSC Server"), ("fnd0_fsc_keys", "FSC Keys"), ("fnd0_fsc_group", "FSC Group")],
    "db":          [("fnd0_tcdbserver", "TC DB Server"), ("fnd0_serverpool_DBConfig", "Pool DB Config")],
    "aw":          [("fnd0_httpsconfig", "HTTPS Config"), ("aws2_client_builder", "Client Builder"),
                    ("aws2_client_gateway_webtier", "Gateway Web Tier")],
    "solr":        [("aws2_indexingengine", "Indexing Engine"), ("aws2_zookeeper", "ZooKeeper"),
                    ("aws2_ftsIndexer", "FTS Indexer")],
    "dispatcher":  [("fnd0_dispatcherModule", "Dispatcher Module"),
                    ("fnd0_dispatcherScheduler", "Dispatcher Scheduler"),
                    ("fnd0_dispatcherclient", "Dispatcher Client")],
    "vis":         [("aws2_vispoolassigner", "VIS Pool Assigner"),
                    ("aws2_visservermanager", "VIS Server Manager")],
    "tccs":        [("fnd0_tccs", "TCCS Client")],
    "client_2tier":[("fnd0_2tierrichclient", "2-Tier Rich Client")],
    "client_4tier":[("fnd0_4tierrichclient", "4-Tier Rich Client")],
    "client_mass": [("eda0_client", "EDA Mass Client")],
    "single_bl":   [("fnd0_blserver", "BL Server (pure)")],
    "msf":         [("fnd0_microservice", "Microservice"), ("fnd0_containerconfig", "Container Config")],
    "license":     [("fnd0_licensingserver", "License Server")],
    "vault":       [("fnd0_vault", "Vault Server")],
}

# Auto-assigned cluster color palette
PALETTE = ["#4ECDC4", "#FF6B6B", "#45B7D1", "#96CEB4", "#E6A817",
           "#DDA0DD", "#98D8C8", "#D4AC0D", "#FF8C42", "#6C5B7B",
           "#C06C84", "#355C7D", "#F67280", "#99B898", "#E84A5F"]


def app_num(name):
    """Extract trailing number from a machine name (eg. APP01->1, APP123->123)."""
    m = re.search(r"(\d+)$", name)
    return int(m.group(1)) if m else 0


def discover_clusters(components):
    """
    Dynamically discover clusters from SM components.
    Returns (machine_to_cluster, cluster_data).

    machine_to_cluster: {machine_name: cluster_name}
    cluster_data: {cluster_name: {"color": str, "members": [machine_names]}}
    """
    cluster_members = defaultdict(list)

    for c in components:
        if c["id"] == "fnd0_serverManager":
            mn = c["machineName"]
            cluster_name = c["props"].get("fnd0_serverManagerDisplayClusterId", "Unnamed")
            cluster_members[cluster_name].append(mn)

    # Also cover machines that have WT but no SM (inherits from connected SM cluster)
    # by expanding: if WT connects to SM, WT's machine gets the same cluster
    # Handled later in classify — for now, build from SM data

    machine_to_cluster = {}
    cluster_data = {}

    sorted_clusters = sorted(cluster_members.items(), key=lambda x: x[0])
    for i, (cname, members) in enumerate(sorted_clusters):
        color = PALETTE[i % len(PALETTE)]
        for mn in members:
            machine_to_cluster[mn] = cname
        cluster_data[cname] = {
            "color": color,
            "members": sorted(members, key=app_num),
        }

    return machine_to_cluster, cluster_data


# ══════════════════════════════════════════════════════════════════════
# 1. XML Parsing
# ══════════════════════════════════════════════════════════════════════

def parse_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    config = root.get("configName", "Unknown")
    foundation = "Unknown"
    for sw in root.findall(".//quickDeploySoftware/software"):
        if sw.get("id") == "Foundation":
            foundation = sw.get("version", "Unknown")

    def extract(elem):
        info = {
            "id": elem.get("id", ""),
            "machineName": elem.get("machineName", ""),
            "platform": elem.get("platform", ""),
            "props": {}, "connectedTo": [],
        }
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "property":
                info["props"][child.get("id", "")] = child.get("value", "")
            elif tag == "connectedTo":
                info["connectedTo"].append({"component": child.get("component", ""),
                                           "machineName": child.get("machineName", "")})
        return info

    components, clients = [], []
    cc = root.find(".//quickDeployComponents")
    if cc is not None:
        for el in cc.iter("component"): components.append(extract(el))
    cl = root.find(".//quickDeployClients")
    if cl is not None:
        for el in cl.iter("client"): clients.append(extract(el))

    return {"configName": config, "foundation": foundation}, components, clients


# ══════════════════════════════════════════════════════════════════════
# 2. Classification (dynamic clusters)
# ══════════════════════════════════════════════════════════════════════

def classify(components, clients):
    arch = {
        "infra_groups": {c: {"label": CAT_LABELS[c], "color": CAT_COLORS[c], "items": []} for c in CAT_ORDER},
        "cache_fsc": [],
        "clusters": {},
        "comp_counts": defaultdict(int),
        "tccs_counts": defaultdict(int),
        "cluster_data": {},  # cluster_name → {color, members}
    }

    # ── Phase 1: discover clusters from SM data ──
    machine_to_cluster, cluster_data = discover_clusters(components)

    # Expand: WT machines not in machine_to_cluster → inherit from connected SM
    wt_connects = {}
    for c in components:
        if c["id"] == "fnd0_j2ee_tcwebtier":
            mn = c["machineName"]
            for conn in c.get("connectedTo", []):
                if conn["component"] == "fnd0_serverManager":
                    wt_connects.setdefault(mn, []).append(conn["machineName"])

    changed = True
    while changed:
        changed = False
        for wt_mn, sm_list in wt_connects.items():
            if wt_mn in machine_to_cluster:
                continue
            for sm_mn in sm_list:
                if sm_mn in machine_to_cluster:
                    cname = machine_to_cluster[sm_mn]
                    machine_to_cluster[wt_mn] = cname
                    if wt_mn not in cluster_data[cname]["members"]:
                        cluster_data[cname]["members"].append(wt_mn)
                    changed = True
                    break

    # Sort cluster members
    for cd in cluster_data.values():
        cd["members"].sort(key=app_num)

    arch["cluster_data"] = cluster_data

    # Init clusters dict
    for cname, cd in sorted(cluster_data.items()):
        arch["clusters"][cname] = {"color": cd["color"], "apps": {}}

    # ── Phase 2: index SM/WT info ──
    sm_index = {}
    wt_index = {}
    for c in components:
        cid = c["id"]
        if cid == "fnd0_serverManager":
            sm_index[c["machineName"]] = {
                "cluster": c["props"].get("fnd0_serverManagerDisplayClusterId", ""),
                "pool": c["props"].get("fnd0_serverPoolId", ""),
            }
        if cid == "fnd0_j2ee_tcwebtier":
            wt_index[c["machineName"]] = {
                "app_name": c["props"].get("fnd0_j2ee_applicationName", ""),
            }

    # Count
    for c in components:
        arch["comp_counts"][c["id"]] += 1
    for cl in clients:
        arch["comp_counts"][cl["id"]] += 1

    # Rich client machine sets
    rc_machines = {"client_2tier": set(), "client_4tier": set(), "client_mass": set()}
    all_items = components + clients
    for item in all_items:
        cid, mn = item["id"], item["machineName"]
        if cid == "fnd0_2tierrichclient": rc_machines["client_2tier"].add(mn)
        elif cid == "fnd0_4tierrichclient": rc_machines["client_4tier"].add(mn)
        elif cid == "eda0_client": rc_machines["client_mass"].add(mn)

    # Corporate server detection
    corp_machine = None
    container_registry = None
    for c in components:
        if c["id"] == "fnd0_corporateserver":
            corp_machine = c["machineName"]
        if c["id"] == "fnd0_containerconfig":
            container_registry = {
                "manager": c["props"].get("fnd0_containerconfig_containerManager", ""),
                "registry": c["props"].get("fnd0_containerconfig_containerRegistry", ""),
            }

    # ── Phase 3: classify components ──
    for item in all_items:
        cid, mn = item["id"], item["machineName"]

        # Standard component → infra group
        if cid in COMP_CAT:
            cat, lbl = COMP_CAT[cid]
            arch["infra_groups"][cat]["items"].append({"machine": mn, "label": lbl, "is_master": False})
            continue

        # Container registry
        if cid == "fnd0_containerconfig" and container_registry:
            arch["infra_groups"]["msf"]["items"].append({
                "machine": container_registry["registry"], "label": "Registry", "is_master": False,
            })
            continue

        # Corporate server → skip (tracked above)
        if cid == "fnd0_corporateserver":
            continue

        # FSC: use fnd0_isMaster property (TC standard) for master/cache distinction
        if cid == "fnd0_fsc":
            is_master = item["props"].get("fnd0_isMaster", "").lower() == "true"
            if is_master:
                # Dedicated master FSC (e.g. FSC01-08)
                arch["infra_groups"]["fsc"]["items"].append({
                    "machine": mn, "label": "Master", "is_master": True,
                })
                continue
            elif mn in machine_to_cluster:
                # Co-located on cluster APP machine → set has_fsc, not standalone
                pass  # fall through to cluster processing
            else:
                # Standalone non-master → cache / external
                arch["cache_fsc"].append({"machine": mn})
                continue

        # TCCS → separate category
        if cid == "fnd0_tccs":
            arch["infra_groups"]["tccs"]["items"].append({"machine": mn, "label": "TCCS", "is_master": False})
            for cat in ["client_2tier", "client_4tier", "client_mass"]:
                if mn in rc_machines[cat]:
                    arch["tccs_counts"][cat] += 1; break
            continue

        # Cluster members
        cname = machine_to_cluster.get(mn)
        if not cname or cname not in arch["clusters"]:
            continue

        apps = arch["clusters"][cname]["apps"]
        if mn not in apps:
            si = sm_index.get(mn, {})
            wi = wt_index.get(mn, {})
            apps[mn] = {
                "sm_pool": si.get("pool", ""),
                "wt_appname": wi.get("app_name", ""),
                "has_webtier": False, "has_sm": False, "has_fsc": False,
                "has_bl": False, "is_corp": False, "wt_connects_to": [],
            }
        app = apps[mn]

        if cid == "fnd0_j2ee_tcwebtier":
            app["has_webtier"] = True
            app["wt_connects_to"] = [c["machineName"] for c in item["connectedTo"]
                                     if c["component"] == "fnd0_serverManager"]
        elif cid == "fnd0_serverManager":
            app["has_sm"] = True
        elif cid == "fnd0_fsc":
            app["has_fsc"] = True
        elif cid == "fnd0_blserver":
            app["has_bl"] = True

    # ── Post-processing ──

    # Extract pure BL servers (has_bl, no SM, no WT) → single_bl
    pure_bl_machines = []
    for cname in list(arch["clusters"].keys()):
        to_remove = []
        for an, app in arch["clusters"][cname]["apps"].items():
            if app.get("has_bl") and not app["has_sm"] and not app["has_webtier"]:
                pure_bl_machines.append(an)
                to_remove.append(an)
        for an in to_remove:
            del arch["clusters"][cname]["apps"][an]
        if not arch["clusters"][cname]["apps"]:
            del arch["clusters"][cname]

    for mn in sorted(pure_bl_machines, key=app_num):
        arch["infra_groups"]["single_bl"]["items"].append({"machine": mn, "label": "Pure BL", "is_master": False})

    # Mark corporate server
    if corp_machine:
        for cname in arch["clusters"]:
            if corp_machine in arch["clusters"][cname]["apps"]:
                arch["clusters"][cname]["apps"][corp_machine]["is_corp"] = True
                arch["clusters"][cname]["apps"][corp_machine]["has_bl"] = False
                break

    # Full-mesh detection per cluster
    for cname, cd in arch["clusters"].items():
        all_apps = cd["apps"]
        sm_set = {an for an, a in all_apps.items() if a["has_sm"]}
        wt_set = {an for an, a in all_apps.items() if a["has_webtier"]}
        full = True
        for wt_name in wt_set:
            wt = all_apps[wt_name]
            connected_sm = set(wt["wt_connects_to"]) & sm_set
            if connected_sm != sm_set:
                full = False; break
        cd["mesh_wt"] = len(wt_set)
        cd["mesh_sm"] = len(sm_set)
        cd["full_mesh"] = full and cd["mesh_wt"] >= 2 and cd["mesh_sm"] >= 2

    # Sort infra items
    arch["cache_fsc"].sort(key=lambda x: x["machine"])
    for cat in arch["infra_groups"]:
        arch["infra_groups"][cat]["items"].sort(key=lambda x: (0 if x.get("is_master") else 1, x["machine"]))

    return arch, machine_to_cluster


# ══════════════════════════════════════════════════════════════════════
# 3. Layout
# ══════════════════════════════════════════════════════════════════════

COL_W, COL_GAP = 120, 10
SM_H, WT_H = 48, 42
MID_GAP = 64
INFRA_ITEM_W, INFRA_ITEM_H, INFRA_GAP = 220, 36, 8


def layout(arch, machine_to_cluster):
    el = {"zones": [], "nodes": [], "links": [], "labels": [], "mesh_bands": []}
    y = 10

    # ═══ Infrastructure Groups ═══
    for cat in CAT_ORDER:
        group = arch["infra_groups"][cat]
        items = group["items"]
        if not items: continue
        n_items = len(items)
        title = f'{group["label"]} ({n_items})'
        el["labels"].append({
            "x": 10, "y": y + 20,
            "text": title, "class": "group-title", "color": group["color"],
        })
        ix = 180
        for it in items:
            lbl = it["label"]
            el["nodes"].append({
                "id": f"infra_{cat}_{it['machine']}",
                "x": ix, "y": y + 3, "w": 160, "h": INFRA_ITEM_H,
                "machine": it["machine"], "label": lbl,
                "color": group["color"], "is_master": it.get("is_master", False),
                "category": "infra_item",
            })
            ix += 170
        y += INFRA_ITEM_H + 10
    y += 12

    # ═══ Clusters (dynamic order) ═══
    clusters = arch["clusters"]
    cluster_names = sorted(clusters.keys())
    for cn in cluster_names:
        cdata = clusters[cn]
        apps, n = cdata["apps"], len(cdata["apps"])
        if n == 0: continue

        SM_TOP = 34
        row_w = n * COL_W + (n - 1) * COL_GAP + 24
        row_h = SM_TOP + SM_H + MID_GAP + WT_H + 36

        color = cdata["color"]
        # Zone background
        el["zones"].append({"x": 4, "y": y, "w": row_w + 8, "h": row_h + 4,
                           "color": color, "name": cn})

        # Full-mesh band
        if cdata.get("full_mesh"):
            wt_n, sm_n = cdata["mesh_wt"], cdata["mesh_sm"]
            el["mesh_bands"].append({
                "x": 8, "y": y + SM_TOP + SM_H + 6,
                "w": row_w, "h": MID_GAP - 12,
                "color": color, "cluster": cn,
                "label": f"Full Connection {sm_n}x{sm_n}",
            })

        title = f'{cn}  .  {n} APPs'
        if cdata.get("full_mesh"):
            title += f'  [Mesh {cdata["mesh_sm"]}x{cdata["mesh_sm"]}]'
        el["labels"].append({
            "x": 12, "y": y + 4,
            "text": title, "class": "cluster-title", "color": color,
        })

        sorted_apps = sorted(apps.keys(), key=app_num)
        for i, app_name in enumerate(sorted_apps):
            app = apps[app_name]
            cx = 14 + i * (COL_W + COL_GAP)
            sm_y = y + SM_TOP

            # SM box
            el["nodes"].append({
                "id": f"sm_{cn}_{app_name}", "x": cx, "y": sm_y, "w": COL_W, "h": SM_H,
                "machine": app_name, "display": app["sm_pool"] or "",
                "category": "sm", "color": "#E74C3C", "cluster": cn,
            })
            # WT box
            wt_y = sm_y + SM_H + MID_GAP
            el["nodes"].append({
                "id": f"wt_{cn}_{app_name}", "x": cx, "y": wt_y, "w": COL_W, "h": WT_H,
                "machine": app_name, "display": app["wt_appname"] or "",
                "category": "webtier", "color": "#3498DB", "cluster": cn,
            })
            # APP label
            el["labels"].append({
                "x": cx + COL_W/2, "y": wt_y + WT_H + 12,
                "text": app_name, "class": "app-label",
            })
            # Annotations
            annots = []
            if app.get("is_corp"): annots.append(("Corp", "#F39C12"))
            if app.get("has_bl"): annots.append(("BL", "#F39C12"))
            if app.get("has_fsc"): annots.append(("FS", "#2ECC71"))
            if annots:
                annot_y = wt_y + WT_H + 24
                spacing = min(18, (COL_W - 10) / max(len(annots), 1))
                start_x = cx + COL_W/2 - (len(annots)-1)*spacing/2
                for ai, (al, ac) in enumerate(annots):
                    el["nodes"].append({
                        "id": f"annot_{cn}_{app_name}_{al}",
                        "x": start_x + ai*spacing, "y": annot_y, "r": 7,
                        "machine": app_name, "label": al, "color": ac, "category": "annot",
                    })

            # Links
            wt_top = (cx + COL_W/2, wt_y)
            for tgt_machine in app["wt_connects_to"]:
                tgt_cname = machine_to_cluster.get(tgt_machine)
                if tgt_cname and tgt_cname in clusters:
                    el["links"].append({
                        "src_cluster": cn, "src_app": app_name, "src_pos": wt_top,
                        "tgt_cluster": tgt_cname, "tgt_app": tgt_machine,
                        "cross": (cn != tgt_cname),
                        "hidden": cdata.get("full_mesh", False),
                    })

        y += row_h + 16

    # Resolve links
    sm_bottoms = {(n["cluster"], n["machine"]): (n["x"]+n["w"]/2, n["y"]+n["h"])
                  for n in el["nodes"] if n["category"] == "sm"}
    resolved = []
    for link in el["links"]:
        tk = (link["tgt_cluster"], link["tgt_app"])
        if tk in sm_bottoms:
            x1, y1 = link["src_pos"]; x2, y2 = sm_bottoms[tk]
            resolved.append({"x1":x1, "y1":y1, "x2":x2, "y2":y2, "cross":link["cross"],
                            "src_app": link["src_app"], "hidden": link.get("hidden", False)})
    el["links"] = resolved

    # ═══ Standalone FSC ═══
    y += 6
    caches = arch["cache_fsc"]
    CACHE_COLS = 6
    if caches:
        el["labels"].append({
            "x": 10, "y": y + 14,
            "text": f"Standalone FSC ({len(caches)})",
            "class": "section",
        })
        y += 22
        for i, item in enumerate(caches):
            cx = 14 + (i % CACHE_COLS) * (INFRA_ITEM_W + INFRA_GAP)
            cy = y + (i // CACHE_COLS) * (INFRA_ITEM_H + INFRA_GAP)
            el["nodes"].append({
                "id": f"cache_{item['machine']}", "x": cx, "y": cy,
                "w": INFRA_ITEM_W, "h": INFRA_ITEM_H,
                "machine": item["machine"], "label": item["machine"],
                "color": "#9B59B6", "category": "cache",
            })
        cache_rows = max(1, (len(caches) + CACHE_COLS - 1) // CACHE_COLS)
        y += cache_rows * (INFRA_ITEM_H + INFRA_GAP) + 10

    # Canvas size
    max_x = 10
    for z in el["zones"]: max_x = max(max_x, z["x"]+z["w"])
    for n in el["nodes"]: max_x = max(max_x, n["x"]+n.get("w", n.get("r",8)*2))
    el["svg_w"] = max(max_x+20, 400)
    el["svg_h"] = y+20
    return el


# ══════════════════════════════════════════════════════════════════════
# 4. SVG Rendering
# ══════════════════════════════════════════════════════════════════════

def render_svg(elements, meta):
    svg = []
    W, H = elements["svg_w"], elements["svg_h"]
    svg.append(f'<svg id="arch-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
               f'width="{W}" height="{H}" style="background:var(--bg);font-family:Segoe UI,Microsoft YaHei,sans-serif">')

    # Mesh Bands
    for mb in elements.get("mesh_bands", []):
        svg.append(
            f'<rect x="{mb["x"]}" y="{mb["y"]}" width="{mb["w"]}" height="{mb["h"]}" '
            f'rx="3" fill="{mb["color"]}" fill-opacity="0.08" '
            f'stroke="{mb["color"]}" stroke-width="1" stroke-opacity="0.2" stroke-dasharray="4,2"/>'
        )
        svg.append(
            f'<text x="{mb["x"]+mb["w"]/2}" y="{mb["y"]+mb["h"]/2+4}" '
            f'text-anchor="middle" fill="{mb["color"]}" fill-opacity="0.6" font-size="9">{mb["label"]}</text>'
        )

    # Links grouped by src_app
    link_groups = defaultdict(list)
    for link in elements["links"]:
        link_groups[link.get("src_app", "_other")].append(link)

    for src_app, links in sorted(link_groups.items()):
        is_hidden = all(l.get("hidden", False) for l in links)
        cls = 'wt-links' + (' hidden-init' if is_hidden else '')
        svg.append(f'<g class="{cls}" id="links-{src_app}">')
        for link in links:
            s = "#E74C3C" if link["cross"] else "#3498DB"
            d = ' stroke-dasharray="3,2"' if link["cross"] else ""
            o = "0.15" if link["cross"] else "0.25"
            w = "0.7" if link["cross"] else "1.0"
            svg.append(f'<line x1="{link["x1"]}" y1="{link["y1"]}" x2="{link["x2"]}" y2="{link["y2"]}" '
                       f'stroke="{s}" stroke-width="{w}" stroke-opacity="{o}"{d}/>')
        svg.append('</g>')

    for z in elements["zones"]:
        svg.append(f'<rect x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}" '
                   f'rx="6" fill="{z["color"]}" fill-opacity="0.06" '
                   f'stroke="{z["color"]}" stroke-width="1.5" stroke-opacity="0.25"/>')

    for lbl in elements["labels"]:
        cls = lbl.get("class")
        if cls == "section":
            svg.append(f'<text x="{lbl["x"]}" y="{lbl["y"]}" fill="var(--sec)" font-size="13" font-weight="bold">{lbl["text"]}</text>')
        elif cls == "cluster-title":
            svg.append(f'<text x="{lbl["x"]}" y="{lbl["y"]+16}" fill="{lbl.get("color","#ccc")}" font-size="14" font-weight="bold">{lbl["text"]}</text>')
        elif cls == "group-title":
            svg.append(f'<text x="{lbl["x"]}" y="{lbl["y"]}" fill="{lbl.get("color","#ccc")}" font-size="11" font-weight="bold">{lbl["text"]}</text>')
        elif cls == "app-label":
            svg.append(f'<text x="{lbl["x"]}" y="{lbl["y"]}" text-anchor="middle" fill="var(--applbl)" font-size="10">{lbl["text"]}</text>')

    for node in elements["nodes"]:
        cat = node["category"]
        if cat in ("sm", "webtier"):
            d = node.get("display","")
            if len(d) > 16: d = d[:14]+".."
            fs = "10" if len(d) > 10 else "11"
            cls = 'wt-node' if cat == 'webtier' else ''
            svg.append(
                f'<rect x="{node["x"]}" y="{node["y"]}" width="{node["w"]}" height="{node["h"]}" '
                f'rx="4" fill="{node["color"]}" fill-opacity="0.15" '
                f'stroke="{node["color"]}" stroke-width="1.5" stroke-opacity="0.5" '
                f'class="{cls}" data-app="{node["machine"]}" data-cluster="{node.get("cluster","")}">'
                f'<title>{node["machine"]}: {d}</title></rect>'
            )
            svg.append(
                f'<text x="{node["x"]+node["w"]/2}" y="{node["y"]+node["h"]/2+5}" '
                f'text-anchor="middle" fill="var(--boxtext)" font-size="{fs}" font-weight="bold">{d}</text>'
            )
        elif cat == "infra_item":
            im = node.get("is_master", False)
            sw, so = ("2","0.6") if im else ("1","0.4")
            lt = node["label"]
            svg.append(
                f'<rect x="{node["x"]}" y="{node["y"]}" width="{node["w"]}" height="{node["h"]}" '
                f'rx="3" fill="{node["color"]}" fill-opacity="0.18" '
                f'stroke="{node["color"]}" stroke-width="{sw}" stroke-opacity="{so}">'
                f'<title>{node["machine"]}: {node["label"]}{" (Master)" if im else ""}</title></rect>'
            )
            svg.append(f'<text x="{node["x"]+8}" y="{node["y"]+22}" fill="var(--boxtext)" font-size="11">{node["machine"]}</text>')
            svg.append(f'<text x="{node["x"]+node["w"]-8}" y="{node["y"]+22}" text-anchor="end" fill="var(--infolbl)" font-size="10">{lt}</text>')
        elif cat == "cache":
            svg.append(
                f'<rect x="{node["x"]}" y="{node["y"]}" width="{node["w"]}" height="{node["h"]}" '
                f'rx="3" fill="{node["color"]}" fill-opacity="0.12" '
                f'stroke="{node["color"]}" stroke-width="1" stroke-opacity="0.35">'
                f'<title>{node["machine"]}</title></rect>'
            )
            svg.append(f'<text x="{node["x"]+8}" y="{node["y"]+22}" fill="var(--boxtext)" font-size="11">{node["machine"]}</text>')
        elif cat == "annot":
            svg.append(
                f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{node["r"]}" '
                f'fill="{node["color"]}" fill-opacity="0.85" stroke="#fff" stroke-width="0.5">'
                f'<title>{node["machine"]}: {node["label"]}</title></circle>'
            )
            svg.append(f'<text x="{node["x"]}" y="{node["y"]+2}" text-anchor="middle" fill="#fff" font-size="7" font-weight="bold">{node["label"]}</text>')
    svg.append('</svg>')
    return "\n".join(svg)


# ══════════════════════════════════════════════════════════════════════
# 5. HTML Wrapper + Stats
# ══════════════════════════════════════════════════════════════════════

def build_stats_tables(arch):
    cc = arch["comp_counts"]

    # Infra table
    infra_rows = []
    for cat in CAT_ORDER:
        items = arch["infra_groups"].get(cat, {}).get("items", [])
        if not items: continue
        masters = [i for i in items if i.get("is_master")]
        tag = f" ({len(masters)} Master)" if masters else ""
        infra_rows.append(f'<tr><td>{CAT_LABELS[cat]}</td><td>{len(items)}{tag}</td></tr>')

    # Component detail
    comp_rows = []
    for cat in CAT_ORDER:
        if cat not in CAT_COMPONENT_IDS: continue
        cids = CAT_COMPONENT_IDS[cat]
        row_ids = []
        for cid, name in cids:
            cnt = cc.get(cid, 0)
            if cnt > 0:
                row_ids.append((cid, name, cnt))
        if not row_ids: continue
        n_rows = len(row_ids)
        first_row = row_ids[0]
        comp_rows.append(
            f'<tr><td rowspan="{n_rows}" class="cat-col">{CAT_LABELS[cat]}</td>'
            f'<td class="cid">{first_row[0]}</td><td>{first_row[1]}</td>'
            f'<td><strong>{first_row[2]}</strong></td></tr>'
        )
        for cid, name, cnt in row_ids[1:]:
            comp_rows.append(
                f'<tr><td class="cid">{cid}</td><td>{name}</td><td><strong>{cnt}</strong></td></tr>'
            )

    tccs_cnt = cc.get("fnd0_tccs", 0)
    if tccs_cnt > 0:
        comp_rows.append(
            f'<tr><td rowspan="1" class="cat-col">{CAT_LABELS["tccs"]}</td>'
            f'<td class="cid">fnd0_tccs</td><td>TCCS Client</td>'
            f'<td><strong>{tccs_cnt}</strong></td></tr>'
        )

    # Dynamic cluster table
    crow = []
    for cname in sorted(arch["clusters"].keys()):
        cd = arch["clusters"][cname]
        n = len(cd["apps"])
        wt = sum(1 for a in cd["apps"].values() if a["has_webtier"])
        sm = sum(1 for a in cd["apps"].values() if a["has_sm"])
        fs = sum(1 for a in cd["apps"].values() if a["has_fsc"])
        bl = sum(1 for a in cd["apps"].values() if a.get("has_bl"))
        cp = sum(1 for a in cd["apps"].values() if a.get("is_corp"))
        info = f"{n} APP"
        if cp: info += f" / Corp {cp}"
        info += f" / BL {bl} / FS {fs} / WT {wt} / SM {sm}"
        crow.append(f'<tr><td>{cname}</td><td>{info}</td></tr>')
    return ''.join(infra_rows), ''.join(comp_rows), ''.join(crow)


def build_html(svg_str, meta, arch):
    infra_table, comp_table, cluster_table = build_stats_tables(arch)
    cache_n = len(arch["cache_fsc"])
    total_comps = sum(arch["comp_counts"].values())
    n_clusters = len(arch["clusters"])

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta["configName"]} -- TC Architecture</title>
<style>
:root {{
  --bg: #0d1117; --fg: #c9d1d9; --sec: #555; --boxtext: #ddd;
  --applbl: #888; --infolbl: #999; --card: #161b22; --border: #21262d; --th: #1c2128;
}}
:root.light {{
  --bg: #f6f8fa; --fg: #24292f; --sec: #656d76; --boxtext: #24292f;
  --applbl: #57606a; --infolbl: #57606a; --card: #fff; --border: #d0d7de; --th: #eaeef2;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--fg);overflow:auto}}
#app{{padding:14px;min-width:max-content}}
#top{{margin-bottom:10px}}
.title-row{{display:flex;align-items:center;gap:12px;margin-bottom:4px}}
#title-block h1{{font-size:18px;color:var(--fg);white-space:nowrap}}
#title-block .sub{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.tag{{padding:2px 10px;border-radius:10px;font-size:11px;font-weight:bold;border:1px solid var(--border);background:var(--card);color:var(--fg)}}
.tag.total{{background:#1f6feb;color:#fff;border-color:#1f6feb}}
#theme-btn{{padding:5px 14px;border:1px solid var(--border);border-radius:6px;background:var(--card);color:var(--fg);cursor:pointer;font-size:11px;transition:all .2s;white-space:nowrap}}
#theme-btn:hover{{border-color:#58a6ff;color:#58a6ff}}
#stats{{display:grid;grid-template-columns:auto 1fr;gap:18px;margin-bottom:10px;align-items:start}}
.stats-left{{display:flex;flex-direction:column;gap:14px}}
.stats-right{{min-width:0}}
.stats-table{{border-collapse:collapse;font-size:11px}}
.stats-table caption{{font-weight:bold;font-size:12px;color:var(--sec);text-align:left;padding-bottom:4px}}
.stats-table td{{padding:1px 8px 1px 0;white-space:nowrap}}
.stats-table td:first-child{{color:var(--infolbl)}}
.stats-table tr:hover td{{color:var(--fg)}}
.stats-table .cat-col{{color:#1f6feb!important;font-weight:bold;font-size:10px;vertical-align:top;padding-right:6px}}
.stats-table .cid{{font-family:monospace;font-size:10px}}
#legend{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;font-size:11px;color:var(--sec)}}
.leg{{display:flex;align-items:center;gap:4px}}
.leg-dot{{width:11px;height:11px;border-radius:2px}}
.leg-sep{{margin-left:10px}}
#svg-wrap{{overflow:auto;border:1px solid var(--border);border-radius:5px;background:var(--bg)}}
.hidden-init{{display:none}}
.wt-links.show{{display:block!important}}
.wt-node{{cursor:pointer;transition:all .15s}}
.wt-node:hover{{filter:brightness(1.3)}}
.tooltip{{position:fixed;background:var(--card);border:1px solid var(--border);padding:6px 10px;border-radius:4px;font-size:11px;pointer-events:none;z-index:100;display:none;box-shadow:0 2px 8px rgba(0,0,0,0.3)}}
</style>
</head>
<body>
<div id="app">
  <div id="top">
    <div id="title-block">
      <div class="title-row">
        <h1>{meta["configName"]} -- TC Deployment Architecture</h1>
        <button id="theme-btn" onclick="toggleTheme()">☀ Light</button>
      </div>
      <div class="sub">
        <span class="tag">Foundation {meta["foundation"]}</span>
        <span class="tag">{n_clusters} Clusters</span>
        <span class="tag">{cache_n} Standalone FSC</span>
        <span class="tag total">Total {total_comps} Components</span>
      </div>
    </div>
  </div>

  <div id="stats">
    <div class="stats-left">
      <table class="stats-table"><caption>Infra Overview</caption><tbody>
        {infra_table}
      </tbody></table>
      <table class="stats-table"><caption>Clusters</caption><tbody>
        {cluster_table}
      </tbody></table>
    </div>
    <div class="stats-right">
      <table class="stats-table"><caption>Component Details</caption><tbody>
        {comp_table}
      </tbody></table>
    </div>
  </div>

  <div id="legend">
    <div class="leg"><div class="leg-dot" style="background:#E74C3C"></div>SM (PoolID)</div>
    <div class="leg"><div class="leg-dot" style="background:#3498DB"></div>Web (AppName)</div>
    <div class="leg"><div class="leg-dot" style="background:#F39C12"></div>Corp/BL</div>
    <div class="leg"><div class="leg-dot" style="background:#2ECC71"></div>FS</div>
    <div class="leg leg-sep">| WT → SM (same-app)</div>
  </div>

  <div id="svg-wrap">
    {svg_str}
  </div>
</div>
<script>
function toggleTheme() {{
  var r = document.documentElement;
  var b = document.getElementById('theme-btn');
  if (r.classList.contains('light')) {{
    r.classList.remove('light'); b.textContent = '☀ Light';
  }} else {{
    r.classList.add('light'); b.textContent = '🌙 Dark';
  }}
  localStorage.setItem('arch-theme', r.classList.contains('light') ? 'light' : 'dark');
}}
(function() {{
  if (localStorage.getItem('arch-theme') === 'light') {{
    document.documentElement.classList.add('light');
    document.getElementById('theme-btn').textContent = '🌙 Dark';
  }}
  // WT node click to toggle hidden link groups
  var activeNode = null, activeGroup = null;
  document.querySelectorAll('.wt-node').forEach(function(node) {{
    node.addEventListener('click', function(e) {{
      e.stopPropagation();
      var app = this.getAttribute('data-app');
      var group = document.getElementById('links-' + app);
      if (activeNode) {{ activeNode.classList.remove('active'); }}
      if (activeGroup && activeGroup !== group) {{ activeGroup.classList.remove('show'); }}
      if (group) {{
        if (group === activeGroup) {{
          group.classList.remove('show');
          activeGroup = null; activeNode = null;
        }} else {{
          group.classList.add('show');
          activeGroup = group; activeNode = this;
          this.classList.add('active');
        }}
      }}
    }});
  }});
  document.addEventListener('click', function() {{
    if (activeNode) {{ activeNode.classList.remove('active'); }}
    if (activeGroup) {{ activeGroup.classList.remove('show'); }}
    activeNode = null; activeGroup = null;
  }});
  document.getElementById('arch-svg').addEventListener('click', function(e) {{ e.stopPropagation(); }});
}})();
</script>
</body>
</html>'''


# ══════════════════════════════════════════════════════════════════════
# 6. Main
# ══════════════════════════════════════════════════════════════════════

def main():
    if any(a in ("-h", "--help") for a in sys.argv):
        print("""dc_qdxml_to_arch -- TC Quick Deploy XML -> Architecture HTML

Usage:
    dc_qdxml_to_arch                auto-detect single .xml in current dir
    dc_qdxml_to_arch file.xml       parse specific XML
    dc_qdxml_to_arch file.xml out.html   custom output name

Clusters are discovered automatically from SM component attributes.
No hardcoded cluster definitions needed.

Output:
    arch.html          interactive architecture diagram (light/dark theme)
    arch_data.json     structured data for downstream tools""")
        return

    if len(sys.argv) >= 2:
        xml_path = sys.argv[1]
    else:
        cwd = os.getcwd()
        xmls = sorted([f for f in os.listdir(cwd) if f.lower().endswith(".xml")])
        if len(xmls) == 0:
            print("ERROR: No .xml file found."); sys.exit(1)
        if len(xmls) > 1:
            print("ERROR: Multiple .xml files found:"); [print(f"       {x}") for x in xmls]; sys.exit(1)
        xml_path = os.path.join(cwd, xmls[0])
        print(f"Auto-detected: {xmls[0]}")

    out_dir = os.path.dirname(os.path.abspath(xml_path))
    html_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(out_dir, "arch.html")
    json_path = html_path.replace(".html", "_data.json")

    print(f"[1/4] Parse: {xml_path}")
    meta, comps, clis = parse_xml(xml_path)
    total = len(comps) + len(clis)
    print(f"      {meta['configName']} / Foundation {meta['foundation']}  ({total} items)")

    print(f"[2/4] Classify...")
    arch, machine_to_cluster = classify(comps, clis)

    print(f"   Discovered {len(arch['cluster_data'])} clusters:")
    for cname, cd in sorted(arch["cluster_data"].items()):
        print(f"      {cname}: {len(cd['members'])} members")

    print("   Components:")
    for cid, cnt in sorted(arch["comp_counts"].items(), key=lambda x: -x[1]):
        desc = COMP_DESC.get(cid, "")
        print(f"      {cid:40s} {desc:22s} x{cnt}")
    print(f"   Clusters in arch: {len(arch['clusters'])}")
    for cname in sorted(arch["clusters"].keys()):
        cd = arch["clusters"][cname]
        print(f"      {cname}: {len(cd['apps'])} APPs")

    print(f"[3/4] Layout & render...")
    layout_data = layout(arch, machine_to_cluster)
    print(f"      Canvas: {layout_data['svg_w']} x {layout_data['svg_h']}  ({len(layout_data['links'])} links)")

    svg_str = render_svg(layout_data, meta)
    html = build_html(svg_str, meta, arch)

    print(f"[4/4] Write...")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"      HTML: {html_path} ({len(html):,} bytes)")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(arch, f, ensure_ascii=False, indent=2, default=str)
    print(f"      JSON: {json_path}")
    print(f"\nDone.")

    # 双击模式：自动打开浏览器预览
    import webbrowser
    webbrowser.open(f'file:///{html_path}')

    input('\n按 Enter 键退出...')


if __name__ == "__main__":
    main()
