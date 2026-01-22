"""
LewtNanny CLI - Fully Featured Command Line Interface
Entropia Universe Loot Tracking and Financial Analytics
"""

import argparse
import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.app_config import app_config, AppConfig
from src.core.database import DatabaseManager
from src.services.game_data_service import GameDataService, WeaponCalculator
from src.services.loadout_service import LoadoutService, WeaponLoadout
from src.utils.paths import get_user_data_dir, ensure_user_data_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIOutput:
    """Handle CLI output formatting"""
    
    def __init__(self, json_output: bool = False, verbose: bool = False):
        self.json_output = json_output
        self.verbose = verbose
        self.data: List[Dict[str, Any]] = []
    
    def print(self, message: str, level: str = "info"):
        if self.json_output:
            self.data.append({"type": level, "message": message})
        else:
            print(message)
    
    def print_table(self, headers: List[str], rows: List[List[str]], title: str = ""):
        if self.json_output:
            self.data.append({
                "type": "table",
                "headers": headers,
                "rows": rows,
                "title": title
            })
        else:
            if title:
                print(f"\n{title}")
                print("=" * len(title))
            
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
            
            separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
            header_row = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"
            
            print(separator)
            print(header_row)
            print(separator)
            
            for row in rows:
                row_str = "|" + "|".join(f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)) + "|"
                print(row_str)
            print(separator)
    
    def print_json(self):
        if self.json_output:
            print(json.dumps(self.data, indent=2, default=str))
    
    def print_stats(self, stats: Dict[str, Any], title: str = "Statistics"):
        if self.json_output:
            self.data.append({"type": "stats", "title": title, "stats": stats})
        else:
            print(f"\n{title}")
            print("=" * len(title))
            for key, value in stats.items():
                key_formatted = key.replace("_", " ").title()
                print(f"  {key_formatted}: {value}")
    
    def print_error(self, message: str):
        self.print(f"ERROR: {message}", level="error")
    
    def print_warning(self, message: str):
        self.print(f"WARNING: {message}", level="warning")


async def run_command(args: argparse.Namespace, output: CLIOutput) -> int:
    """Run the appropriate command based on arguments"""
    
    if args.command == "stats":
        return await cmd_stats(output)
    elif args.command == "search":
        return await cmd_search(args, output)
    elif args.command == "show":
        return await cmd_show(args, output)
    elif args.command == "weapons":
        return await cmd_weapons(args, output)
    elif args.command == "attachments":
        return await cmd_attachments(args, output)
    elif args.command == "resources":
        return await cmd_resources(args, output)
    elif args.command == "blueprints" or args.command == "bp":
        return await cmd_blueprints(args, output)
    elif args.command == "sessions":
        return await cmd_sessions(output)
    elif args.command == "session":
        return await cmd_session(args, output)
    elif args.command == "db":
        return await cmd_db(args, output)
    elif args.command == "calc":
        return await cmd_calc(args, output)
    elif args.command == "loadout":
        return await cmd_loadout(args, output)
    elif args.command == "gui":
        return cmd_gui(args, output)
    elif args.command == "monitor":
        return await cmd_monitor(args, output)
    else:
        output.print_error(f"Unknown command: {args.command}")
        return 1
    
    return 0


async def cmd_stats(output: CLIOutput) -> int:
    """Show database statistics"""
    try:
        db_manager = DatabaseManager()
        game_service = GameDataService()
        
        db_stats = await db_manager.get_session_count()
        weapon_count = await db_manager.get_weapon_count()
        game_counts = await game_service.get_counts()
        
        stats = {
            "Sessions": db_stats,
            "Weapons": weapon_count,
            "Attachments": game_counts.get('attachments', 0),
            "Resources": game_counts.get('resources', 0),
            "Blueprints": game_counts.get('blueprints', 0),
            "Blueprint Materials": game_counts.get('blueprint_materials', 0),
        }
        
        output.print_stats(stats, "Database Statistics")
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_search(args: argparse.Namespace, output: CLIOutput) -> int:
    """Search for items in the database"""
    try:
        game_service = GameDataService()
        query = args.query
        item_type = args.type or "all"
        limit = args.limit or 50
        
        results = {"weapons": [], "attachments": [], "resources": [], "blueprints": []}
        
        if item_type in ["all", "weapon"]:
            weapons = await game_service.search_weapons(query, limit)
            results["weapons"] = [{"name": w.name, "type": w.weapon_type, "dps": str(w.dps)} for w in weapons[:limit]]
        
        if item_type in ["all", "attachment"]:
            attachments = await game_service.search_attachments(query)
            results["attachments"] = [{"name": a.name, "type": a.attachment_type} for a in attachments[:limit]]
        
        if item_type in ["all", "resource"]:
            resources = await game_service.search_resources(query, limit)
            results["resources"] = [{"name": r.name, "tt_value": str(r.tt_value)} for r in resources[:limit]]
        
        if item_type in ["all", "blueprint"]:
            blueprints = await game_service.search_blueprints(query)
            results["blueprints"] = [{"name": bp.name, "result": bp.result_item} for bp in blueprints[:limit]]
        
        if output.json_output:
            output.data.append({"type": "search_results", "query": query, "results": results})
        else:
            print(f"\nSearch Results for: '{query}'")
            print("=" * 50)
            
            for category, items in results.items():
                if items:
                    print(f"\n{category.title()}:")
                    for item in items[:10]:
                        if category == "weapons":
                            print(f"  {item['name']} ({item['type']}) - DPS: {item['dps']}")
                        elif category == "attachments":
                            print(f"  {item['name']} ({item['type']})")
                        elif category == "resources":
                            print(f"  {item['name']} - TT: {item['tt_value']}")
                        elif category == "blueprints":
                            print(f"  {item['name']} -> {item['result']}")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_show(args: argparse.Namespace, output: CLIOutput) -> int:
    """Show detailed information about an item"""
    try:
        game_service = GameDataService()
        item_name = args.name
        item_type = args.type
        
        if item_type in [None, "weapon"]:
            weapon = await game_service.get_weapon_by_name(item_name)
            if weapon:
                stats = await game_service.get_weapon_stats(item_name)
                if output.json_output:
                    output.data.append({"type": "weapon", "data": {
                        "name": weapon.name,
                        "type": weapon.weapon_type,
                        "damage": str(stats.damage) if stats else "N/A",
                        "ammo_burn": str(stats.ammo_burn) if stats else "N/A",
                        "decay": str(weapon.decay),
                        "dps": str(weapon.dps),
                        "eco": str(weapon.eco),
                        "range": weapon.range_value,
                        "reload_time": str(stats.reload_time) if stats else "N/A"
                    }})
                else:
                    print(f"\nWeapon: {weapon.name}")
                    print("-" * 40)
                    print(f"  Type: {weapon.weapon_type}")
                    print(f"  Damage: {stats.damage if stats else 'N/A'}")
                    print(f"  Ammo Burn: {stats.ammo_burn if stats else 'N/A'}")
                    print(f"  Decay: {weapon.decay}")
                    print(f"  DPS: {weapon.dps}")
                    print(f"  Economy: {weapon.eco}")
                    print(f"  Range: {weapon.range_value}")
                    print(f"  Reload Time: {stats.reload_time if stats else 'N/A'}")
                return 0
        
        if item_type in [None, "attachment"]:
            attachment = await game_service.get_attachment_by_name(item_name)
            if attachment:
                if output.json_output:
                    output.data.append({"type": "attachment", "data": {
                        "name": attachment.name,
                        "type": attachment.attachment_type,
                        "damage_bonus": str(attachment.damage_bonus),
                        "ammo_bonus": str(attachment.ammo_bonus),
                        "decay_modifier": str(attachment.decay_modifier),
                        "economy_bonus": str(attachment.economy_bonus),
                        "range_bonus": attachment.range_bonus
                    }})
                else:
                    print(f"\nAttachment: {attachment.name}")
                    print("-" * 40)
                    print(f"  Type: {attachment.attachment_type}")
                    print(f"  Damage Bonus: {attachment.damage_bonus}")
                    print(f"  Ammo Bonus: {attachment.ammo_bonus}")
                    print(f"  Decay Modifier: {attachment.decay_modifier}")
                    print(f"  Economy Bonus: {attachment.economy_bonus}")
                    print(f"  Range Bonus: {attachment.range_bonus}")
                return 0
        
        if item_type in [None, "blueprint"]:
            blueprint = await game_service.get_blueprint_by_name(item_name)
            if blueprint:
                if output.json_output:
                    materials = [{"name": m.material_name, "quantity": m.quantity} for m in blueprint.materials]
                    output.data.append({"type": "blueprint", "data": {
                        "name": blueprint.name,
                        "result_item": blueprint.result_item,
                        "result_quantity": blueprint.result_quantity,
                        "skill_required": blueprint.skill_required,
                        "condition_limit": blueprint.condition_limit,
                        "materials": materials
                    }})
                else:
                    print(f"\nBlueprint: {blueprint.name}")
                    print("-" * 40)
                    print(f"  Result Item: {blueprint.result_item}")
                    print(f"  Result Quantity: {blueprint.result_quantity}")
                    print(f"  Skill Required: {blueprint.skill_required or 'None'}")
                    print(f"  Condition Limit: {blueprint.condition_limit}")
                    print(f"\n  Materials:")
                    for mat in blueprint.materials:
                        print(f"    {mat.material_name}: {mat.quantity}")
                return 0
        
        output.print_error(f"Item not found: {item_name}")
        return 1
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_weapons(args: argparse.Namespace, output: CLIOutput) -> int:
    """Weapon commands"""
    try:
        game_service = GameDataService()
        
        if args.subcommand == "best":
            limit = args.limit or 10
            weapons = await game_service.get_best_weapons_by_dps(limit)
            
            rows = [[w.name, w.weapon_type, str(w.dps), str(w.eco)] for w in weapons]
            output.print_table(["Name", "Type", "DPS", "Economy"], rows, f"Top {limit} Weapons by DPS")
            
        elif args.subcommand == "eco":
            limit = args.limit or 10
            weapons = await game_service.get_best_weapons_by_eco(limit)
            
            rows = [[w.name, w.weapon_type, str(w.eco), str(w.dps)] for w in weapons]
            output.print_table(["Name", "Type", "Economy", "DPS"], rows, f"Top {limit} Weapons by Economy")
            
        elif args.subcommand == "type":
            weapon_type = args.weapon_type
            if not weapon_type:
                output.print_error("Weapon type required")
                return 1
            weapons = await game_service.get_weapons_by_type(weapon_type)
            
            rows = [[w.name, str(w.dps), str(w.eco)] for w in weapons]
            output.print_table(["Name", "DPS", "Economy"], rows, f"Weapons of Type: {weapon_type}")
            
        else:
            weapons = await game_service.get_all_weapons()
            
            rows = [[w.name, w.weapon_type, str(w.dps), str(w.eco)] for w in weapons[:100]]
            output.print_table(["Name", "Type", "DPS", "Economy"], rows, f"All Weapons ({len(weapons)} total)")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_attachments(args: argparse.Namespace, output: CLIOutput) -> int:
    """Attachment commands"""
    try:
        game_service = GameDataService()
        
        if args.subcommand == "type":
            attachment_type = args.attachment_type
            if not attachment_type:
                output.print_error("Attachment type required")
                return 1
            attachments = await game_service.get_attachments_by_type(attachment_type)
            
            rows = [[a.name, str(a.damage_bonus), str(a.decay_modifier)] for a in attachments]
            output.print_table(["Name", "Dmg Bonus", "Decay Mod"], rows, f"Attachments of Type: {attachment_type}")
        else:
            attachments = await game_service.get_all_attachments()
            
            rows = [[a.name, a.attachment_type, str(a.damage_bonus)] for a in attachments[:100]]
            output.print_table(["Name", "Type", "Damage Bonus"], rows, f"All Attachments ({len(attachments)} total)")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_resources(args: argparse.Namespace, output: CLIOutput) -> int:
    """Resource commands"""
    try:
        game_service = GameDataService()
        
        if args.subcommand == "search":
            query = args.query
            resources = await game_service.search_resources(query)
            
            rows = [[r.name, str(r.tt_value)] for r in resources[:50]]
            output.print_table(["Name", "TT Value"], rows, f"Resources matching: '{query}'")
            
        elif args.subcommand == "tt":
            min_tt = args.min_tt or 0
            max_tt = args.max_tt or 1000
            resources = await game_service.get_resources_by_tt_value(min_tt, max_tt)
            
            rows = [[r.name, str(r.tt_value)] for r in resources[:50]]
            output.print_table(["Name", "TT Value"], rows, f"Resources (TT {min_tt}-{max_tt})")
            
        else:
            resources = await game_service.get_all_resources()
            
            rows = [[r.name, str(r.tt_value)] for r in resources[:100]]
            output.print_table(["Name", "TT Value"], rows, f"All Resources ({len(resources)} total)")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_blueprints(args: argparse.Namespace, output: CLIOutput) -> int:
    """Blueprint commands"""
    try:
        game_service = GameDataService()
        
        if args.subcommand == "search":
            query = args.query
            blueprints = await game_service.search_blueprints(query)
            
            rows = [[bp.name, bp.result_item] for bp in blueprints[:50]]
            output.print_table(["Name", "Result"], rows, f"Blueprints matching: '{query}'")
            
        elif args.subcommand in ["materials", "uses"]:
            material_name = args.material
            if not material_name:
                output.print_error("Material name required")
                return 1
            blueprints = await game_service.get_blueprints_by_material(material_name)
            
            rows = [[bp.name, bp.result_item] for bp in blueprints]
            output.print_table(["Name", "Result"], rows, f"Blueprints using: '{material_name}'")
            
        elif args.subcommand in ["cost", "costcalc"]:
            blueprint_name = args.blueprint
            if not blueprint_name:
                output.print_error("Blueprint name required")
                return 1
            cost = await game_service.calculate_blueprint_cost(blueprint_name)
            
            if output.json_output:
                output.data.append({"type": "blueprint_cost", "blueprint": blueprint_name, "cost": cost})
            else:
                print(f"\nBlueprint Cost: {blueprint_name}")
                print("-" * 40)
                print(f"  Total Material Cost: {cost:.2f} PED")
            
        else:
            blueprints = await game_service.get_all_blueprints()
            
            rows = [[bp.name, bp.result_item, str(len(bp.materials)) + " materials"] for bp in blueprints[:50]]
            output.print_table(["Name", "Result", "Materials"], rows, f"All Blueprints ({len(blueprints)} total)")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_sessions(output: CLIOutput) -> int:
    """List all sessions"""
    try:
        db_manager = DatabaseManager()
        sessions = await db_manager.get_all_sessions()
        
        if not sessions:
            output.print("No sessions found")
            return 0
        
        rows = [[s['id'][:8], s['activity_type'], str(s['total_cost']), str(s['total_return']), str(s['start_time'])[:19]] for s in sessions]
        output.print_table(["ID", "Activity", "Cost", "Return", "Start Time"], rows, f"Sessions ({len(sessions)} total)")
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_session(args: argparse.Namespace, output: CLIOutput) -> int:
    """Session management commands"""
    try:
        db_manager = DatabaseManager()
        
        if args.subcommand == "start":
            activity_type = args.activity_type or "hunting"
            import uuid
            session_id = str(uuid.uuid4())[:8]
            success = await db_manager.create_session(session_id, activity_type)
            
            if success:
                output.print(f"Session started: {session_id} ({activity_type})")
            else:
                output.print_error("Failed to create session")
                return 1
                
        elif args.subcommand == "end":
            sessions = await db_manager.get_all_sessions()
            if sessions:
                current_session = sessions[0]
                await db_manager.update_session_end(current_session['id'])
                output.print(f"Session ended: {current_session['id']}")
            else:
                output.print_error("No active session")
                return 1
                
        elif args.subcommand == "stats":
            session_id = args.session_id
            if not session_id:
                sessions = await db_manager.get_all_sessions()
                if sessions:
                    session_id = sessions[0]['id']
            
            if session_id:
                stats = await db_manager.get_session_stats(session_id)
                events = await db_manager.get_session_events(session_id)
                
                stats['events'] = len(events)
                output.print_stats(stats, f"Session Statistics: {session_id}")
            else:
                output.print_error("No session found")
                return 1
                
        elif args.subcommand == "delete":
            session_id = args.session_id
            if not session_id:
                output.print_error("Session ID required")
                return 1
            
            success = await db_manager.delete_session(session_id)
            if success:
                output.print(f"Session deleted: {session_id}")
            else:
                output.print_error("Failed to delete session")
                return 1
                
        elif args.subcommand == "clear":
            await db_manager.delete_all_sessions()
            output.print("All sessions deleted")
            
        else:
            output.print_error(f"Unknown session command: {args.subcommand}")
            return 1
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_db(args: argparse.Namespace, output: CLIOutput) -> int:
    """Database management commands"""
    try:
        db_path = get_user_data_dir() / "lewtnanny.db"

        if args.subcommand == "info":
            if db_path.exists():
                size_kb = db_path.stat().st_size / 1024
                stats = {
                    "Database Path": str(db_path),
                    "Size": f"{size_kb:.2f} KB",
                    "Modified": datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
                }
                output.print_stats(stats, "Database Information")
            else:
                output.print_error("Database not found")
                return 1
                
        elif args.subcommand == "migrate":
            db_manager = DatabaseManager()
            await db_manager.initialize()
            output.print("Database migration complete")
            
        elif args.subcommand == "vacuum":
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM")
            conn.close()
            output.print("Database optimized (VACUUM complete)")
            
        elif args.subcommand == "backup":
            import shutil
            data_dir = ensure_user_data_dir()
            backup_path = data_dir / f"lewtnanny_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy(db_path, backup_path)
            output.print(f"Backup created: {backup_path}")
            
        else:
            output.print_error(f"Unknown db command: {args.subcommand}")
            return 1
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_calc(args: argparse.Namespace, output: CLIOutput) -> int:
    """Calculation commands"""
    try:
        calculator = WeaponCalculator()
        
        if args.subcommand == "weapon":
            weapon_name = args.weapon
            if not weapon_name:
                output.print_error("Weapon name required")
                return 1
            
            amplifier = args.amplifier
            scope = args.scope
            damage_enh = args.damage or 0
            economy_enh = args.economy or 0
            
            stats = await calculator.calculate_enhanced_stats(
                weapon_name, amplifier, scope, damage_enh, economy_enh
            )
            
            if stats:
                if output.json_output:
                    output.data.append({"type": "weapon_calc", "data": stats.to_dict()})
                else:
                    print(f"\nWeapon Statistics: {weapon_name}")
                    print("-" * 40)
                    print(f"  Damage: {stats.damage:.2f}")
                    print(f"  Ammo Burn: {stats.ammo_burn:.4f}")
                    print(f"  Decay: {stats.decay:.4f}")
                    print(f"  Cost/Shot: {stats.total_cost_per_shot:.4f} PED")
                    print(f"  DPS: {stats.dps:.2f}")
                    print(f"  Damage/PEC: {stats.damage_per_ped:.2f}")
                    print(f"  Effective Range: {stats.effective_range}")
            else:
                output.print_error(f"Weapon not found: {weapon_name}")
                return 1
                
        elif args.subcommand == "dps":
            weapon_name = args.weapon
            if not weapon_name:
                output.print_error("Weapon name required")
                return 1
            
            stats = await calculator.calculate_enhanced_stats(weapon_name)
            if stats:
                output.print(f"{weapon_name} DPS: {stats.dps:.2f}")
            else:
                output.print_error(f"Weapon not found: {weapon_name}")
                return 1
                
        elif args.subcommand == "cost":
            weapon_name = args.weapon
            shots = args.shots or 1
            if not weapon_name:
                output.print_error("Weapon name required")
                return 1
            
            stats = await calculator.calculate_enhanced_stats(weapon_name)
            if stats:
                total_cost = stats.total_cost_per_shot * shots
                output.print(f"{weapon_name} cost for {shots} shots: {total_cost:.4f} PED")
            else:
                output.print_error(f"Weapon not found: {weapon_name}")
                return 1
        
        else:
            output.print_error(f"Unknown calc command: {args.subcommand}")
            return 1
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


async def cmd_loadout(args: argparse.Namespace, output: CLIOutput) -> int:
    """Loadout management commands"""
    try:
        service = LoadoutService()
        
        if args.subcommand in [None, "list"]:
            loadouts = await service.get_all_loadouts()
            if not loadouts:
                output.print("No loadouts found")
                return 0
            
            rows = [[l.name, l.weapon, l.amplifier or "-", str(l.damage_enh)] for l in loadouts]
            output.print_table(["Name", "Weapon", "Amplifier", "Dmg+"], rows, f"Loadouts ({len(loadouts)} total)")
            
        elif args.subcommand in ["show", "get"]:
            loadout = await service.get_loadout_by_name(args.name)
            if loadout:
                if output.json_output:
                    output.data.append({"type": "loadout", "data": loadout.to_dict()})
                else:
                    print(f"\nLoadout: {loadout.name}")
                    print("-" * 40)
                    print(f"  Weapon: {loadout.weapon}")
                    print(f"  Amplifier: {loadout.amplifier or 'None'}")
                    print(f"  Scope: {loadout.scope or 'None'}")
                    print(f"  Sight 1: {loadout.sight_1 or 'None'}")
                    print(f"  Sight 2: {loadout.sight_2 or 'None'}")
                    print(f"  Damage Enh: {loadout.damage_enh}")
                    print(f"  Accuracy Enh: {loadout.accuracy_enh}")
                    print(f"  Economy Enh: {loadout.economy_enh}")
                    
                    # Calculate stats for this loadout
                    calculator = WeaponCalculator()
                    stats = await calculator.calculate_enhanced_stats(
                        loadout.weapon,
                        loadout.amplifier,
                        loadout.scope,
                        loadout.damage_enh,
                        loadout.economy_enh
                    )
                    if stats:
                        print(f"\n  Calculated Stats:")
                        print(f"    DPS: {stats.dps:.2f}")
                        print(f"    Cost/Shot: {stats.total_cost_per_shot:.4f} PED")
                        print(f"    Damage/PEC: {stats.damage_per_ped:.2f}")
            else:
                output.print_error(f"Loadout not found: {args.name}")
                return 1
                
        elif args.subcommand == "add":
            loadout = WeaponLoadout(
                name=args.name,
                weapon=args.weapon,
                amplifier=args.amplifier,
                scope=args.scope,
                damage_enh=args.damage or 0,
                economy_enh=args.economy or 0
            )
            loadout_id = await service.create_loadout(loadout)
            output.print(f"Loadout '{args.name}' created with ID: {loadout_id}")
            
        else:
            output.print_error(f"Unknown loadout command: {args.subcommand}")
            return 1
        
        return 0
    except Exception as e:
        output.print_error(str(e))
        return 1


def cmd_gui(args: argparse.Namespace, output: CLIOutput) -> int:
    """Launch GUI application"""
    from main import main as gui_main
    output.print("Launching GUI...")
    return gui_main()


async def cmd_monitor(args: argparse.Namespace, output: CLIOutput) -> int:
    """Chat log monitoring"""
    import json

    config_path = get_user_data_dir() / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        chat_path = config.get("chat_monitoring", {}).get("log_file_path", "chat.log")
    else:
        chat_path = "chat.log"
    
    if not Path(chat_path).exists():
        output.print_error(f"Chat log not found: {chat_path}")
        return 1
    
    if args.subcommand == "tail":
        num_lines = args.lines or 10
        try:
            lines = []
            with open(chat_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    lines.append(line.rstrip())
                    if len(lines) > 1000:
                        lines.pop(0)
            
            recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
            output.print(f"Last {len(recent_lines)} lines from {chat_path}:")
            print("-" * 60)
            for line in recent_lines:
                print(line)
            return 0
        except Exception as e:
            output.print_error(f"Error reading chat log: {e}")
            return 1
    
    if args.subcommand == "run":
        return await cmd_monitor_run(args, output, chat_path)
    
    return 1


async def cmd_monitor_run(args: argparse.Namespace, output: CLIOutput, chat_path: str) -> int:
    """Run continuous chat log monitoring with event parsing"""
    from datetime import datetime
    from src.core.database import DatabaseManager
    from src.services.loadout_service import LoadoutService
    
    print("=" * 70)
    print("LewtNanny Chat Monitor - Continuous Mode")
    print("=" * 70)
    print(f"Chat Log: {chat_path}")
    print(f"Database: {get_user_data_dir() / 'lewtnanny.db'}")
    
    # Get loadout info if specified
    loadout_name = args.loadout
    if loadout_name:
        service = LoadoutService()
        loadout = await service.get_loadout_by_name(loadout_name)
        if loadout:
            print(f"Loadout: {loadout.name}")
            print(f"  Weapon: {loadout.weapon}")
            print(f"  Amplifier: {loadout.amplifier or 'None'}")
        else:
            print(f"Warning: Loadout '{loadout_name}' not found")
    
    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Create session
    session_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    await db_manager.create_session(session_id, "hunting")
    print(f"Session: {session_id}")
    print("-" * 70)
    print("Monitoring for events... Press Ctrl+C to stop")
    print("-" * 70)
    
    # Compile patterns for event parsing (with timestamp prefix)
    patterns = {
        'damage': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[System\]\s+\[\]\s+You\s+inflicted\s+([\d.]+)\s+points\s+of\s+damage'),
        'damage_taken': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[System\]\s+\[\]\s+You\s+took\s+([\d.]+)\s+points\s+of\s+damage'),
        'loot': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[System\]\s+\[\]\s+You\s+received\s+(.+?)\s+x\s*\(\d+\)\s+Value:\s+([\d.]+)\s+PED'),
        'global': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[Globals\]\s+\[\]\s+(.+?)\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?'),
        'global_team': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[Globals\]\s+\[\]\s+Team\s+"([^"]+)"\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?'),
        'mining': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[Globals\]\s+\[\]\s+(.+?)\s+found\s+a\s+deposit\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!'),
        'craft': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[Globals\]\s+\[\]\s+(.+?)\s+constructed\s+an\s+item\s+\((.+?)\)\s+worth\s+(\d+)\s+PED!'),
        'hof': re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[Globals\]\s+\[\]\s+A\s+record\s+has\s+been\s+added\s+to\s+the\s+Hall\s+of\s+Fame!'),
    }
    
    event_counts = {"damage": 0, "loot": 0, "global": 0, "mining": 0, "craft": 0, "other": 0}
    last_size = Path(chat_path).stat().st_size if Path(chat_path).exists() else 0
    
    try:
        while True:
            await asyncio.sleep(0.5)
            
            if not Path(chat_path).exists():
                continue
            
            current_size = Path(chat_path).stat().st_size
            
            if current_size > last_size:
                with open(chat_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    last_size = current_size
                    
                    for line in new_content.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        
                        event_type = None
                        event_data = None
                        
                        # Check for damage (your attacks)
                        dmg_match = patterns['damage'].search(line)
                        if dmg_match:
                            damage = float(dmg_match.group(1))
                            event_type = "DAMAGE"
                            event_data = {"damage": damage}
                            event_counts["damage"] += 1
                        
                        # Check for damage taken
                        dmg_taken = patterns['damage_taken'].search(line)
                        if dmg_taken and not event_type:
                            damage = float(dmg_taken.group(1))
                            event_type = "DAMAGE_TAKEN"
                            event_data = {"damage_taken": damage}
                            event_counts["damage"] += 1
                        
                        # Check for loot
                        loot_match = patterns['loot'].search(line)
                        if loot_match and not event_type:
                            item = loot_match.group(1)
                            value = float(loot_match.group(2))
                            event_type = "LOOT"
                            event_data = {"item": item, "value": value}
                            event_counts["loot"] += 1
                        
                        # Check for global kills
                        global_match = patterns['global'].search(line)
                        if global_match and not event_type:
                            player = global_match.group(1) or "Unknown"
                            creature = global_match.group(2)
                            value = float(global_match.group(3))
                            is_hof = patterns['hof'].search(line) is not None
                            event_type = "GLOBAL"
                            event_data = {"player": player, "creature": creature, "value": value, "hof": is_hof}
                            event_counts["global"] += 1
                        
                        # Check for team global kills
                        team_match = patterns['global_team'].search(line)
                        if team_match and not event_type:
                            team = team_match.group(1)
                            creature = team_match.group(2)
                            value = float(team_match.group(3))
                            event_type = "TEAM_GLOBAL"
                            event_data = {"team": team, "creature": creature, "value": value}
                            event_counts["global"] += 1
                        
                        # Check for mining globals
                        mine_match = patterns['mining'].search(line)
                        if mine_match and not event_type:
                            player = mine_match.group(1)
                            deposit = mine_match.group(2)
                            value = float(mine_match.group(3))
                            event_type = "MINING"
                            event_data = {"player": player, "deposit": deposit, "value": value}
                            event_counts["mining"] += 1
                        
                        # Check for crafting globals
                        craft_match = patterns['craft'].search(line)
                        if craft_match and not event_type:
                            player = craft_match.group(1)
                            item = craft_match.group(2)
                            value = float(craft_match.group(3))
                            event_type = "CRAFT"
                            event_data = {"player": player, "item": item, "value": value}
                            event_counts["craft"] += 1
                        
                        # Print and save event
                        if event_type:
                            timestamp = line.split(' ')[0] + ' ' + line.split(' ')[1]
                            print(f"[{timestamp}] {event_type}: {json.dumps(event_data)}")
                            
                            # Save to database
                            await db_manager.add_event({
                                'event_type': event_type.lower(),
                                'activity_type': 'hunting',
                                'raw_message': line,
                                'parsed_data': event_data,
                                'session_id': session_id
                            })
                        else:
                            # Count as "other" every 50 lines to avoid spam
                            event_counts["other"] += 1
                            if event_counts["other"] % 50 == 0:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ... (other activity)")
                
                # Print periodic stats
                if sum(event_counts.values()) > 0:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stats: Dmg={event_counts['damage']} Loot={event_counts['loot']} Global={event_counts['global']} Mine={event_counts['mining']} Craft={event_counts['craft']}")
                    print("-" * 70)
                    
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Session Summary")
        print("=" * 70)
        print(f"Damage events: {event_counts['damage']}")
        print(f"Loot events: {event_counts['loot']}")
        print(f"Global kills: {event_counts['global']}")
        print(f"Mining finds: {event_counts['mining']}")
        print(f"Crafting: {event_counts['craft']}")
        print(f"Session ID: {session_id}")
        print("Monitor stopped.")
        return 0
    
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser with subcommands"""
    parser = argparse.ArgumentParser(
        prog="lewtnanny",
        description="LewtNanny - Entropia Universe Loot Tracking and Financial Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_commands.py stats
  python cli_commands.py search "Omegaton"
  python cli_commands.py weapons best --limit 10
  python cli_commands.py session start hunting
  python cli_commands.py calc weapon "Omegaton A100" --amp "Magner" --shots 1000
  python cli_commands.py db info
  python cli_commands.py monitor run --loadout zx
        """
    )
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    search_parser = subparsers.add_parser("search", help="Search for items")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", "-t", choices=["weapon", "attachment", "resource", "blueprint", "all"], default="all")
    search_parser.add_argument("--limit", "-l", type=int, default=50)
    
    show_parser = subparsers.add_parser("show", help="Show detailed item information")
    show_parser.add_argument("name", help="Item name")
    show_parser.add_argument("--type", "-t", choices=["weapon", "attachment", "resource", "blueprint"])
    
    weapons_parser = subparsers.add_parser("weapons", help="Weapon commands")
    weapons_sub = weapons_parser.add_subparsers(dest="subcommand", help="Weapon subcommands")
    weapons_sub.add_parser("list", help="List all weapons")
    weapons_sub.add_parser("best", help="Show top weapons by DPS").add_argument("--limit", "-l", type=int, default=10)
    weapons_sub.add_parser("eco", help="Show top weapons by economy").add_argument("--limit", "-l", type=int, default=10)
    weapons_sub.add_parser("type", help="List weapons by type").add_argument("weapon_type", help="Weapon type (e.g., Rifle, Pistol)")
    
    attachments_parser = subparsers.add_parser("attachments", help="Attachment commands")
    attachments_sub = attachments_parser.add_subparsers(dest="subcommand", help="Attachment subcommands")
    attachments_sub.add_parser("list", help="List all attachments")
    attachments_sub.add_parser("type", help="List attachments by type").add_argument("attachment_type", help="Attachment type (e.g., BLP Amp, Scope)")
    
    resources_parser = subparsers.add_parser("resources", help="Resource commands")
    resources_sub = resources_parser.add_subparsers(dest="subcommand", help="Resource subcommands")
    resources_sub.add_parser("list", help="List all resources")
    resources_sub.add_parser("search", help="Search resources").add_argument("query", help="Search query")
    resources_tt_parser = resources_sub.add_parser("tt", help="List resources by TT value")
    resources_tt_parser.add_argument("--min", dest="min_tt", type=float)
    resources_tt_parser.add_argument("--max", dest="max_tt", type=float)
    
    blueprints_parser = subparsers.add_parser("blueprints", help="Blueprint commands")
    blueprints_parser.add_argument("--bp-alias", dest="bp_alias", help=argparse.SUPPRESS)
    
    def make_bp_alias(name):
        subparsers._name_parser_map[name] = blueprints_parser
    
    blueprints_sub = blueprints_parser.add_subparsers(dest="subcommand", help="Blueprint subcommands")
    blueprints_sub.add_parser("list", help="List all blueprints")
    blueprints_sub.add_parser("search", help="Search blueprints").add_argument("query", help="Search query")
    blueprints_sub.add_parser("materials", help="Find blueprints using a material").add_argument("material", help="Material name")
    blueprints_sub.add_parser("uses", help="Find blueprints using a material").add_argument("material", help="Material name")
    blueprints_sub.add_parser("cost", help="Calculate blueprint cost").add_argument("blueprint", help="Blueprint name")
    blueprints_cost_parser = blueprints_sub.add_parser("costcalc", help="Calculate blueprint cost")
    blueprints_cost_parser.add_argument("blueprint", help="Blueprint name")
    
    sessions_parser = subparsers.add_parser("sessions", help="List all sessions")
    
    session_parser = subparsers.add_parser("session", help="Session management")
    session_sub = session_parser.add_subparsers(dest="subcommand", help="Session subcommands")
    session_sub.add_parser("start", help="Start a new session").add_argument("activity_type", nargs="?", default="hunting", help="Activity type")
    session_sub.add_parser("end", help="End current session")
    session_sub.add_parser("stats", help="Show session statistics").add_argument("session_id", nargs="?", help="Session ID")
    session_sub.add_parser("delete", help="Delete a session").add_argument("session_id", help="Session ID")
    session_sub.add_parser("clear", help="Delete all sessions")
    
    db_parser = subparsers.add_parser("db", help="Database management")
    db_sub = db_parser.add_subparsers(dest="subcommand", help="Database subcommands")
    db_sub.add_parser("info", help="Show database information")
    db_sub.add_parser("migrate", help="Run database migrations")
    db_sub.add_parser("vacuum", help="Optimize database")
    db_sub.add_parser("backup", help="Backup database")
    
    calc_parser = subparsers.add_parser("calc", help="Calculations")
    calc_sub = calc_parser.add_subparsers(dest="subcommand", help="Calculation subcommands")
    calc_sub_w = calc_sub.add_parser("weapon", help="Calculate weapon statistics")
    calc_sub_w.add_argument("weapon", help="Weapon name")
    calc_sub_w.add_argument("--amp", dest="amplifier", help="Amplifier name")
    calc_sub_w.add_argument("--scope", help="Scope name")
    calc_sub_w.add_argument("--damage", type=int, default=0, help="Damage enhancement level")
    calc_sub_w.add_argument("--economy", type=int, default=0, help="Economy enhancement level")
    calc_sub_dps = calc_sub.add_parser("dps", help="Calculate weapon DPS")
    calc_sub_dps.add_argument("weapon", help="Weapon name")
    
    calc_sub_cost = calc_sub.add_parser("cost", help="Calculate cost per shot")
    calc_sub_cost.add_argument("weapon", help="Weapon name")
    calc_sub_cost.add_argument("--shots", type=int, default=1)
    
    loadout_parser = subparsers.add_parser("loadout", help="Loadout management")
    loadout_sub = loadout_parser.add_subparsers(dest="subcommand", help="Loadout subcommands")
    loadout_sub.add_parser("list", help="List all loadouts")
    loadout_show = loadout_sub.add_parser("show", help="Show loadout details").add_argument("name", help="Loadout name")
    loadout_sub.add_parser("get", help="Get a loadout by name").add_argument("name", help="Loadout name")
    loadout_add = loadout_sub.add_parser("add", help="Create a new loadout")
    loadout_add.add_argument("--name", required=True, help="Loadout name")
    loadout_add.add_argument("--weapon", required=True, help="Weapon name")
    loadout_add.add_argument("--amp", dest="amplifier", help="Amplifier name")
    loadout_add.add_argument("--scope", help="Scope name")
    loadout_add.add_argument("--damage", type=int, default=0, help="Damage enhancement level")
    loadout_add.add_argument("--economy", type=int, default=0, help="Economy enhancement level")
    
    gui_parser = subparsers.add_parser("gui", help="Launch GUI application")
    
    monitor_parser = subparsers.add_parser("monitor", help="Chat log monitoring")
    monitor_sub = monitor_parser.add_subparsers(dest="subcommand", help="Monitor subcommands")
    monitor_tail = monitor_sub.add_parser("tail", help="Show last N lines from chat log")
    monitor_tail.add_argument("lines", nargs="?", type=int, default=10, help="Number of lines")
    monitor_run = monitor_sub.add_parser("run", help="Run continuous monitoring")
    monitor_run.add_argument("--loadout", help="Loadout name to use")
    
    return parser


def main() -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output = CLIOutput(json_output=args.json, verbose=args.verbose)
    
    if args.debug:
        output.print(f"Command: {args.command}")
        output.print(f"Arguments: {vars(args)}")
    
    try:
        code = asyncio.run(run_command(args, output))
    except KeyboardInterrupt:
        output.print("\nOperation cancelled")
        return 130
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        output.print_error(str(e))
        return 1
    
    if output.json_output and output.data:
        output.print_json()
    
    return code


if __name__ == '__main__':
    sys.exit(main())
