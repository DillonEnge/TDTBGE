import time
import sys
import logging
import random
import csv
import inspect
import termios, tty, os
 
# getch method used to process key inputs immediately from the user without need to press the enter key to submit
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
 
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# World class used for world generation, rendering, and manipulation
class World:
    # Generic character constants class to be used in world framing
    class CHARACTER:
        END_WALL = " ||\n"
        SPACE = " -"
        WALL = "||"   
        BORDER = " ="
    
    # Initializes the world with specified default properties
    def __init__(self, title, worldSize, debug=False):
        logging.basicConfig(filename='world.log',level=logging.DEBUG)
        logging.info("Initializing world...")
        self.debug = debug
        if self.debug:
            print("Initializing world...")
        self.title = title
        self.controllers = {}
        self.entities = []
        self.sprite_cache = []
        self.worldSize = worldSize
        self.generate_world_array()
        self.generate_world_display()
        self.render_cycle = 0

    # Adds a passed entity to the world
    def add_entity(self, entity):
        self.entities.append(entity)
        self.update_sprite_cache(entity)

    # Adds a controller to the world
    # Takes the controller function and the key string that is pressed to activate that function
    def add_controller(self, controller, key):
        if self.debug:
            print(f'adding controller to world: {self.title}...')

        self.controllers[key] = controller

    # Updates the sprite cache, used for adding new entity visual states to the world for later use
    def update_sprite_cache(self, entity):
        for state in entity.states:
            for key in state:
                self.sprite_cache.append(state[key])

    # Generates non-visual world array map used to derive the world display from
    def generate_world_array(self):
        world_array = [[-1 for x in range(self.worldSize[1])] for y in range(self.worldSize[0])]

        for entity in self.entities:
            world_array[entity.position[0]][entity.position[1]] = entity.determine_state(self.sprite_cache)

        self.world_array = world_array

    # Generates visual world display to be printed to the screen derived from the generated world array
    def generate_world_display(self):
        world_display = ""

        for x in self.world_array:
            world_display += self.CHARACTER.WALL
            
            for y in x:
                world_display += self.CHARACTER.BORDER.lstrip() + self.CHARACTER.BORDER.lstrip()
            
            world_display += self.CHARACTER.BORDER.lstrip() + self.CHARACTER.END_WALL.lstrip()
            break

        for x in self.world_array:
            world_display += self.CHARACTER.WALL

            for y in x:
                if y == -1:
                    world_display += self.CHARACTER.SPACE
                else:
                    world_display += f' {self.sprite_cache[y]}'

            world_display += self.CHARACTER.END_WALL

        for x in self.world_array:
            world_display += self.CHARACTER.WALL
            
            for y in x:
                world_display += self.CHARACTER.BORDER.lstrip() + self.CHARACTER.BORDER.lstrip()
            
            world_display += self.CHARACTER.BORDER.lstrip() + self.CHARACTER.END_WALL.lstrip()
            break

        world_display = world_display[:world_display.rfind("\n")]
        self.world_display = world_display

    # Renders the world by updating the world then printing the display and waiting for user key input
    def render(self, waiting=False):
        self.update()
        print(self.world_display)
        self.render_cycle += 1
        if not waiting:
            self.listen()

    # Renders a specified amount of frames without waiting for user key input
    def wait(self, frames):
        for _ in range(frames):
            self.render(True)

    # Listens for keyboard inputs and processes the inputs for any world/entity controller that shares that key name
    def listen(self):
        key = getch()
        time.sleep(0)

        logging.info('key pressed: ' + key)
        if self.debug:
            print('key pressed: ' + key)

        if key == '\\':
            sys.exit(0)

        if key in self.controllers:
            self.controllers[key](self)
        
        for entity in self.entities:
            if key in entity.controllers:
                entity.controllers[key](entity, self)

    # Updates the world, used for updating entities and purging dead entities, as well as calculating and drawing the next render frame
    def update(self):
        logging.info(f'Updating world {self.title}...')
        if self.debug:
            print(f'Updating world {self.title}...')
        purged_entities = []
        for entity in self.entities:
                if entity.alive:
                    entity.update()
                else:
                    purged_entities.append(entity)
        for entity in purged_entities:
            self.entities.pop(self.entities.index(entity))
        self.generate_world_array()
        self.generate_world_display()

# Entity class used for entity creation, processing, and manipulation
class Entity:
    # Initializes entity with initial defaults
    def __init__(self, name, states, initialPosition, determine_state_method=None, debug=False, **kwargs):
        self.alive = True
        self.attributes = {}
        for key, value in kwargs.items():
            self.attributes[key] = value
        self.debug = debug
        self.determine_state_method = determine_state_method
        self.name = name
        self.position = [initialPosition[0], initialPosition[1]]
        self.states = states
        self.controllers = {}
    
    # Determines which visual state character to return from the passed sprite_cache
    def determine_state(self, sprite_cache):
        if self.determine_state_method != None:
            for state in self.states:
                for key in state.keys():
                    if key == self.determine_state_method(self):
                        return sprite_cache.index(state[key])
        else:
            return sprite_cache.index(self.states[0]['default'])

    # Gets the entities x position
    def get_x_pos(self):
        return self.position[1]

    # Gets the entities y position
    def get_y_pos(self):
        return self.position[0]

    # Adds a controller to the entity
    # Takes the controller function and the key string that is pressed to activate that function
    def add_controller(self, controller, key):
        if self.debug:
            print(f'adding controller to entity {self.name}...')
        source = inspect.getsource(controller)
        new_line_char = '\n'

        exec(f"def {key}(entity, world): {source[source.index(new_line_char):]}")

        self.controllers[key] = locals()[key]
    
    # Incrementally modifies the current entity position
    def modify_pos(self, x_pos = 0, y_pos = 0):
        self.position[1] += x_pos
        self.position[0] -= y_pos

    # Sets the entity position to a new position
    def set_pos(self, x_pos, y_pos):
        self.position[1] = x_pos
        self.position[0] = y_pos

    # Determines if self is touching the passed entity
    def is_touching(self, entity):
        for x in range(-1, 2):
                for y in range(-1, 2):
                    if self.position == [entity.position[0] + x, entity.position[1] + y]:
                        return True
        return False

    # Destroys entity
    def destroy(self):
        self.alive = False

    # Updates entity, (used for debug only right now, may be assignable a function callback in the future)
    def update(self):
        if self.debug:
            print(f'updating entity {self.name}...')
        logging.info(f'updating entity {self.name}...')
        if self.debug:
            print(self.attributes)
