from TDTBGE import World, Entity, Lib
from colorama import Fore

worldSize = [ 20,20 ]

world = World('Test World', worldSize, bgm='audio/adventure_theme.wav')

food = Entity(
    'food',
    [
        { 'default': Lib.color_text('x', Fore.GREEN) }
    ],
    [ 5,5 ],
    value=5
)
world.add_entity(food)

def w(entity):
    entity.modify_pos(y_pos=1)

def a(entity):
    entity.modify_pos(x_pos=-1)

def s(entity):
    entity.modify_pos(y_pos=-1)

def d(entity):
    entity.modify_pos(x_pos=1)

def e(entity, world):
    for entity2 in world.entities:
        if entity2.name == 'food':
            if entity.is_touching(entity2):
                entity.attributes['hunger'] -= entity2.attributes['value']
                entity2.destroy()
                world.play_sound('audio/coin.wav')

def p(world):
    world.wait(5)

def determine_state(entity):
    if entity.attributes['hunger'] > 5:
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
    hunger=10
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
