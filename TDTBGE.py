import time
import sys
import logging
import random
import csv
import inspect
import termios, tty, os
import simpleaudio
from os import system, name
from colorama import Fore, Style



# World class used for world generation, rendering, and manipulation
class World:
    # Initializes the world with specified default properties
    def __init__(self, title, world_size, window_size, window_pos=[0,0], debug=False, bgm='', **kwargs):
        logging.basicConfig(filename='world.log',level=logging.DEBUG)
        logging.info("Initializing world...")
        self.attributes = {}
        for key, value in kwargs.items():
            self.attributes[key] = value
        self.debug = debug
        if self.debug:
            print("Initializing world...")
        self.title = title
        self.controllers = {}
        self.entities = []
        self.sprite_cache = []
        self.world_size = world_size
        self.window_size = window_size
        self.window_pos = window_pos
        self.bgm_filename = bgm
        self.render_cycle = 0

    # Adds a passed entity to the world
    def add_entity(self, entity):
        self.entities.append(entity)
        self.update_sprite_cache(entity)

    # Incrementally modifies the current entity position
    def modify_window_pos(self, x_pos = 0, y_pos = 0):
        self.window_pos[1] += x_pos
        self.window_pos[0] -= y_pos

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
        world_array = [[-1 for x in range(self.world_size[1])] for y in range(self.world_size[0])]

        for entity in self.entities:
            if not entity.abstract:
                for arr in entity.grouping_map:
                    if len(arr) == 3:
                        for nested_arr in arr[2].grouping_map:
                            x_pos = entity.position[1] + arr[1] + nested_arr[1]
                            y_pos = entity.position[0] + arr[0] + nested_arr[0]
                            world_array[y_pos][x_pos] = arr[2].determine_state(self, pos=[entity.position[0] + arr[0], entity.position[1] + arr[1]])
                    else:
                        world_array[entity.position[0] + arr[0]][entity.position[1] + arr[1]] = entity.determine_state(self)

        self.world_array = world_array

    # Generates visual world display to be printed to the screen derived from the generated world array
    def generate_world_display(self):
        world_display = ""

        for x in range(self.window_size[0]):
            world_display += Lib.CHARACTER.WALL
            for y in range(self.window_size[1]):
                world_display += Lib.CHARACTER.BORDER.lstrip() + Lib.CHARACTER.BORDER.lstrip()

            world_display += Lib.CHARACTER.BORDER.lstrip() + Lib.CHARACTER.END_WALL.lstrip()
            break

        for x in range(self.world_size[0]):
            if x >= self.window_pos[0] and x < self.window_pos[0] + self.window_size[0]:
                world_display += Lib.CHARACTER.WALL

                for y in range(self.world_size[1]):
                    if y >= self.window_pos[1] and y < self.window_pos[1] + self.window_size[1]:
                        if self.world_array[x][y] == -1:
                            world_display += f' {Lib.CHARACTER.SPACE}'
                        else:
                            world_display += f' {self.sprite_cache[self.world_array[x][y]]}'

                world_display += Lib.CHARACTER.END_WALL


        for x in range(self.window_size[0]):
            world_display += Lib.CHARACTER.WALL

            for y in range(self.window_size[1]):
                world_display += Lib.CHARACTER.BORDER.lstrip() + Lib.CHARACTER.BORDER.lstrip()

            world_display += Lib.CHARACTER.BORDER.lstrip() + Lib.CHARACTER.END_WALL.lstrip()
            break

        world_display = world_display[:world_display.rfind("\n")]
        self.world_display = world_display

    # Renders the world by updating the world then printing the display and waiting for user key input
    def render(self, waiting=False):
        self.update()
        if not self.debug:
            Lib.clear()
        print(self.world_display)
        self.render_cycle += 1
        if not waiting:
            self.listen()


    # Plays a sound from the given .wav filename
    def play_sound(self, filename):
        wave_obj = simpleaudio.WaveObject.from_wave_file(filename)
        wave_obj.play()

    # Plays a bgm track from the given .wav filename
    def play_bgm(self, filename):
        self.bgm_initialized = True
        wave_obj = simpleaudio.WaveObject.from_wave_file(filename)
        self.play_obj = wave_obj.play()

    # Renders a specified amount of frames without waiting for user key input
    def wait(self, frames):
        for _ in range(frames):
            self.render(True)

    # Listens for keyboard inputs and processes the inputs for any world/entity controller that shares that key name
    def listen(self):
        key = Lib.getch()
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
            print(f'World {self.title} is on render cycle {self.render_cycle}')
        if self.bgm_filename != '':
            if not hasattr(self, 'play_obj') or not self.play_obj.is_playing():
                self.play_bgm(self.bgm_filename)
        purged_entities = []
        for entity in self.entities:
                if entity.alive:
                    entity.update()
                else:
                    purged_entities.append(entity)
        for entity in purged_entities:
            for nested_entity in self.entities:
                purged_item = []
                for x in range(len(nested_entity.grouping_map)):
                    if entity in nested_entity.grouping_map[x]:
                        purged_item.append(x)
                for item in purged_item:
                    nested_entity.grouping_map.pop(item)
            self.entities.pop(self.entities.index(entity))
        self.generate_world_array()
        self.generate_world_display()

# Entity class used for entity creation, processing, and manipulation
class Entity:
    # Initializes entity with initial defaults
    def __init__(self, name, states, initialPosition=None, abstract=False, grouping_map=[ [0,0] ], collision_list=[], determine_state_method=None, debug=False, **kwargs):
        self.alive = True
        self.abstract = abstract
        self.collision_list = collision_list
        self.name = name
        self.debug = debug
        self.floating_methods={}
        self.interperate_grouping_map(grouping_map)
        self.states = states
        self.add_determine_state_method(determine_state_method)
        if not abstract:
            self.position = [initialPosition[0], initialPosition[1]]
        self.controllers = {}
        self.attributes = {}
        for key, value in kwargs.items():
            self.attributes[key] = value

    def interperate_grouping_map(self, grouping_map):
        new_map = []
        for item in grouping_map:
            if len(item) == 5:
                if item[4] == 'square_fill':
                    for y2 in range(item[0],item[2]):
                        for x2 in range(item[1],item[3]):
                            new_map.append([y2,x2])
                if item[4] == 'square_no_fill':
                    for y2 in range(item[0],item[2] + 1):
                        new_map.append([y2,0])
                        new_map.append([y2,item[3]])
                        for x2 in range(item[1],item[3]):
                            new_map.append([0,x2])
                            new_map.append([item[2],x2])
            else:
                new_map.append(item)
        self.grouping_map = new_map

    # Determines which visual state character to return from the passed sprite_cache
    def determine_state(self, world, pos=None):
        if self.abstract:
            self.position = pos
        if self.determine_state_method != None:
            for state in self.states:
                for key in state.keys():
                    if key == self.determine_state_method(self, world):
                        return world.sprite_cache.index(state[key])
        else:
            return world.sprite_cache.index(self.states[0]['default'])

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
        function_name = f'{self.name}_controller_{key}'
        exec(f"def {function_name}(entity, world): {source[source.index(new_line_char):]}")

        self.controllers[key] = locals()[function_name]

    def add_floating_method(self, floating_method):
        if self.debug:
            print(f'adding floating method to entity {self.name}...')

        source = inspect.getsource(floating_method)
        new_line_char = '\n'
        function_name = f'{floating_method.__name__}'
        exec(f"def {function_name}{source[source.index('('): source.index(')')]}): {source[source.index(new_line_char):]}")

        self.floating_methods[function_name] = locals()[function_name]

    def add_determine_state_method(self, determine_state_method):
        if determine_state_method != None:
            source = inspect.getsource(determine_state_method)
            new_line_char = '\n'
            function_name = f'{self.name}_determine_state_method'
            exec(f"def {function_name}(entity, world): {source[source.index(new_line_char):]}")
            self.determine_state_method = locals()[function_name]
        else:
            self.determine_state_method = None

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

    # Determines if self will collide with the passed entity
    def will_collide_with(self, entity, x_pos=0, y_pos=0):
        if self.name in entity.collision_list:
            for arr in entity.grouping_map:
                if self.position[0] - y_pos == entity.position[0] + arr[0]:
                    if self.position[1] + x_pos == entity.position[1] + arr[1]:
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

class Lib:
    # Generic character constants class to be used in world framing
    class CHARACTER:
        END_WALL = " ||\n"
        SPACE = "-"
        WALL = "||"
        BORDER = " ="

    # Returns text colored using colorama and takes text to be colored plus a colorama Fore color specification
    @staticmethod
    def color_text(text, color):
        return f'{color}{text}{Style.RESET_ALL}'

    # getch method used to process key inputs immediately from the user without need to press the enter key to submit
    @staticmethod
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    # Clears display in between renders
    @staticmethod
    def clear():
        if name == 'nt':
            _ = system('cls')
        else:
            _ = system('clear')
