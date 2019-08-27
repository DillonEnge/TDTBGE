import time
import sys
import logging
import random
import csv
import inspect

import termios, tty, os
 
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
 
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

class World:
    class CHARACTER:
        END_WALL = " ||\n"
        SPACE = " -"
        WALL = "||"   
        BORDER = " ="
    
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

    def add_entity(self, entity):
        self.entities.append(entity)
        self.update_sprite_cache(entity)

    def add_controller(self, controller, key):
        if self.debug:
            print(f'adding controller to world: {self.title}...')

        self.controllers[key] = controller

    def update_sprite_cache(self, entity):
        for state in entity.states:
            for key in state:
                self.sprite_cache.append(state[key])

    def generate_world_array(self):
        world_array = [[-1 for x in range(self.worldSize[1])] for y in range(self.worldSize[0])]

        for entity in self.entities:
            world_array[entity.position[0]][entity.position[1]] = entity.determine_state(self.sprite_cache)

        self.world_array = world_array

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

    def render(self, waiting=False):
        self.update()
        print(self.world_display)
        self.render_cycle += 1
        if not waiting:
            self.listen()

    def wait(self, frames):
        for _ in range(frames):
            self.render(True)

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


class Entity:
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

    def defaultFactory(self):
        return ''

    def determine_state(self, sprite_cache):
        if self.determine_state_method != None:
            for state in self.states:
                for key in state.keys():
                    if key == self.determine_state_method(self):
                        return sprite_cache.index(state[key])
        else:
            return sprite_cache.index(self.states[0]['default'])

    def get_x_pos(self):
        return self.position[1]

    def get_y_pos(self):
        return self.position[0]

    def add_controller(self, controller, key):
        if self.debug:
            print(f'adding controller to entity {self.name}...')
        source = inspect.getsource(controller)
        new_line_char = '\n'

        exec(f"def {key}(entity, world): {source[source.index(new_line_char):]}")

        self.controllers[key] = locals()[key]
    
    def modify_pos(self, x_pos = 0, y_pos = 0):
        self.position[1] += x_pos
        self.position[0] -= y_pos

    def set_pos(self, x_pos, y_pos):
        self.position[1] = x_pos
        self.position[0] = y_pos

    def is_touching(self, entity):
        for x in range(-1, 2):
                for y in range(-1, 2):
                    if self.position == [entity.position[0] + x, entity.position[1] + y]:
                        return True
        return False

    def destroy(self):
        self.alive = False

    def update(self):
        if self.debug:
            print(f'updating entity {self.name}...')
        logging.info(f'updating entity {self.name}...')
        if self.debug:
            print(self.attributes)
