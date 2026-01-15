import json
import os
from pathlib import Path
from collections import defaultdict

def merge_sdgui_files(folder_path, output_file="combined.sdgui"):
    """
    Merge all .sdgui files in a folder into a single combined file.
    
    Args:
        folder_path: Path to folder containing .sdgui files
        output_file: Name of the output merged file
    """
    folder = Path(folder_path)
    all_sdgui_files = list(folder.glob("*.sdgui"))
    
    # Exclude the output file from the list of files to merge
    output_path = folder / output_file
    sdgui_files = [f for f in all_sdgui_files if f != output_path]
    
    if not sdgui_files:
        print(f"No .sdgui files found in {folder_path}")
        return
    
    print(f"Found {len(sdgui_files)} .sdgui files to merge:")
    for f in sdgui_files:
        print(f"  - {f.name}")
    
    # Initialize merged structure
    merged = None
    all_impacts = {}
    all_effects = {}
    all_scenarios = {}
    scenario_impacts = defaultdict(lambda: defaultdict(list))
    deleted_impacts_set = set()
    
    # Read and merge all files
    for sdgui_file in sdgui_files:
        print(f"\nProcessing {sdgui_file.name}...")
        
        with open(sdgui_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tables = data.get("tables", {})
        
        # Initialize merged structure with first file
        if merged is None:
            merged = {
                "version": data.get("version", 1),
                "gitHash": data.get("gitHash", ""),
                "tables": {
                    "effects": {},
                    "fields": tables.get("fields", {}),
                    "globals": tables.get("globals", {}),
                    "impacts": {},
                    "scenarios": {}
                }
            }
        
        # Merge effects
        effects = tables.get("effects", {})
        for eid, effect in effects.items():
            if eid not in all_effects:
                all_effects[eid] = effect
                print(f"  Added effect: {effect.get('name', 'Unnamed')}")
        
        # Merge impacts
        impacts = tables.get("impacts", {})
        for iid, impact in impacts.items():
            if iid not in all_impacts:
                all_impacts[iid] = impact
                parent_name = all_effects.get(impact.get('parent', ''), {}).get('name', 'Unknown')
                print(f"  Added impact: {iid} -> SDG {impact.get('sdgCode', '?')} on '{parent_name}'")
        
        # Merge scenarios
        scenarios = tables.get("scenarios", {})
        for sid, scenario in scenarios.items():
            if sid not in all_scenarios:
                all_scenarios[sid] = {
                    "id": scenario.get("id"),
                    "title": scenario.get("title", "Untitled scenario"),
                    "description": scenario.get("description", ""),
                    "impacts": {},
                    "deletedAt": scenario.get("deletedAt"),
                    "deletedImpacts": []
                }
                merged["tables"]["scenarios"][sid] = all_scenarios[sid]
                print(f"  Added scenario: {scenario.get('title', 'Untitled')}")
            
            # Merge scenario impacts
            scenario_impacts_data = scenario.get("impacts", {})
            for eid, impact_list in scenario_impacts_data.items():
                if not isinstance(impact_list, list):
                    continue
                for iid in impact_list:
                    if iid not in scenario_impacts[sid][eid]:
                        scenario_impacts[sid][eid].append(iid)
                        print(f"    Linked impact {iid[:20]}... to effect {eid[:20]}...")
            
            # Collect deleted impacts
            deleted_impacts_set.update(scenario.get("deletedImpacts", []))
    
    # Build final merged structure
    merged["tables"]["effects"] = all_effects
    merged["tables"]["impacts"] = all_impacts
    
    # Build scenario impacts
    for sid in all_scenarios.keys():
        if sid in merged["tables"]["scenarios"]:
            for eid in scenario_impacts[sid]:
                merged["tables"]["scenarios"][sid]["impacts"][eid] = scenario_impacts[sid][eid]
            merged["tables"]["scenarios"][sid]["deletedImpacts"] = list(deleted_impacts_set)
    
    # Write merged file
    output_path = folder / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Merge complete!")
    print(f"  Total effects: {len(all_effects)}")
    print(f"  Total impacts: {len(all_impacts)}")
    print(f"  Total scenarios: {len(all_scenarios)}")
    print(f"  Output file: {output_path}")
    
    return output_path

if __name__ == "__main__":
    import sys
    
    # Get folder path from command line or use current directory
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "."
    
    # Get output filename from command line or use default
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "combined.sdgui"
    
    print("=" * 60)
    print("SDGUI File Merger")
    print("=" * 60)
    print(f"Target folder: {folder_path}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    merge_sdgui_files(folder_path, output_file)
