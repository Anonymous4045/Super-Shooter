import pygame as pg
import threading
import random
import time

from playsound import playsound
from pathlib import Path


game_name = "Super Shooter"

WIDTH, HEIGHT = 1000, 700

pg.init()
pg.font.init()

PROJECT_DIR = Path(__file__).parent
ASSETS_DIR = PROJECT_DIR / 'Assets'
FOOTSTEPS_DIR = ASSETS_DIR / 'Footsteps'

# Assets
GUNNER_RIGHT = pg.image.load(ASSETS_DIR / 'Gunner.png')
GUNNER_LEFT = pg.transform.flip(GUNNER_RIGHT, True, False)

EVIL_TWIN_RIGHT = pg.image.load(ASSETS_DIR / 'Evil Twin.png')
EVIL_TWIN_LEFT = pg.transform.flip(EVIL_TWIN_RIGHT, True, False)

ZOMBIE_RIGHT = pg.image.load(ASSETS_DIR / 'Zombie.png')
ZOMBIE_LEFT = pg.transform.flip(ZOMBIE_RIGHT, True, False)

BULLET_RIGHT = pg.image.load(ASSETS_DIR / 'Bullet.png')
BULLET_LEFT = pg.transform.flip(BULLET_RIGHT, True, False)

STONE = pg.image.load(ASSETS_DIR / 'Stone.png')

# Animations
GUNNER_RIGHT_CENTER = pg.image.load(ASSETS_DIR / 'Gunner (center).png')
GUNNER_LEFT_CENTER = pg.transform.flip(GUNNER_RIGHT_CENTER, True, False)

GUNNER_ANIMATIONS = [pg.image.load(ASSETS_DIR / f'Gunner Animation {i}.png') for i in range(1, 8)]
GUNNER_ANIMATIONS = [GUNNER_ANIMATIONS] + [[pg.transform.flip(a, True, False) for a in GUNNER_ANIMATIONS]]

# Sounds
FOOTSTEPS = [FOOTSTEPS_DIR / f'0{i}-Audio Track.mp3' for i in range(1, 16)]
FOOTSTEPS = list(map(lambda s: str(s), FOOTSTEPS))
SONG = str(ASSETS_DIR / 'Music.wav')

pg.display.set_caption(game_name)

screen = pg.display.set_mode((WIDTH, HEIGHT))

# Colors
white = 255, 255, 255
black = 0, 0, 0
red = 255, 0, 0
green = 0, 255, 0
blue = 0, 0, 255


def play_song():
    while True:
        playsound(SONG, block=True)


song_thread = threading.Thread(target=play_song, name='Background_song')
song_thread.daemon = True
song_thread.start()


class Text:
    all = []

    def __init__(self, message: str, foreground, background, size, center,
                 has_outline=False, outline_color=white):
        self.all.append(self)
        self.message = message
        self.foreground = foreground
        font = pg.font.get_default_font()
        self.text = pg.font.Font(font, size).render(
            message, True, foreground, background
        )
        self.rect = self.text.get_rect()
        self.rect.center = center
        self.has_outline = has_outline
        self.outline_color = outline_color

    def show(self):
        screen.blit(self.text, self.rect)
        if self.has_outline:
            pg.draw.rect(screen, self.outline_color, self.rect, 1)


class Entity:
    all = []
    last_fire = None
    firerate = .5
    grace = firerate - .01
    jump_air_time = .35
    jump_power = 30
    hit_cd = 1

    def __init__(self, health, damage, pos, sprites: list, animations=None):
        self.speed = 7.5
        self.damage = damage
        self.all.append(self)
        self.sprites = {'right': sprites[0], 'left': sprites[1]}
        self.health = health
        self.x, self.y = pos
        self.direction = 'right'
        self.width, self.height = self.sprites[self.direction].get_size()
        self.frames = 1
        self.is_walking = self.is_jumping = False
        self.jump_cd = self.jump_air_time * 2
        self.animations = animations
        self.jump_start = self.jump_end = self.last_hit = self.last_jump = 0

    @property
    def rect(self):
        return self.sprites[self.direction].get_rect(topleft=(self.x, self.y))

    def fire(self):
        if self.last_fire is None or time.perf_counter() - self.last_fire > self.firerate:
            Bullet((self.x + 50 if self.direction in ('right', 'right center') else self.x + 20,
                    self.y + self.height // 2 - 8),
                   {'right': 'right', 'left': 'left', 'right center': 'right', 'left center': 'left'}[self.direction])
            self.last_fire = time.perf_counter()
            playsound(str(ASSETS_DIR / 'Gunshot.mp3'), block=False)

    def jump(self):
        self.last_jump = time.perf_counter()
        self.is_jumping = True
        self.jump_start = time.perf_counter()
        self.jump_end = self.jump_start + self.jump_air_time

    def is_on_ground(self) -> bool:
        return any([t.rect.collidepoint(self.x + self.width // 2, self.y + self.height + 17) for t in Terrain.all])

    def kill(self):
        del Entity.all[Entity.all.index(self)], self

    def show(self):
        screen.blit(self.sprites[self.direction], (self.x, self.y))


class Bullet:
    all = []
    lifespan = 3
    sprites = {'right': BULLET_RIGHT, 'left': BULLET_LEFT}
    speed = 50
    damage = 25

    def __init__(self, pos, direction: str):
        self.all.append(self)
        self.start = time.perf_counter_ns()
        self.x, self.y = pos
        self.direction = direction

    @property
    def rect(self):
        return Bullet.sprites[self.direction].get_rect(topleft=(self.x, self.y))

    def check_life(self):
        if time.perf_counter_ns() - self.start > self.lifespan * 1_000_000_000:
            Bullet.all.remove(self)
            del self

    def move(self):
        self.x += {'right': Bullet.speed, 'left': -Bullet.speed,
                   'right center': Bullet.speed, 'left center': -Bullet.speed}[self.direction]

    def destroy(self):
        try:
            del Bullet.all[Bullet.all.index(self)], self
        except ValueError:
            pass

    def show(self):
        screen.blit(Bullet.sprites[self.direction], (self.x, self.y))


def clear_t():
    for t in Terrain.all:
        t.destroy()


def generate_terrain():
    for t in Terrain.all:
        t.show()


class Terrain:
    all = []

    def __init__(self, pos, sprite):
        Terrain.all.append(self)
        self.x, self.y = pos
        self.sprite = sprite

    @property
    def rect(self):
        return self.sprite.get_rect(topleft=(self.x, self.y))

    def show(self):
        screen.blit(self.sprite, (self.x, self.y))


# Levels
def level_1():
    player_spawn = 100, 500

    Entity(100, 25, (700, player_spawn[1]), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 4

    for row in range(0, 6):
        for column in range(32):
            Terrain((32 * column, HEIGHT - 32 * row), STONE)
    return player_spawn


def level_2():
    player_spawn = 0, HEIGHT - 132

    for i in range(32):
        Terrain((i * 32, HEIGHT - 32), STONE)
    for i in range(25):
        Terrain((i * 32, HEIGHT - 32 * 5), STONE)
    for i in range(5, 32):
        Terrain((i * 32, HEIGHT - 32 * 10), STONE)
    for i in range(25):
        Terrain((i * 32, HEIGHT - 32 * 15), STONE)

    for y in [32, 320]:
        Entity(100, 25, (WIDTH - 100, HEIGHT - y - 100), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 4
    for y in [32 * 5, 32 * 15]:
        Entity(100, 25, (0, HEIGHT - y - 100), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 4

    return player_spawn


def level_3():
    player_spawn = 0, HEIGHT - 132

    for n in range(0, 21, 5):
        Entity(100, 10, (WIDTH - 100, HEIGHT - 100 - 32 * n), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 5
        for i in range(n, 33):
            Terrain((32 * i, HEIGHT - 32 * n - 32), STONE)

    Entity(100, 10, (WIDTH - 100, 0), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 5

    return player_spawn


def level_4():
    player_spawn = 0, HEIGHT - 132

    for a in range(20):
        for b in range(a * 3, 32):
            Terrain((b * 32, HEIGHT - 32 * a), STONE)

    for x, y in enumerate([364, 232, 100]):
        Entity(100, 10, (0, y - 100), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 4
        for i in range(10 * x + 5):
            Terrain((i * 32, y), STONE)

    return player_spawn


def level_5():
    player_spawn = 300, 100

    for i in range(32):
        Terrain((i * 32, HEIGHT - 32), STONE)
    for i in range(25):
        Terrain((i * 32, HEIGHT - 32 * 5), STONE)
    for i in range(5, 32):
        Terrain((i * 32, HEIGHT - 32 * 10), STONE)
    for i in range(25):
        Terrain((i * 32, HEIGHT - 32 * 15), STONE)

    for i in range(5):
        Entity(500, 10, (i * 5, 100), [ZOMBIE_RIGHT, ZOMBIE_LEFT]).speed = 4

    return player_spawn


load_level = {1: level_1, 2: level_2, 3: level_3, 4: level_4, 5: level_5}

Text(game_name, white, black, 100, (500, 300))
Text("Play", white, black, 64, (500, 400), has_outline=True)

menu = True
while menu:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            quit()
            exit()

        if event.type == pg.KEYDOWN and event.key == pg.K_q:
            pg.quit()
            quit()
            exit()

        elif event.type == pg.MOUSEBUTTONDOWN:
            for sprite in Text.all:
                if sprite.message == 'Play' and sprite.rect.collidepoint(event.pos):
                    menu = False

    screen.fill(black)

    for text in Text.all:
        text.show()

    pg.display.update()

while True:
    Entity.all = []
    Terrain.all = []
    Bullet.all = []

    Text.all = [Text(f' {i} ', random.choice([white, red, green, blue]), black, 150,
                     [(int(150 * (i % 5) + WIDTH * .2), (HEIGHT // 2) + 75) for i in range(5)][i - 1],
                     has_outline=True) for i in range(1, 6)] + \
               [Text('Levels', green, black, 200, (WIDTH // 2, HEIGHT // 2 - 150))]

    level_selector = True
    while level_selector:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()

            if event.type == pg.MOUSEBUTTONDOWN:
                for sprite in Text.all:
                    if sprite.rect.collidepoint(event.pos) and sprite.has_outline:
                        level_selected = int(sprite.message)
                        level_selector = False

            if event.type == pg.KEYDOWN and event.key == pg.K_q:
                pg.quit()
                quit()
                exit()

        # Display
        screen.fill(black)

        for text in Text.all:
            text.show()

        pg.display.update()

    Text.all = []

    player_spawn = load_level[level_selected]()

    a, b = [GUNNER_ANIMATIONS[i] for i in range(2)]
    player = Entity(100, 0, player_spawn, [GUNNER_RIGHT, GUNNER_LEFT], animations=[
        [a[0], a[1], a[2], a[3], a[3], a[2], a[1], a[0], a[4], a[5], a[6], a[6], a[5], a[4]],
        [b[0], b[1], b[2], b[3], b[3], b[2], b[1], b[0], b[4], b[5], b[6], b[6], b[5], b[4]]
    ])
    del a, b
    player.sprites = {**player.sprites, **{'right center': GUNNER_RIGHT_CENTER, 'left center': GUNNER_LEFT_CENTER}}

    player.animations = [[i for i in lst for _ in range(2)] for lst in player.animations]

    is_pressed = {'a': False, 'd': False, ' ': False}
    twin = False
    twin_can_spawn = True

    frame = 0

    start_time = time.time()

    while level_selected:
        if frame == 260 and twin_can_spawn:
            twin = Entity(300, 25, player_spawn, [EVIL_TWIN_RIGHT, EVIL_TWIN_LEFT])
            twin.speed = 4
            del entity.all[-1]
            twin_can_spawn = False

        pg.time.Clock().tick(30)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.__dict__['button'] == 1:
                    player.fire()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_q:
                    pg.quit()
                    quit()
                    exit()
                if event.key == pg.K_f:
                    player.fire()
                if event.key == pg.K_SPACE and player.is_on_ground():
                    player.jump()
                # if event.key == pg.K_p: This code is for taking a screenshot
                #     pg.image.save(screen, 'screenshot.png')
                is_pressed[event.__dict__['unicode']] = True

            if event.type == pg.KEYUP:
                if event.__dict__['unicode'] in is_pressed:
                    is_pressed[event.__dict__['unicode']] = False

        # Logic
        if frame > 10_000:
            frame = 0

        f = 3
        if is_pressed['a']:
            if player.direction == 'right':
                player.direction = 'left center'
                player.frames = f
            else:
                if player.frames <= 0:
                    player.direction = 'left'
                    player.x -= player.speed
                    player.is_walking = 1
        elif is_pressed['d']:
            if player.direction == 'left':
                player.direction = 'right center'
                player.frames = f
            else:
                if player.frames <= 0:
                    player.direction = 'right'
                    player.x += player.speed
                    player.is_walking = 2
        else:
            player.is_walking = 0

        if player.frames > 0:
            player.frames -= 1

        # Display
        screen.fill(blue)

        generate_terrain()

        Text(f'Health: {player.health}', red, blue, 64, (WIDTH // 2, 32))

        for text in Text.all:
            text.show()
            del Text.all[Text.all.index(text)], text

        for bullet in Bullet.all:
            bullet.check_life()
            bullet.move()
            bullet.show()
            if twin:
                if bullet.rect.colliderect(twin.rect):
                    pg.draw.rect(screen, black, twin.rect)
                    bullet.destroy()
                    twin.health -= Bullet.damage
            for entity in Entity.all:
                if entity != player:
                    if bullet.rect.colliderect(entity.rect):
                        bullet.destroy()
                        entity.health -= Bullet.damage
                        pg.draw.rect(screen, green, entity.rect)

        if player.is_walking and not frame % 10:
            playsound(FOOTSTEPS[random.randint(1, 14)], block=False)

        for entity in Entity.all:
            for t in Terrain.all:
                if t.rect.collidepoint(entity.x, entity.y):
                    entity.is_jumping = False
                if t.rect.collidepoint(entity.x + 45, entity.y + entity.height - 10):
                    entity.x += entity.speed
                    entity.y -= 35
                if t.rect.collidepoint(entity.x + 55, entity.y + entity.height - 10.):
                    entity.x -= entity.speed
                    entity.y -= 35
            if entity.x <= 0:
                entity.x = 0
            if entity.x + entity.width >= WIDTH:
                entity.x = WIDTH - entity.width
            if entity == twin:
                if twin.y > player.y:
                    twin.y -= twin.speed
                if twin.y < player.y:
                    twin.y += twin.speed
            if entity == player:
                if player.is_walking:
                    screen.blit(player.animations[player.is_walking - 2][frame % len(player.animations[0])],
                                (player.x, player.y))
                if player.is_jumping:
                    if time.perf_counter() - entity.jump_start < Entity.jump_air_time:
                        entity.y -= entity.jump_power
                    if time.perf_counter() >= entity.jump_end:
                        entity.is_jumping = False
                elif not player.is_on_ground():
                    player.y += entity.jump_power
                if not player.is_walking:
                    player.show()
            else:
                if entity.x < player.x and player.x - entity.x > 5:
                    entity.x += entity.speed
                    entity.direction = 'right'
                elif entity.x > player.x and entity.x - player.x > 5:
                    entity.x -= entity.speed
                    entity.direction = 'left'
                if entity.rect.colliderect(player.rect) and time.perf_counter() - entity.last_hit > entity.hit_cd:
                    player.health -= entity.damage
                    playsound(str(ASSETS_DIR / 'Damage.mp3'), block=False)
                    pg.draw.rect(screen, red, player.rect)
                    entity.last_hit = time.perf_counter()
                if not entity.is_on_ground():
                    entity.y += entity.jump_power
                entity.show()
            if entity.health <= 0:
                if entity == player:
                    playsound(str(ASSETS_DIR / 'Death.mp3'), block=True)
                    level_selected = None
                else:
                    entity.kill()

        if twin:
            if twin.rect.colliderect(player.rect) and time.perf_counter() - twin.last_hit > twin.hit_cd:
                player.health -= twin.damage
                playsound(str(ASSETS_DIR / 'Damage.mp3'), block=False)
                pg.draw.rect(screen, red, player.rect)
                twin.last_hit = time.perf_counter()
            if twin.x > player.x:
                twin.direction = 'left'
                twin.x -= twin.speed
            if twin.x < player.x:
                twin.direction = 'right'
                twin.x += twin.speed
            if twin.y > player.y:
                twin.y -= twin.speed
            if twin.y < player.y:
                twin.y += twin.speed
            screen.blit(twin.sprites[twin.direction], twin.rect)
            if twin.health <= 0:
                del twin
                twin = False

        # Player wins level
        if len(Entity.all) == 1 and Entity.all[0] == player:
            level_selected = None
            for entity in Entity.all:
                entity.kill()
            for i, t in enumerate(Terrain.all):
                del Terrain.all[i], t
            for i, bullet in enumerate(Bullet.all):
                del Bullet.all[i], bullet

        pg.display.update()

        frame += 1
