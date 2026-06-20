"""
AI Dungeon Master - RPG Adventure Generator
============================================
Sistema de generación de aventuras RPG utilizando LLMs.

Genera:
- Misiones y quests
- Enemigos y criaturas
- Narrativa atmosférica
- Diálogos de NPCs
- Mapas ASCII procedurales

Author: César Adrián Delgado Díaz
Portfolio: https://tu-portfolio.com
LinkedIn: https://www.linkedin.com/in/cesar-delgado-diaz
GitHub: https://github.com/cesar530
License: MIT
"""

import json
import os
import random
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import warnings

# Suppress numpy warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    from langchain_community.llms import Ollama
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain not available. Using fallback generation.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from utils import (
    generate_ascii_map, generate_world_map,
    display_map, display_enemy, display_mission, 
    display_dialogue, display_narrative,
    get_prompt_template, scale_enemy_to_level,
    ENEMY_TYPES, MISSION_TYPES, LOCATIONS, REWARDS,
    get_random_enemy_type, get_random_location, get_random_reward
)

# Load environment variables
load_dotenv()

# Rich console
console = Console()


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class Difficulty(Enum):
    """Difficulty levels for encounters and missions."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    LEGENDARY = "legendary"


class MissionType(Enum):
    """Types of missions/quests."""
    RESCUE = "rescue"
    ASSASSINATION = "assassination"
    RETRIEVAL = "retrieval"
    ESCORT = "escort"
    EXPLORATION = "exploration"
    DEFENSE = "defense"
    INVESTIGATION = "investigation"
    DUNGEON_CLEAR = "dungeon_clear"


@dataclass
class Enemy:
    """Data class representing an enemy creature."""
    name: str
    enemy_type: str
    hp: int
    attack: int
    defense: int
    abilities: List[str] = field(default_factory=list)
    weakness: str = ""
    description: str = ""
    lore: str = ""
    tactics: str = ""
    loot: List[str] = field(default_factory=list)
    level: int = 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Enemy':
        """Create from dictionary."""
        return cls(
            name=data.get('name', 'Unknown'),
            enemy_type=data.get('type', data.get('enemy_type', 'unknown')),
            hp=data.get('hp', 10),
            attack=data.get('attack', 5),
            defense=data.get('defense', 2),
            abilities=data.get('abilities', []),
            weakness=data.get('weakness', ''),
            description=data.get('description', ''),
            lore=data.get('lore', ''),
            tactics=data.get('tactics', ''),
            loot=data.get('loot', []),
            level=data.get('level', 1)
        )


@dataclass
class Mission:
    """Data class representing a quest/mission."""
    title: str
    description: str
    objective: str
    reward: str
    difficulty: str = "medium"
    secondary_objectives: List[str] = field(default_factory=list)
    estimated_duration: str = "1 session"
    key_npcs: List[str] = field(default_factory=list)
    potential_twists: List[str] = field(default_factory=list)
    location: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Mission':
        """Create from dictionary."""
        return cls(
            title=data.get('title', 'Unknown Quest'),
            description=data.get('description', ''),
            objective=data.get('objective', ''),
            reward=data.get('reward', 'Unknown'),
            difficulty=data.get('difficulty', 'medium'),
            secondary_objectives=data.get('secondary_objectives', []),
            estimated_duration=data.get('estimated_duration', '1 session'),
            key_npcs=data.get('key_npcs', []),
            potential_twists=data.get('potential_twists', []),
            location=data.get('location', '')
        )


@dataclass
class NPC:
    """Data class representing a non-player character."""
    name: str
    role: str
    personality: str
    appearance: str = ""
    background: str = ""
    secrets: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    dialogue_style: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


# =============================================================================
# LLM PROVIDERS
# =============================================================================

class LLMProvider:
    """Base class for LLM providers."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local models."""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.llm = None
        
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = Ollama(model=model, base_url=base_url)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not connect to Ollama: {e}[/yellow]")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""
        if self.llm:
            try:
                return self.llm.invoke(prompt)
            except Exception as e:
                console.print(f"[red]Error with Ollama: {e}[/red]")
                return self._fallback_generate(prompt)
        return self._fallback_generate(prompt)
    
    def _fallback_generate(self, prompt: str) -> str:
        """Fallback generation when Ollama is not available."""
        return FallbackGenerator.generate_from_prompt(prompt)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not initialize OpenAI: {e}[/yellow]")
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate text using OpenAI."""
        if self.client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 1000)
                )
                return response.choices[0].message.content
            except Exception as e:
                console.print(f"[red]Error with OpenAI: {e}[/red]")
                return FallbackGenerator.generate_from_prompt(prompt)
        return FallbackGenerator.generate_from_prompt(prompt)


class FallbackGenerator:
    """Fallback content generator when no LLM is available."""
    
    # Pre-defined content templates
    ENEMY_NAMES = {
        'goblin': ['Grukk the Sneaky', 'Nibblix Shadowfoot', 'Grimtooth'],
        'skeleton': ['Bones the Eternal', 'Rattling Shade', 'Hollow Knight'],
        'orc': ['Groknak Bloodfist', 'Thrak Skullcrusher', 'Urguk Ironhide'],
        'dragon': ['Ignis the Scorcher', 'Frostmaw', 'Shadowscale'],
        'lich': ['Malachar the Undying', 'Nethris Soulbinder', 'Kelvorn'],
        'troll': ['Grumblor', 'Stonehide', 'Mossclaw'],
        'vampire': ['Count Aldric', 'Lady Seraphina', 'Lord Mordecai'],
        'werewolf': ['Fenris Moonstalker', 'Shadowfang', 'Ravenclaw'],
        'demon': ['Azrael the Fallen', 'Infernax', 'Voidbringer'],
        'ghost': ['The Weeping Spirit', 'Phantom of Sorrow', 'Echo of Despair']
    }
    
    MISSION_TEMPLATES = [
        {
            'title': 'The {adjective} {item} of {location}',
            'description': 'Ancient legends speak of a {adjective} {item} hidden within {location}. Many have sought it, but none have returned.',
            'objective': 'Venture into {location} and retrieve the {item}.',
            'reward': '{reward}'
        },
        {
            'title': 'Rescue the {npc} from {enemy}',
            'description': 'The {npc} has been captured by {enemy} and taken to their lair. Time is running out.',
            'objective': 'Find and rescue the {npc} before it\'s too late.',
            'reward': '{reward}'
        },
        {
            'title': 'The {enemy} Menace',
            'description': 'A {enemy} has been terrorizing the nearby villages. The locals are desperate for help.',
            'objective': 'Track down and defeat the {enemy}.',
            'reward': '{reward}'
        }
    ]
    
    ADJECTIVES = ['Lost', 'Cursed', 'Ancient', 'Forgotten', 'Sacred', 'Dark', 'Enchanted']
    ITEMS = ['Artifact', 'Crown', 'Sword', 'Amulet', 'Tome', 'Orb', 'Staff']
    NPCS = ['Village Elder', 'Princess', 'Merchant', 'Wizard', 'Knight', 'Healer']
    
    ABILITIES = {
        'goblin': ['Sneak Attack', 'Poison Dagger', 'Quick Escape'],
        'skeleton': ['Bone Shield', 'Reassemble', 'Haunting Howl'],
        'orc': ['Battle Cry', 'Crushing Blow', 'Enrage'],
        'dragon': ['Fire Breath', 'Wing Gust', 'Terrifying Presence', 'Tail Sweep'],
        'lich': ['Necrotic Touch', 'Soul Drain', 'Summon Undead', 'Death Ray'],
        'troll': ['Regeneration', 'Boulder Throw', 'Ground Slam'],
        'vampire': ['Blood Drain', 'Charm', 'Bat Form', 'Mist Form'],
        'werewolf': ['Savage Bite', 'Pack Howl', 'Lunge'],
        'demon': ['Hellfire', 'Corruption', 'Shadow Step', 'Fear Aura'],
        'ghost': ['Phase', 'Possession', 'Wail of Despair', 'Cold Touch']
    }
    
    WEAKNESSES = {
        'goblin': 'Fire and loud noises',
        'skeleton': 'Holy magic and blunt weapons',
        'orc': 'Strategy and coordination',
        'dragon': 'The underbelly and magical weapons',
        'lich': 'Destroying their phylactery',
        'troll': 'Fire and acid',
        'vampire': 'Sunlight, garlic, and holy symbols',
        'werewolf': 'Silver weapons',
        'demon': 'Holy magic and sacred weapons',
        'ghost': 'Holy magic and resolving their unfinished business'
    }
    
    NARRATIVE_TEMPLATES = [
        "The air grows thick with {atmosphere} as you enter {location}. {detail}",
        "Before you lies {location}, {description}. The silence is {adjective}.",
        "You step cautiously into {location}. {sensory}. Something stirs in the shadows.",
        "The path leads to {location}. {description} {detail}"
    ]
    
    ATMOSPHERES = ['ancient dust', 'an otherworldly chill', 'a sense of dread', 'magical energy']
    SENSORY_DETAILS = [
        'The smell of decay hangs in the air',
        'Distant echoes bounce off the walls',
        'The temperature drops suddenly',
        'Faint whispers seem to come from everywhere'
    ]
    
    @classmethod
    def generate_from_prompt(cls, prompt: str) -> str:
        """Generate content based on prompt analysis."""
        prompt_lower = prompt.lower()
        
        if 'enemy' in prompt_lower or 'monster' in prompt_lower:
            return cls.generate_enemy()
        elif 'mission' in prompt_lower or 'quest' in prompt_lower:
            return cls.generate_mission()
        elif 'narrative' in prompt_lower or 'scene' in prompt_lower:
            return cls.generate_narrative()
        elif 'dialogue' in prompt_lower or 'npc' in prompt_lower:
            return cls.generate_dialogue()
        else:
            return cls.generate_narrative()
    
    @classmethod
    def generate_enemy(cls, enemy_type: Optional[str] = None) -> str:
        """Generate a random enemy."""
        if not enemy_type:
            enemy_type = random.choice(list(ENEMY_TYPES.keys()))
        
        base_stats = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES['goblin'])
        name = random.choice(cls.ENEMY_NAMES.get(enemy_type, ['Unknown Enemy']))
        
        enemy = {
            'name': name,
            'type': enemy_type,
            'hp': base_stats['base_hp'] + random.randint(-5, 10),
            'attack': base_stats['base_attack'] + random.randint(-2, 3),
            'defense': base_stats['base_defense'] + random.randint(-1, 2),
            'abilities': cls.ABILITIES.get(enemy_type, ['Basic Attack'])[:3],
            'weakness': cls.WEAKNESSES.get(enemy_type, 'Unknown'),
            'description': f"A fearsome {enemy_type} that strikes fear into the hearts of adventurers.",
            'lore': f"Legends speak of this {enemy_type}'s dark origins.",
            'tactics': f"This creature prefers to {random.choice(['ambush', 'charge', 'defend', 'flank'])} its prey.",
            'loot': [f"{random.randint(10, 100)} gold", f"{enemy_type.title()} Trophy"]
        }
        
        return json.dumps(enemy, indent=2)
    
    @classmethod
    def generate_mission(cls) -> str:
        """Generate a random mission."""
        template = random.choice(cls.MISSION_TEMPLATES)
        
        mission = {
            'title': template['title'].format(
                adjective=random.choice(cls.ADJECTIVES),
                item=random.choice(cls.ITEMS),
                location=random.choice(LOCATIONS),
                npc=random.choice(cls.NPCS),
                enemy=random.choice(list(ENEMY_TYPES.keys())).title()
            ),
            'description': template['description'].format(
                adjective=random.choice(cls.ADJECTIVES).lower(),
                item=random.choice(cls.ITEMS).lower(),
                location=random.choice(LOCATIONS),
                npc=random.choice(cls.NPCS),
                enemy=random.choice(list(ENEMY_TYPES.keys()))
            ),
            'objective': template['objective'].format(
                item=random.choice(cls.ITEMS),
                location=random.choice(LOCATIONS),
                npc=random.choice(cls.NPCS),
                enemy=random.choice(list(ENEMY_TYPES.keys()))
            ),
            'reward': random.choice(REWARDS),
            'difficulty': random.choice(['Easy', 'Medium', 'Hard']),
            'secondary_objectives': [
                'Find hidden treasure',
                'Rescue any prisoners',
                'Discover the location\'s secrets'
            ],
            'estimated_duration': f"{random.randint(1, 3)} sessions",
            'key_npcs': [random.choice(cls.NPCS)],
            'potential_twists': [
                'The villain is not who they seem',
                'An ally betrays the party',
                'A greater threat emerges'
            ]
        }
        
        return json.dumps(mission, indent=2)
    
    @classmethod
    def generate_narrative(cls, location: Optional[str] = None) -> str:
        """Generate narrative text."""
        if not location:
            location = random.choice(LOCATIONS)
        
        template = random.choice(cls.NARRATIVE_TEMPLATES)
        
        return template.format(
            location=location,
            atmosphere=random.choice(cls.ATMOSPHERES),
            detail=random.choice(cls.SENSORY_DETAILS),
            description=f"a place of {'darkness' if random.random() > 0.5 else 'forgotten glory'}",
            adjective=random.choice(['deafening', 'unsettling', 'complete', 'broken']),
            sensory=random.choice(cls.SENSORY_DETAILS)
        )
    
    @classmethod
    def generate_dialogue(cls, npc_name: Optional[str] = None) -> str:
        """Generate NPC dialogue."""
        if not npc_name:
            npc_name = random.choice(cls.NPCS)
        
        greetings = [
            f"*{npc_name} looks up from their work* Ah, travelers! What brings you to these parts?",
            f"*{npc_name} steps forward cautiously* You're not from around here, are you?",
            f"*{npc_name} smiles warmly* Welcome, friends! How may I assist you?",
            f"*{npc_name} narrows their eyes* State your business, stranger."
        ]
        
        return random.choice(greetings)


# =============================================================================
# MAIN DUNGEON MASTER CLASS
# =============================================================================

class AIDungeonMaster:
    """
    AI Dungeon Master - RPG Adventure Generator
    
    Generates quests, enemies, narrative, dialogues, and ASCII maps
    for tabletop RPG adventures.
    """
    
    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the AI Dungeon Master.
        
        Args:
            provider: LLM provider ('ollama', 'openai', or 'fallback')
            model: Model name to use
            **kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider
        self.model = model
        
        if provider == "ollama":
            self.model = model or "llama3.2"
            self.llm_provider = OllamaProvider(model=self.model, **kwargs)
        elif provider == "openai":
            self.model = model or "gpt-3.5-turbo"
            self.llm_provider = OpenAIProvider(model=self.model, **kwargs)
        else:
            self.llm_provider = None
        
        self.system_prompt = get_prompt_template('system')
        self.generated_content = {
            'missions': [],
            'enemies': [],
            'npcs': [],
            'narratives': [],
            'maps': []
        }
        
        console.print(f"[bold green]🎲 AI Dungeon Master initialized[/bold green]")
        console.print(f"   Provider: {provider}")
        console.print(f"   Model: {self.model or 'fallback'}")
    
    def generate_mission(
        self,
        theme: str = "fantasy",
        player_level: int = 5,
        difficulty: str = "medium",
        context: str = "",
        display: bool = True
    ) -> Mission:
        """
        Generate a new quest/mission.
        
        Args:
            theme: Theme of the adventure
            player_level: Level of the player party
            difficulty: Mission difficulty
            context: Additional context
            display: Whether to display the result
            
        Returns:
            Mission object
        """
        prompt = get_prompt_template('mission').format(
            context=context or "Standard fantasy RPG setting",
            theme=theme,
            level=player_level
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating quest...", total=None)
            
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, system_prompt=self.system_prompt)
            else:
                response = FallbackGenerator.generate_mission()
            
            progress.remove_task(task)
        
        try:
            mission_data = json.loads(response)
        except json.JSONDecodeError:
            mission_data = json.loads(FallbackGenerator.generate_mission())
        
        mission = Mission.from_dict(mission_data)
        self.generated_content['missions'].append(mission)
        
        if display:
            display_mission(mission.to_dict())
        
        return mission
    
    def generate_enemy(
        self,
        enemy_type: Optional[str] = None,
        difficulty: str = "medium",
        environment: str = "dungeon",
        theme: str = "fantasy",
        level: int = 5,
        display: bool = True
    ) -> Enemy:
        """
        Generate a new enemy/monster.
        
        Args:
            enemy_type: Type of enemy (optional)
            difficulty: Encounter difficulty
            environment: Environment where enemy is found
            theme: Theme of the adventure
            level: Target player level
            display: Whether to display the result
            
        Returns:
            Enemy object
        """
        prompt = get_prompt_template('enemy').format(
            difficulty=difficulty,
            environment=environment,
            theme=theme
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Summoning creature...", total=None)
            
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, system_prompt=self.system_prompt)
            else:
                response = FallbackGenerator.generate_enemy(enemy_type)
            
            progress.remove_task(task)
        
        try:
            enemy_data = json.loads(response)
        except json.JSONDecodeError:
            enemy_data = json.loads(FallbackGenerator.generate_enemy(enemy_type))
        
        enemy = Enemy.from_dict(enemy_data)
        enemy = Enemy.from_dict(scale_enemy_to_level(enemy.to_dict(), level))
        
        self.generated_content['enemies'].append(enemy)
        
        if display:
            display_enemy(enemy.to_dict())
        
        return enemy
    
    def generate_narrative(
        self,
        scene_type: str = "exploration",
        location: Optional[str] = None,
        mood: str = "mysterious",
        characters: List[str] = None,
        events: str = "",
        display: bool = True
    ) -> str:
        """
        Generate atmospheric narrative text.
        
        Args:
            scene_type: Type of scene
            location: Location name
            mood: Mood/atmosphere
            characters: Characters present
            events: Recent events
            display: Whether to display the result
            
        Returns:
            Narrative text
        """
        location = location or get_random_location()
        characters = characters or ["the adventuring party"]
        
        prompt = get_prompt_template('narrative').format(
            scene_type=scene_type,
            location=location,
            mood=mood,
            characters=', '.join(characters),
            events=events or "The party has just arrived"
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Weaving narrative...", total=None)
            
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, system_prompt=self.system_prompt)
            else:
                response = FallbackGenerator.generate_narrative(location)
            
            progress.remove_task(task)
        
        self.generated_content['narratives'].append(response)
        
        if display:
            display_narrative(response)
        
        return response
    
    def generate_dialogue(
        self,
        npc_name: str,
        npc_role: str = "villager",
        personality: str = "friendly",
        player_action: str = "greets the NPC",
        context: str = "",
        mood: str = "neutral",
        display: bool = True
    ) -> str:
        """
        Generate NPC dialogue.
        
        Args:
            npc_name: Name of the NPC
            npc_role: Role/occupation of the NPC
            personality: NPC's personality traits
            player_action: What the player said/did
            context: Scene context
            mood: NPC's current mood
            display: Whether to display the result
            
        Returns:
            Dialogue text
        """
        prompt = get_prompt_template('dialogue').format(
            npc_name=npc_name,
            npc_role=npc_role,
            personality=personality,
            player_action=player_action,
            context=context or "A chance encounter",
            mood=mood
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Channeling {npc_name}...", total=None)
            
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, system_prompt=self.system_prompt)
            else:
                response = FallbackGenerator.generate_dialogue(npc_name)
            
            progress.remove_task(task)
        
        if display:
            display_dialogue(npc_name, response, mood)
        
        return response
    
    def generate_dungeon_map(
        self,
        width: int = 40,
        height: int = 20,
        num_rooms: int = 5,
        seed: Optional[int] = None,
        display: bool = True
    ) -> str:
        """
        Generate a procedural dungeon map.
        
        Args:
            width: Map width in characters
            height: Map height in characters
            num_rooms: Number of rooms
            seed: Random seed for reproducibility
            display: Whether to display the result
            
        Returns:
            ASCII map string
        """
        dungeon_map = generate_ascii_map(width, height, num_rooms, seed)
        self.generated_content['maps'].append(dungeon_map)
        
        if display:
            display_map(dungeon_map, "🏰 Dungeon Map")
        
        return dungeon_map
    
    def generate_world_map(
        self,
        width: int = 60,
        height: int = 30,
        seed: Optional[int] = None,
        display: bool = True
    ) -> str:
        """
        Generate a world/overworld map.
        
        Args:
            width: Map width
            height: Map height
            seed: Random seed
            display: Whether to display the result
            
        Returns:
            ASCII world map
        """
        world = generate_world_map(width, height, seed)
        self.generated_content['maps'].append(world)
        
        if display:
            display_map(world, "🌍 World Map")
        
        return world
    
    def describe_map(self, ascii_map: str, display: bool = True) -> str:
        """
        Generate a narrative description of an ASCII map.
        
        Args:
            ascii_map: The ASCII map to describe
            display: Whether to display the result
            
        Returns:
            Map description
        """
        prompt = get_prompt_template('map').format(ascii_map=ascii_map)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing map...", total=None)
            
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, system_prompt=self.system_prompt)
            else:
                response = FallbackGenerator.generate_narrative()
            
            progress.remove_task(task)
        
        if display:
            display_narrative(response)
        
        return response
    
    def create_encounter(
        self,
        difficulty: str = "medium",
        num_enemies: int = 3,
        theme: str = "fantasy",
        display: bool = True
    ) -> Dict:
        """
        Create a complete encounter with multiple enemies.
        
        Args:
            difficulty: Encounter difficulty
            num_enemies: Number of enemies
            theme: Adventure theme
            display: Whether to display the result
            
        Returns:
            Dictionary with encounter details
        """
        enemies = []
        for _ in range(num_enemies):
            enemy = self.generate_enemy(
                difficulty=difficulty,
                theme=theme,
                display=False
            )
            enemies.append(enemy)
        
        # Generate encounter narrative
        narrative = self.generate_narrative(
            scene_type="combat",
            mood="tense",
            display=False
        )
        
        # Generate map
        encounter_map = self.generate_dungeon_map(
            width=30,
            height=15,
            num_rooms=2,
            display=False
        )
        
        encounter = {
            'enemies': [e.to_dict() for e in enemies],
            'narrative': narrative,
            'map': encounter_map,
            'difficulty': difficulty
        }
        
        if display:
            console.print(Panel("[bold red]⚔️ ENCOUNTER![/bold red]"))
            display_narrative(narrative)
            display_map(encounter_map, "Battle Map")
            for enemy in enemies:
                display_enemy(enemy.to_dict())
        
        return encounter
    
    def get_generated_content(self) -> Dict:
        """Get all generated content."""
        return {
            'missions': [m.to_dict() for m in self.generated_content['missions']],
            'enemies': [e.to_dict() for e in self.generated_content['enemies']],
            'narratives': self.generated_content['narratives'],
            'maps': self.generated_content['maps']
        }
    
    def save_campaign(self, filename: str):
        """Save generated content to a JSON file."""
        content = self.get_generated_content()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✅ Campaign saved to {filename}[/green]")
    
    def load_campaign(self, filename: str):
        """Load campaign content from a JSON file."""
        with open(filename, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        self.generated_content['missions'] = [Mission.from_dict(m) for m in content.get('missions', [])]
        self.generated_content['enemies'] = [Enemy.from_dict(e) for e in content.get('enemies', [])]
        self.generated_content['narratives'] = content.get('narratives', [])
        self.generated_content['maps'] = content.get('maps', [])
        
        console.print(f"[green]✅ Campaign loaded from {filename}[/green]")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main demo function."""
    console.print(Panel.fit(
        "[bold magenta]🎲 AI Dungeon Master Demo 🎲[/bold magenta]\n"
        "RPG Adventure Generator",
        border_style="magenta"
    ))
    
    # Initialize with fallback (no LLM needed for demo)
    dm = AIDungeonMaster(provider="fallback")
    
    # Generate a quest
    console.print("\n[bold cyan]📜 Generating Quest...[/bold cyan]")
    mission = dm.generate_mission(theme="dark fantasy", player_level=5)
    
    # Generate an enemy
    console.print("\n[bold cyan]👹 Summoning Enemy...[/bold cyan]")
    enemy = dm.generate_enemy(difficulty="medium", level=5)
    
    # Generate a map
    console.print("\n[bold cyan]🗺️ Creating Dungeon Map...[/bold cyan]")
    dungeon = dm.generate_dungeon_map(width=40, height=15, num_rooms=4, seed=42)
    
    # Generate narrative
    console.print("\n[bold cyan]📖 Writing Narrative...[/bold cyan]")
    narrative = dm.generate_narrative(
        scene_type="discovery",
        mood="mysterious"
    )
    
    console.print("\n[bold green]✅ Demo complete![/bold green]")


if __name__ == "__main__":
    main()
