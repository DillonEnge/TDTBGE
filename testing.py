from TDTBGE import World, Entity, Lib
from colorama import Fore
import random

world_size = [ 20,20 ]

world = World('Test World', world_size, bgm='audio/adventure_theme.wav')

for i in range(10):
    random_x = random.randint(0,19)
    random_y = random.randint(0,19)
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
    if entity.get_y_pos() > 0:
        entity.modify_pos(y_pos=1)

def a(entity):
    if entity.get_x_pos() > 0:
        entity.modify_pos(x_pos=-1)

def s(entity):
    if entity.get_y_pos() < world.world_size[0] - 1:
        entity.modify_pos(y_pos=-1)

def d(entity):
    if entity.get_x_pos() < world.world_size[1] - 1:
        entity.modify_pos(x_pos=1)
        print(entity.get_x_pos())

def e(entity, world):
    for entity2 in world.entities:
        if entity2.name.find('food') != -1:
            if entity.is_touching(entity2):
                entity.attributes['hunger'] -= entity2.attributes['value']
                entity2.destroy()
                world.play_sound('audio/coin.wav')

def p(world):
    world.wait(5)

def determine_state(entity):
    if entity.attributes['hunger'] > 25:
        return 'famished'
    else:
        return 'hungry'

player = Entity(
    'player',
    [
        { 'hungry': Lib.color_text('O', Fore.BLUE) },
        { 'famished': Lib.color_text('o', Fore.LIGHTCYAN_EX) }
    ],
    [ 1,1 ],
    determine_state_method=determine_state,
    debug=True,
    hunger=50
)

player.add_controller(w, 'w')
player.add_controller(a, 'a')
player.add_controller(s, 's')
player.add_controller(d, 'd')
player.add_controller(e, 'e')
world.add_controller(p, 'p')

world.add_entity(player)

while True:
    world.render()
