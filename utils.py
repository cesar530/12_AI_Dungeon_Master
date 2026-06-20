"""
AI Dungeon Master - Utility Functions
======================================
Funciones de utilidad para generación de aventuras RPG.

Author: César Adrián Delgado Díaz
GitHub: https://github.com/cesar530
License: MIT
"""

import random
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Rich console for pretty printing
console = Console()


# =============================================================================
# ASCII ART GENERATION
# =============================================================================

ASCII_TILES = {
    'wall': '#',
    'floor': '.',
    'door': 'D',
    'chest': 'C',
    'enemy': 'E',
    'player': '@',
    'stairs_up': '<',
    'stairs_down': '>',
    'water': '~',
    'tree': 'T',
    'mountain': '^',
    'path': '=',
    'trap': 'X',
    'npc': 'N',
    'boss': 'B',
    'empty': ' '
}

ROOM_TEMPLATES = {
    'small': (5, 5),
    'medium': (8, 8),
    'large': (12, 10),
    'corridor_h': (10, 3),
    'corridor_v': (3, 10),
    'chamber': (15, 12)
}


def generate_ascii_map(
    width: int = 40,
    height: int = 20,
    num_rooms: int = 5,
    seed: Optional[int] = None
) -> str:
    """
    Genera un mapa ASCII de una mazmorra procedural.
    
    Args:
        width: Ancho del mapa en caracteres
        height: Alto del mapa en caracteres
        num_rooms: Número de habitaciones a generar
        seed: Semilla para reproducibilidad
        
    Returns:
        String con el mapa ASCII
    """
    if seed:
        random.seed(seed)
    
    # Initialize map with walls
    dungeon = [[ASCII_TILES['wall'] for _ in range(width)] for _ in range(height)]
    rooms = []
    
    # Generate rooms
    for _ in range(num_rooms * 3):  # Try multiple times to place rooms
        if len(rooms) >= num_rooms:
            break
            
        room_w = random.randint(4, min(10, width // 3))
        room_h = random.randint(4, min(8, height // 3))
        room_x = random.randint(1, width - room_w - 1)
        room_y = random.randint(1, height - room_h - 1)
        
        # Check for overlap
        new_room = (room_x, room_y, room_w, room_h)
        if not any(_rooms_overlap(new_room, r) for r in rooms):
            rooms.append(new_room)
            
            # Carve room
            for y in range(room_y, room_y + room_h):
                for x in range(room_x, room_x + room_w):
                    dungeon[y][x] = ASCII_TILES['floor']
    
    # Connect rooms with corridors
    for i in range(len(rooms) - 1):
        _connect_rooms(dungeon, rooms[i], rooms[i + 1])
    
    # Add features
    _add_dungeon_features(dungeon, rooms)
    
    # Convert to string
    return '\n'.join([''.join(row) for row in dungeon])


def _rooms_overlap(room1: Tuple, room2: Tuple, padding: int = 2) -> bool:
    """Check if two rooms overlap with padding."""
    x1, y1, w1, h1 = room1
    x2, y2, w2, h2 = room2
    
    return not (x1 + w1 + padding < x2 or x2 + w2 + padding < x1 or
                y1 + h1 + padding < y2 or y2 + h2 + padding < y1)


def _connect_rooms(dungeon: List[List[str]], room1: Tuple, room2: Tuple):
    """Connect two rooms with an L-shaped corridor."""
    x1, y1, w1, h1 = room1
    x2, y2, w2, h2 = room2
    
    # Center points
    cx1, cy1 = x1 + w1 // 2, y1 + h1 // 2
    cx2, cy2 = x2 + w2 // 2, y2 + h2 // 2
    
    # Carve horizontal then vertical
    if random.random() < 0.5:
        _carve_h_corridor(dungeon, cx1, cx2, cy1)
        _carve_v_corridor(dungeon, cy1, cy2, cx2)
    else:
        _carve_v_corridor(dungeon, cy1, cy2, cx1)
        _carve_h_corridor(dungeon, cx1, cx2, cy2)


def _carve_h_corridor(dungeon: List[List[str]], x1: int, x2: int, y: int):
    """Carve a horizontal corridor."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 < y < len(dungeon) - 1 and 0 < x < len(dungeon[0]) - 1:
            dungeon[y][x] = ASCII_TILES['floor']


def _carve_v_corridor(dungeon: List[List[str]], y1: int, y2: int, x: int):
    """Carve a vertical corridor."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 < y < len(dungeon) - 1 and 0 < x < len(dungeon[0]) - 1:
            dungeon[y][x] = ASCII_TILES['floor']


def _add_dungeon_features(dungeon: List[List[str]], rooms: List[Tuple]):
    """Add features like enemies, chests, etc. to the dungeon."""
    if not rooms:
        return
        
    # Player start in first room
    x, y, w, h = rooms[0]
    dungeon[y + h // 2][x + w // 2] = ASCII_TILES['player']
    
    # Stairs in last room
    if len(rooms) > 1:
        x, y, w, h = rooms[-1]
        dungeon[y + h // 2][x + w // 2] = ASCII_TILES['stairs_down']
    
    # Add enemies and chests in other rooms
    for room in rooms[1:-1] if len(rooms) > 2 else []:
        x, y, w, h = room
        
        # Random enemy placement
        if random.random() < 0.7:
            ex = random.randint(x + 1, x + w - 2)
            ey = random.randint(y + 1, y + h - 2)
            dungeon[ey][ex] = ASCII_TILES['enemy']
        
        # Random chest placement
        if random.random() < 0.4:
            cx = random.randint(x + 1, x + w - 2)
            cy = random.randint(y + 1, y + h - 2)
            if dungeon[cy][cx] == ASCII_TILES['floor']:
                dungeon[cy][cx] = ASCII_TILES['chest']


def generate_world_map(
    width: int = 60,
    height: int = 30,
    seed: Optional[int] = None
) -> str:
    """
    Genera un mapa ASCII del mundo exterior.
    
    Args:
        width: Ancho del mapa
        height: Alto del mapa
        seed: Semilla para reproducibilidad
        
    Returns:
        String con el mapa del mundo
    """
    if seed:
        random.seed(seed)
    
    world = [[ASCII_TILES['floor'] for _ in range(width)] for _ in range(height)]
    
    # Add mountains
    for _ in range(height * width // 20):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        world[y][x] = ASCII_TILES['mountain']
    
    # Add trees/forests
    for _ in range(height * width // 15):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        if world[y][x] == ASCII_TILES['floor']:
            world[y][x] = ASCII_TILES['tree']
    
    # Add water bodies
    num_lakes = random.randint(2, 5)
    for _ in range(num_lakes):
        lake_x = random.randint(5, width - 10)
        lake_y = random.randint(5, height - 10)
        lake_size = random.randint(3, 8)
        
        for dy in range(-lake_size, lake_size + 1):
            for dx in range(-lake_size, lake_size + 1):
                if dx * dx + dy * dy <= lake_size * lake_size:
                    ny, nx = lake_y + dy, lake_x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        world[ny][nx] = ASCII_TILES['water']
    
    # Add paths
    path_y = height // 2
    for x in range(width):
        world[path_y + random.randint(-1, 1)][x] = ASCII_TILES['path']
    
    return '\n'.join([''.join(row) for row in world])


# =============================================================================
# DISPLAY UTILITIES
# =============================================================================

def display_map(map_str: str, title: str = "Dungeon Map"):
    """Display a map with rich formatting."""
    console.print(Panel(map_str, title=title, border_style="green"))


def display_enemy(enemy: Dict):
    """Display enemy information in a styled panel."""
    table = Table(show_header=False, box=None)
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("🎭 Name", enemy.get('name', 'Unknown'))
    table.add_row("⚔️ Type", enemy.get('type', 'Unknown'))
    table.add_row("❤️ HP", str(enemy.get('hp', '???')))
    table.add_row("🗡️ Attack", str(enemy.get('attack', '???')))
    table.add_row("🛡️ Defense", str(enemy.get('defense', '???')))
    
    if enemy.get('abilities'):
        table.add_row("✨ Abilities", ', '.join(enemy['abilities']))
    
    console.print(Panel(table, title=f"[red]⚔️ {enemy.get('name', 'Enemy')}[/red]", border_style="red"))


def display_mission(mission: Dict):
    """Display mission information."""
    content = Text()
    content.append(f"📜 {mission.get('title', 'Unknown Mission')}\n\n", style="bold yellow")
    content.append(mission.get('description', 'No description available.'), style="white")
    content.append(f"\n\n🎯 Objective: ", style="cyan")
    content.append(mission.get('objective', 'Unknown'), style="white")
    content.append(f"\n💰 Reward: ", style="gold1")
    content.append(mission.get('reward', 'Unknown'), style="white")
    
    console.print(Panel(content, title="[bold blue]Quest[/bold blue]", border_style="blue"))


def display_dialogue(speaker: str, dialogue: str, emotion: str = "neutral"):
    """Display NPC dialogue."""
    emotion_styles = {
        'neutral': 'white',
        'happy': 'green',
        'angry': 'red',
        'sad': 'blue',
        'mysterious': 'magenta',
        'scared': 'yellow'
    }
    
    style = emotion_styles.get(emotion, 'white')
    console.print(f"[bold cyan]{speaker}:[/bold cyan]")
    console.print(Panel(dialogue, border_style=style))


def display_narrative(text: str, style: str = "italic"):
    """Display narrative text with atmospheric formatting."""
    console.print(f"[{style}]{text}[/{style}]")


# =============================================================================
# RPG DATA STRUCTURES
# =============================================================================

ENEMY_TYPES = {
    'goblin': {'base_hp': 15, 'base_attack': 5, 'base_defense': 2},
    'skeleton': {'base_hp': 20, 'base_attack': 6, 'base_defense': 3},
    'orc': {'base_hp': 35, 'base_attack': 10, 'base_defense': 5},
    'dragon': {'base_hp': 100, 'base_attack': 25, 'base_defense': 15},
    'lich': {'base_hp': 80, 'base_attack': 20, 'base_defense': 10},
    'troll': {'base_hp': 60, 'base_attack': 15, 'base_defense': 8},
    'vampire': {'base_hp': 50, 'base_attack': 18, 'base_defense': 6},
    'werewolf': {'base_hp': 45, 'base_attack': 16, 'base_defense': 4},
    'demon': {'base_hp': 90, 'base_attack': 22, 'base_defense': 12},
    'ghost': {'base_hp': 30, 'base_attack': 12, 'base_defense': 1}
}

MISSION_TYPES = [
    'rescue', 'assassination', 'retrieval', 'escort', 
    'exploration', 'defense', 'investigation', 'dungeon_clear'
]

LOCATIONS = [
    'Ancient Dungeon', 'Haunted Forest', 'Dragon\'s Lair', 
    'Abandoned Castle', 'Cursed Swamp', 'Crystal Caves',
    'Volcanic Temple', 'Frozen Citadel', 'Shadow Realm',
    'Enchanted Tower', 'Underground City', 'Sky Fortress'
]

REWARDS = [
    '100 gold coins', '500 gold coins', '1000 gold coins',
    'Legendary Sword', 'Magic Staff', 'Dragon Scale Armor',
    'Ring of Power', 'Ancient Artifact', 'Spell Book',
    'Title of Knight', 'Land Grant', 'Royal Favor'
]


def get_random_enemy_type() -> str:
    """Get a random enemy type."""
    return random.choice(list(ENEMY_TYPES.keys()))


def get_random_mission_type() -> str:
    """Get a random mission type."""
    return random.choice(MISSION_TYPES)


def get_random_location() -> str:
    """Get a random location."""
    return random.choice(LOCATIONS)


def get_random_reward() -> str:
    """Get a random reward."""
    return random.choice(REWARDS)


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

SYSTEM_PROMPT = """You are an experienced Dungeon Master for fantasy RPG games. 
Your role is to create immersive, engaging, and creative content for tabletop RPG adventures.
You should:
- Be descriptive and atmospheric in your narration
- Create balanced and interesting encounters
- Develop memorable NPCs with distinct personalities
- Craft engaging storylines with meaningful choices
- Use fantasy tropes creatively while avoiding clichés
- Maintain consistency in the world you create

Always respond in the requested format (JSON when specified)."""

MISSION_PROMPT = """Generate a detailed RPG quest/mission with the following structure:
- title: A compelling quest name
- description: 2-3 paragraphs of atmospheric backstory
- objective: Clear main goal
- secondary_objectives: List of optional goals
- reward: What the players receive upon completion
- difficulty: Easy/Medium/Hard/Legendary
- estimated_duration: In game sessions
- key_npcs: Important characters involved
- potential_twists: Plot twists that could occur

Context: {context}
Theme: {theme}
Player Level: {level}

Respond in JSON format."""

ENEMY_PROMPT = """Create a detailed enemy/monster for an RPG encounter:
- name: Unique creature name
- type: Base creature type (e.g., dragon, undead, demon)
- hp: Hit points (consider difficulty)
- attack: Attack power
- defense: Defense value
- abilities: List of special abilities (3-5)
- weakness: What they're vulnerable to
- description: Physical appearance and behavior
- lore: Brief backstory/origin
- tactics: How they fight in combat
- loot: What they drop when defeated

Difficulty Level: {difficulty}
Environment: {environment}
Theme: {theme}

Respond in JSON format."""

NARRATIVE_PROMPT = """Write atmospheric narrative text for this RPG scene:

Scene Type: {scene_type}
Location: {location}
Mood: {mood}
Characters Present: {characters}
Recent Events: {events}

Write 2-3 paragraphs of immersive, second-person narrative that sets the scene 
and engages the players. Include sensory details (sight, sound, smell, etc.)."""

DIALOGUE_PROMPT = """Create dialogue for this NPC interaction:

NPC Name: {npc_name}
NPC Role: {npc_role}
Personality: {personality}
Player's Question/Action: {player_action}
Context: {context}
NPC's Current Mood: {mood}

Write the NPC's response in character. Include:
- Their spoken dialogue
- Body language/actions (in parentheses)
- Any relevant information they might share
- Hints about their true nature or hidden knowledge (if applicable)"""

MAP_DESCRIPTION_PROMPT = """Analyze this ASCII map and provide a narrative description:

```
{ascii_map}
```

Legend:
# = Wall, . = Floor, D = Door, C = Chest, E = Enemy
@ = Player, < = Stairs Up, > = Stairs Down, ~ = Water
T = Tree, ^ = Mountain, = = Path, X = Trap, N = NPC, B = Boss

Describe this location as a Dungeon Master would, including:
- Overall atmosphere and environment
- Notable features and points of interest
- Potential dangers and opportunities
- Suggested encounter ideas"""


def get_prompt_template(prompt_type: str) -> str:
    """Get the appropriate prompt template."""
    templates = {
        'system': SYSTEM_PROMPT,
        'mission': MISSION_PROMPT,
        'enemy': ENEMY_PROMPT,
        'narrative': NARRATIVE_PROMPT,
        'dialogue': DIALOGUE_PROMPT,
        'map': MAP_DESCRIPTION_PROMPT
    }
    return templates.get(prompt_type, SYSTEM_PROMPT)


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_enemy_stats(enemy: Dict) -> bool:
    """Validate that enemy has required stats."""
    required = ['name', 'hp', 'attack', 'defense']
    return all(key in enemy for key in required)


def validate_mission(mission: Dict) -> bool:
    """Validate that mission has required fields."""
    required = ['title', 'description', 'objective', 'reward']
    return all(key in mission for key in required)


def scale_enemy_to_level(enemy: Dict, level: int) -> Dict:
    """Scale enemy stats based on player level."""
    scaling = 1 + (level - 1) * 0.15
    scaled = enemy.copy()
    scaled['hp'] = int(enemy.get('hp', 10) * scaling)
    scaled['attack'] = int(enemy.get('attack', 5) * scaling)
    scaled['defense'] = int(enemy.get('defense', 2) * scaling)
    scaled['level'] = level
    return scaled


if __name__ == "__main__":
    # Demo
    console.print("[bold green]AI Dungeon Master - Utils Demo[/bold green]\n")
    
    # Generate and display a dungeon map
    dungeon = generate_ascii_map(40, 15, num_rooms=4, seed=42)
    display_map(dungeon, "Demo Dungeon")
    
    # Display sample enemy
    sample_enemy = {
        'name': 'Shadow Wraith',
        'type': 'undead',
        'hp': 45,
        'attack': 12,
        'defense': 3,
        'abilities': ['Phase Shift', 'Life Drain', 'Fear Aura']
    }
    display_enemy(sample_enemy)
    
    # Display sample mission
    sample_mission = {
        'title': 'The Lost Artifact',
        'description': 'Ancient texts speak of a powerful artifact hidden deep within the ruins.',
        'objective': 'Retrieve the Orb of Shadows from the Ancient Temple',
        'reward': 'Legendary Magic Staff + 500 gold'
    }
    display_mission(sample_mission)
    
    console.print("\n[bold green]Utils loaded successfully![/bold green]")
