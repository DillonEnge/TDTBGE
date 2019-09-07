from TDTBGE import World, Entity, Lib
from colorama import Fore
import random

world_size = [ 200,200 ]

window_size = [ 20,20 ]

window_pos = [0,0]


world = World('Test World', world_size, window_size, window_pos=window_pos, debug=False,bgm='audio/adventure_theme.wav')

for i in range(int(world_size[0]/2)):
    random_x = random.randint(0,world_size[1] - 1)
    random_y = random.randint(0,world_size[0] - 1)
    food = Entity(
        f'food{i}',
        [
            { 'default': Lib.color_text('x', Fore.GREEN) }
        ],
        [ random_y,random_x ],
        value=5
    )
    world.add_entity(food)

def w(entity, world):
    if entity.get_y_pos() > world.window_pos[0]:
        entity.modify_pos(y_pos=1)
    elif world.window_pos[0] > 0:
        world.modify_window_pos(y_pos=1)
        entity.modify_pos(y_pos=1)

def a(entity, world):
    if entity.get_x_pos() > world.window_pos[1]:
        entity.modify_pos(x_pos=-1)
    elif world.window_pos[1] > 0:
        world.modify_window_pos(x_pos=-1)
        entity.modify_pos(x_pos=-1)

def s(entity, world):
    if entity.get_y_pos() < world.window_pos[0] + world.window_size[0] - 1:
        entity.modify_pos(y_pos=-1)
    elif world.window_pos[0] < world.world_size[0] - world.window_size[0]:
        world.modify_window_pos(y_pos=-1)
        entity.modify_pos(y_pos=-1)

def d(entity, world):
    if entity.get_x_pos() < world.window_pos[1] + world.window_size[1] - 1:
        entity.modify_pos(x_pos=1)
    elif world.window_pos[1] < world.world_size[1] - world.window_size[1]:
        world.modify_window_pos(x_pos=1)
        entity.modify_pos(x_pos=1)

def e(entity, world):
    for entity2 in world.entities:
        if entity2.name.find('food') != -1:
            if entity.is_touching(entity2):
                entity.attributes['hunger'] -= entity2.attributes['value']
                entity2.destroy()
                world.play_sound('audio/coin.wav')

def p(world):
    world.wait(5)

def determine_player_state(entity):
    if entity.attributes['hunger'] > 25:
        return 'famished'
    else:
        return 'default'

def o(entity,world):
    for entity2 in world.entities:
        if entity2.name.find('door') != -1:
            if entity.is_touching(entity2):
                entity2.attributes['door_open'] = True

player = Entity(
    'player',
    [
        { 'default': Lib.color_text('O', Fore.BLUE) },
        { 'famished': Lib.color_text('o', Fore.LIGHTCYAN_EX) }
    ],
    [ 1,1 ],
    determine_state_method=determine_player_state,
    hunger=50
)

def determine_door_state(entity, world):
    if entity.attributes['door_open'] == True:
        for entity2 in world.entities:
            if entity2.name.find(entity.attributes['censor_name']) != -1:
                entity2.destroy()
        return 'door_open'
    else:
        return 'door_closed'

door = Entity(
    'door',
    [
        { 'door_closed': Lib.color_text('D', Fore.RED) },
        { 'door_open': Lib.CHARACTER.SPACE }
    ],
    abstract=True,
    determine_state_method=determine_door_state,
    door_open=False,
    censor_name='censor'
)

def determine_censor_state(entity, world):
    for entity2 in world.entities:
        if entity2.name.find(entity.attributes['door']) != -1:
            if entity2.attributes['door_open'] == True:
                pass
    return 'default'
                

censor = Entity(
    'censor',
    [
        { 'default': Lib.color_text('X', Fore.MAGENTA) }
    ],
    abstract=True,
    grouping_map=[[0,0,4,9,'square_fill']],
    determine_state_method=determine_censor_state,
    door='door'
)

house = Entity(
    'house',
    [
        { 'default': Lib.color_text('X', Fore.MAGENTA) }
    ],
    [ 5,5 ],
    grouping_map=[ [0,0,5,10,'square_no_fill'], [1,1,censor], [0,3,door] ]
)

player.add_controller(w, 'w')
player.add_controller(a, 'a')
player.add_controller(s, 's')
player.add_controller(d, 'd')
player.add_controller(e, 'e')
player.add_controller(o, 'o')
world.add_controller(p, 'p')

world.add_entity(house)
world.add_entity(door)
world.add_entity(censor)
world.add_entity(player)

while True:
    world.render()
