"""
===========================================================
 File:        game
 Author:      bloodandeath
 Created:     10/17/2025 10:23 PM
 Description: The main game for now.

 Version:     1.0
 License:     MIT License
===========================================================
"""

import math
import random

# TODO: Add documentation to everything
# TODO: Split classes into separate modules (Files)
# TODO: Better item handling for the future
# TODO: Figure out how to handle health items (Should we give/take the entities current health if they equip/drop it)

# -------- Items --------
class Item:
    def __init__(self, name: str, desc: str, kind: str,
                 bonus_hp: int = 0, bonus_damage: int = 0, bonus_armor: int = 0,
                 bonus_dodge: float = 0, bonus_crit: float = 0,
                 heal: int = 0):
        self.name = name
        self.desc = desc
        self.kind = kind
        self.bonus_hp = bonus_hp
        self.bonus_damage = bonus_damage
        self.bonus_armor = bonus_armor
        self.bonus_dodge = bonus_dodge
        self.bonus_crit = bonus_crit
        self.heal = heal

    def use(self, target: "Entity"):
        match self.kind:
            case "potion":
                before = target.hp
                target.hp = min(target.max_hp, target.hp + self.heal)
                print(f"{target.name} drinks {self.name} and heals {target.hp - before}. "
                      f"({target.hp}/{target.max_hp})")
                return "consume"

            case "mod":
                print(f"{self.name} grants passive bonuses while carried.")
                return "keep"

            case "key":
                print(f"{self.name}: utility item.")
                return "keep"

            case _:
                print(f"{self.name} does nothing obvious.")
                return "keep"


# -------- Entities --------
class Entity:

    def __init__(self,
                 name: str, desc: str,
                 base_max_hp: int, base_damage: int, base_armor: int = 0,
                 base_dodge: float = 0, base_crit: float = 0,
                 hostile: bool = False):
        self.name = name
        self.desc = desc
        self._base_max_hp = max(1, base_max_hp)
        self._base_damage = max(0, base_damage)
        self._base_armor = max(0, base_armor)
        self._base_dodge = max(0.05, base_dodge)
        self._base_crit = max(0.05, base_crit)
        self.hp = self._base_max_hp
        self.inventory: list[Item] = []
        self.hostile = hostile

    # region Properties
    @property
    def max_hp(self) -> int:
        return self._base_max_hp + sum(item.bonus_hp for item in self.inventory if item.kind == "mod")

    @property
    def damage(self) -> int:
        return self._base_damage + sum(item.bonus_damage for item in self.inventory if item.kind == "mod")

    @property
    def armor(self) -> int:
        return self._base_armor + sum(item.bonus_armor for item in self.inventory if item.kind == "mod")

    @property
    def dodge(self) -> float:
        return round(self._base_dodge + sum(item.bonus_dodge for item in self.inventory if item.kind == "mod"), 2)

    @property
    def crit(self) -> float:
        return round(self._base_crit + sum(item.bonus_crit for item in self.inventory if item.kind == "mod"), 2)

    @property
    def alive(self) -> bool:
        return self.hp > 0
    # endregion

    def _reconcile_hp(self):
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def take_damage(self, amount: int, tag: str) -> bool:
        """
        Damages the entity for said amount of damage (Before modifiers)

        :param int amount: The amount of damage
        :param str tag: The tag of the damage (' [CRIT]' or '')
        :return: True if the damage was successful, False otherwise"""
        amount = math.ceil(amount * amount / (amount + self.armor))

        if random.random() < self.dodge:
            return False

        self.hp -= amount
        print(f"{self.name} takes {amount} damage{tag}. ({self.hp}/{self.max_hp})")

        if self.hp == 0:
            print(f"{self.name} has died.")
        return True

    def attack(self, other: "Entity"):
        if not self.alive:
            return

        dealt = max(1, self.damage)

        tag = ''
        if random.random() < self.crit:
            dealt = math.ceil(dealt * 1.5)
            tag = ' [CRIT]'

        print(f"{self.name} attacks {other.name}!")
        if not other.take_damage(dealt, tag):
            print(f"{other.name} dodges {self.name}!")


# -------- Rooms --------
def opposite_of(d: str) -> str | None:
    return {"north": "south", "south": "north",
            "east": "west", "west": "east",
            "up": "down", "down": "up"}.get(d)


class Exit:
    def __init__(self, target: "Room", locked: bool = False,
                 requires_item_name: str | None = None):
        self.target = target
        self.locked = locked
        self.requires_item_name = requires_item_name


class Room:
    def __init__(self, name: str, desc: str, dark: bool = False):
        self.name = name
        self.desc = desc
        self.dark = dark
        self.exits: dict[str, Exit] = {}
        self.items: list[Item] = []
        self.entities: list[Entity] = []

    def link(self,
             direction: str, other: "Room", bidirectional: bool = True,
             locked: bool = False, requires_item_name: str | None = None):
        d = direction.lower()
        self.exits[d] = Exit(other, locked, requires_item_name)
        if bidirectional:
            other.exits[opposite_of(d)] = Exit(self)


# -------- World setup --------
def build_items():
    return {

        # region Modifiers
        "Iron Helmet": Item("Iron Helmet", "A simple helm.", "mod", bonus_armor=5),
        "Wolf Pelt": Item("Wolf Pelt", "Warm and tough.", "mod", bonus_hp=5),
        "Short Sword": Item("Short Sword", "A rusty old blade", "mod", bonus_damage=3),
        "Sharpening Stone": Item("Sharpening Stone", "It's better than your hands.", "mod", bonus_damage=1),
        "Enchiridion": Item("Enchiridion", "This book whispers power...", "mod", bonus_hp=5, bonus_damage=5, bonus_armor=5),
        "Bottled Lightning": Item("Bottled Lightning", "Gives you a spark of life.", "mod", bonus_crit=0.10),
        "Old Coin": Item("Old Coin", "You feel a little luckier.", "mod", bonus_dodge=0.10),
        # endregion

        # region Potions
        "Small Potion": Item("Small Potion", "Heals 5 HP.", "potion", heal=5),
        "Medium Potion": Item("Medium Potion", "Heals 10 HP.", "potion", heal=10),
        "Large Potion": Item("Large Potion", "Heals 20 HP.", "potion", heal=20),
        # endregion

        # region Utility
        "Brass Key": Item("Brass Key", "Opens a brass-locked door.", "key"),
        "Lantern": Item("Lantern", "An oil lantern. Try 'lantern on/off'.", "key"),
        "Map": Item("Map", "Shows a map of the castle when used.", "key"),
        # endregion
    }


def build_world():
    items = build_items()

    # region Rooms
    receptacle = Room("Receptacle", "A small stone chamber where your journey begins.")     # Start
    library = Room("Library", "Shelves of moldy tomes.")
    hall = Room("Hall", "A dusty corridor with cobwebs.")
    great_hall = Room("Great Hall", "A grand room with a shattered chandelier.")
    bedroom = Room("Bedroom", "A faded canopy bed and cracked mirror.")
    throne = Room("Throne Room", "A cracked throne sits upon a dais.")                      # Boss room
    armory = Room("Armory", "Racks of rusted weapons.")
    courtyard = Room("Courtyard", "An overgrown courtyard open to the sky.")
    cellar = Room("Cellar", "Damp and cold; the air smells of mildew.")
    catacomb = Room("Catacombs", "Narrow, twisting passages.", dark=True)
    crypt = Room("Crypt", "Ancient tombs line the walls.", dark=True)
    # endregion

    # region Links
    receptacle.link("north", library)
    library.link("east", hall)
    hall.link("north", great_hall)
    great_hall.link("west", bedroom)
    great_hall.link("north", throne, bidirectional=False, locked=True, requires_item_name="Brass Key")
    hall.link("east", armory)
    hall.link("south", courtyard)
    courtyard.link("south", cellar)
    cellar.link("down", catacomb)
    catacomb.link("east", crypt)
    # endregion

    # region Monsters
    slime = Entity("Slime", "A wobbling mass of goo. What's keeping this thing alive?", 8, 1, hostile=True)
    skeleton = Entity("Skeleton", "Clattering bones with a rusty sword.", 10, 1, hostile=True)
    wizard = Entity("Wizard", "He's floating there, menacingly...", 9, 1, base_dodge=0.2, hostile=True)
    zombie = Entity("Zombie", "It shambles forward hungrily.", 10, 2, hostile=True)
    lich = Entity("The Lich", "Ancient and terrifying.", 30, 8, base_armor=6, hostile=True)
    # endregion

    # region Items
    '''
    Valid items:
    "Iron Helmet" .
    "Wolf Pelt" .
    "Short Sword" .
    "Sharpening Stone" .
    "Enchiridion" .
    "Bottled Lightning" .
    "Old Coin" .
    "Small Potion" ..
    "Brass Key" 
    "Lantern"  .
    "Map" .
    '''
    #                                                           - The below items are dropped by creatures on that level
    #receptacle.items += [items["Small Potion"]]#               -
    library.items += [items["Map"]]#                            - Bottled Lightning
    # hall                                                      -
    # great_hall                                                -
    bedroom.items += [items["Lantern"], items["Medium Potion"]]# -
    # throne.items += [items["Small Potion']]                   -
    armory.items += [items["Sharpening Stone"]]#                     - Iron Helmet, Old Coin
    courtyard.items += [items["Small Potion"]]#                 -
    # cellar                                                    -
    # catacomb                                                  - Sharpening Stone, Wolf Pelt
    # crypt                                                     - Enchiridion, Brass Key

    slime.inventory += [items["Bottled Lightning"]]
    skeleton.inventory += [items["Short Sword"], items["Wolf Pelt"], items["Brass Key"]]  # Get it? Skeleton key!
    wizard.inventory += [items["Enchiridion"], items["Large Potion"]]
    zombie.inventory += [items["Iron Helmet"], items["Old Coin"]]

    library.entities.append(slime)
    armory.entities.append(zombie)
    catacomb.entities.append(skeleton)
    crypt.entities.append(wizard)
    throne.entities.append(lich)
    # endregion

    # region Player
    hero = Entity("Hero", "A brave adventurer.", 16, 2, base_armor=1)
    hero.inventory.append(items["Small Potion"])
    # endregion

    return receptacle, hero


# -------- Game --------
HELP = """\
Commands:
  help                 Show this help
  go <dir>             Move (north/south/east/west/up/down/back)
  room                 Show current room
  look                 Describe surroundings
  take <item>          Pick up item (danger if enemies nearby)
  drop <item>          Drop item
  inv                  Show inventory
  use <item>           Use consumable item
  attack <name>        Attack enemy
  lantern <on|off>     Toggle lantern (if you have one)
  map                  Show map (if you have one)
  exit                 Quit
"""

WELCOME = """\
                    Welcome to The Lich by Corbin Breton

You wake up, you must have blacked out... You're feeling very numbingly cold.
     As you stammer onto your feet, you begin remembering where you are.
      'Icecrown' you think to yourself... 'I must be the only survivor'
          Your party managed to push through the undead horde, your
                fate has been sealed, you must pursue The Lich.
                    'The Throne Room can't be too far...'
                         (Type 'help' for commands.)
"""

MAP = """\
                 [Throne Room]
                       ^
                       |  (locked; Brass Key opens)
    [Bedroom] --- [Great Hall]
                       |
    [Library] ----- [Hall] --- [Armory]
        |              |
    [Receptacle*]      |
                  [Courtyard]
                       |
                   [Cellar]
                       |  (Down)
                       v
                  [Catacombs][D] --- [Crypt][D]

(* = Start, [D] = Dark room)
"""

class Game:
    def __init__(self):
        self.current_room, self.player = build_world()
        self.lantern_lit = False
        self.escape_dir: str | None = None
        self.combat_lock = False
        self.victory = False
        self.action_counter = 0

    # region Utility Functions
    def _player_has(self, name: str) -> bool:
        return any(item.name.lower() == name.lower() for item in self.player.inventory)

    def _hostiles(self) -> list[Entity]:
        return [e for e in self.current_room.entities if e.hostile and e.alive]

    def _enter_room_effects(self, entered_dir: str):
        self.escape_dir = opposite_of(entered_dir)
        hostiles = self._hostiles()
        if hostiles:
            self.combat_lock = True
            names = ", ".join(e.name for e in hostiles)
            print(f"A monster blocks your path!")
            for e in hostiles:
                print(f"  - {e.name}: {e.desc}")

    # endregion

    # region Commands
    def move(self, direction: str):

        direction = direction.lower()

        # Darkness check
        if self.current_room.dark and not self.lantern_lit and direction != self.escape_dir:
            print("It's pitch black. You can only feel your way back (try 'go back').")
            return

        if direction == "back":
            if not self.escape_dir:
                print("You're not sure which way 'back' is.")
                return
            direction = self.escape_dir

        if direction not in self.current_room.exits:
            print("You cannot move that direction.\n")
            return

        # Combat locked gives the player a 20% fleeing chance
        if self.combat_lock and random.random() > 0.2:
            foe = next(iter(self._hostiles()), None)
            print("You try to flee, but the enemy blocks your way!")
            if foe:
                foe.attack(self.player)
            return

        exit_obj = self.current_room.exits[direction]
        if exit_obj.locked:
            needed = exit_obj.requires_item_name
            if needed and self._player_has(needed):
                print(f"You use the {needed}. The lock clicks open.")
                exit_obj.locked = False
            else:
                print("The way is locked.")
                return

        self.current_room = exit_obj.target
        print(f"You move {direction} into the {self.current_room.name}.\n")
        self.combat_lock = False
        self.action_counter += 1
        self._enter_room_effects(direction)

    def look(self):
        room = self.current_room
        if room.dark and not self.lantern_lit:
            print(f"{room.name}: It's pitch black. You can only feel a wall behind you.\n")
            return

        # Display the players current position and stats
        print(f"{room.name}: {room.desc}")
        print(
f"""\
Your stats → HP {self.player.hp}/{self.player.max_hp}  DMG {self.player.damage}  ARM {self.player.armor}
             DODGE {self.player.dodge * 100}%  CRIT {self.player.crit * 100}%""")

        # Display all the available directions the player can travel
        for direction, exit_obj in room.exits.items():
            status = " [locked]" if exit_obj.locked else ""
            print(f"  Exit {direction.capitalize()} -> {exit_obj.target.name}{status}")

        if room.items:
            print("\nItems here:")
            for item in room.items:
                print(f"  - {item.name}: {item.desc}")

        if room.entities:
            print("\nYou see:")
            for e in room.entities:
                tag = " (dead)" if not e.alive else ""
                print(f"  - {e.name}{tag} [HP {e.hp}/{e.max_hp}, DMG {e.damage}, ARM {e.armor}]")
        print()

    def take(self, item_name: str):
        if not item_name:
            print("Take what?")
            return

        for item in list(self.current_room.items):
            if item.name.lower() == item_name.lower():
                self.player.inventory.append(item)
                self.current_room.items.remove(item)
                self.player._reconcile_hp()
                print(f"You pick up the {item.name}.")
                self.action_counter += 1
                if self._hostiles():
                    print("While you fumble with the item, a foe strikes!")
                    self._hostiles()[0].attack(self.player)
                return

        print(f"No item named '{item_name}' here.")

    def drop(self, item_name: str):
        for item in list(self.player.inventory):
            if item.name.lower() == item_name.lower():
                if item.name.lower() == "lantern" and self.lantern_lit:
                    self.lantern_lit = False
                    print("You set your lantern down; its flame gutters out.")
                self.player.inventory.remove(item)
                self.current_room.items.append(item)
                self.player._reconcile_hp()
                print(f"You drop the {item.name}.")
                return
        print(f"You don't have '{item_name}'.")

    def inv(self):
        if not self.player.inventory:
            print("Your inventory is empty.")
            return

        print("Inventory:")
        for item in self.player.inventory:
            tag = ""
            if item.kind == "mod":
                bonuses = []
                if item.bonus_hp: bonuses.append(f"+{item.bonus_hp} HP")
                if item.bonus_damage: bonuses.append(f"+{item.bonus_damage} DMG")
                if item.bonus_armor: bonuses.append(f"+{item.bonus_armor} ARM")
                if item.bonus_crit: bonuses.append(f"+{item.bonus_crit * 100}% CRIT")
                if item.bonus_dodge: bonuses.append(f"+{item.bonus_dodge * 100}% DODGE")
                tag = " (" + ", ".join(bonuses) + ")" if bonuses else ""
            if item.name.lower() == "lantern":
                tag += " [ON]" if self.lantern_lit else " [OFF]"
            print(f"  - {item.name}{tag}: {item.desc}")
        print()

    def use(self, item_name: str):
        for item in list(self.player.inventory):
            if item.name.lower() == item_name.lower():
                if item.name.lower() == "lantern":
                    print("Try: lantern on  |  lantern off")
                    return
                result = item.use(self.player)

                if result == "consume":
                    self.player.inventory.remove(item)
                    self.player._reconcile_hp()
                    self.action_counter += 1
                return
        print(f"You don't have '{item_name}'.")

    def lantern_cmd(self, state: str):
        if not self._player_has("Lantern"):
            print("You don't have a lantern.")
            return
        match state.lower():
            case "on":
                if self.lantern_lit:
                    print("Your lantern is already on.")
                else:
                    self.lantern_lit = True
                    print("You light your lantern.")
            case "off":
                if not self.lantern_lit:
                    print("Your lantern is already off.")
                else:
                    self.lantern_lit = False
                    print("You extinguish your lantern.")
            case _:
                print("Usage: lantern <on|off>")

    def show_map(self):
        if not self._player_has("Map"):
            print("You don't have a map.")
            return
        print(MAP)

    def attack(self, target_name: str):
        target = next((e for e in self.current_room.entities if e.name.lower() == target_name.lower()), None)
        if not target:
            print(f"No one named '{target_name}' is here.")
            return
        if not target.alive:
            print(f"{target.name} is already dead.")
            return

        self.player.attack(target)
        self.action_counter += 1
        if not target.alive and target.inventory:
            print(f"{target.name} drops:")
            while target.inventory:
                dropped = target.inventory.pop()
                print(f"  - {dropped.name}")
                self.current_room.items.append(dropped)
        elif not target.alive and target.name == "The Lich":
            print("\nYou have defeated The Lich. The castle grows silent.\n")
            self.victory = True
        elif target.alive and target.hostile:
            target.attack(self.player)

        self.combat_lock = bool(self._hostiles())

    # endregion

    def run(self):
        print(WELCOME)

        '''The entire loop just parses the next command, and then interacts with the world dynamically.
            Once the Win or Loose condition is met, the loop terminates, and the game is over'''
        while self.player.alive and not self.victory:
            raw = input("> ").strip()
            if not raw:
                continue
            parts = raw.split()
            cmd = parts[0].lower()
            arg = " ".join(parts[1:])
            match cmd:
                case "exit":
                    break
                case "help":
                    print(HELP)
                case "go":
                    self.move(arg)
                case "room":
                    print(f"Current room: {self.current_room.name}\n")
                case "look":
                    self.look()
                case "take":
                    self.take(arg)
                case "drop":
                    self.drop(arg)
                case "inv":
                    self.inv()
                case "use":
                    self.use(arg)
                case "attack":
                    self.attack(arg)
                case "lantern":
                    self.lantern_cmd(arg)
                case "map":
                    self.show_map()
                case _:
                    print("Unknown command. Type 'help' for options.")

        '''Here, the player will be presented with the victory or death message (unless they just type exit)
            Next some basic stats are displayed about that run,
            and the player is given an option to play again'''
        if self.victory:
            print("You have WON.")
        elif not self.player.alive:
            print("You have fallen. The Lich's laughter echoes...")
        print(f"Total actions: {self.action_counter}")
        self.inv()
        print("Play again? [Y/N]")
        play_again = input("> ").strip().lower()
        match play_again:
            case "y" | "yes":
                self.__init__()
                self.run()
            case "n" | "no":
                print("Thank you for playing.")
                exit(0)


if __name__ == "__main__":
    Game().run()
