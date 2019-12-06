# Golf On Planets
# Caleb Hostetler
# 11/11/2019


import sys

import pygame
from pygame import Surface
from pygame.locals import *

import random
import math

import pymunk
from pymunk.vec2d import Vec2d
from pymunk import pygame_util

'''
This program uses two sets of coordinates:
    - Pygame coordinates - Set of coordinates related to the window of the game. Origin is ALWAYS at the top left of the
                           window. Y axis increases as you move DOWN.
    - World/pymunk coordinates -  Coordinate system in which Y value increases as you move UP. Similar to a normal 
                                x/y graph.
                                
All calculations should be performed in world coordinates whenever possible. Coordinates should only be converted
to pygame coordinates when things need drawn on screen. Any objects with a position will have an (x,y) pair that 
refers to their position in WORLD COORDINATES

 -------------------------------           -------------------------------             ----------------------------
| Pygame coords for mouse, etc. |   ->    |          World coords         |    ->     | Pygame coordinates to draw |
 -------------------------------           -------------------------------             ----------------------------
                                                  ^               |
                                                  |               V
                                           --------------------------------     
                                          |       Physics Calculations     |
                                           --------------------------------
 
 Some important variables to know about:
    - camera_x, camera_y - This is the (x,y) world coordinate of the camera's top left corner
    - camera_center - (Include?) (x,y) coordinate of the center of the camera
    - camera_width, camera_height - Dimensions of the area seen by the camera. Should usually be the size of the 
      window (WIN_WIDTH, WIN_HEIGHT), although this may be possible to change if you want to "zoom out"
    - WIN_WIDTH, WIN_HEIGHT - Width and height of the game window
    - ACTIVE_ZONE_WIDTH - The width of the "active zone" around the window:
    
     ________________________________________________________________________
    |                                                                        |
    |                                                                        |
    |                          pymunk space                                  |
    |                                                                        |
    |                ____________________________                            |
    |               |      active zone           |                           |
    |               |    +__________________     |                           |
    |               |    |                  |    |                           |
    |               |    |     pygame       |    |                           |   ("+" represents the location of 
    |               |    |     camera       |    |                           |    (camera_x, camera_y))
    |               |    |                  |    |                           |
    |               |     ------------------     |                           |
    |               |____________________________|                           |
    |                                                                        |
    |                                                                        |
    |                                                                        |
     ------------------------------------------------------------------------
      

 Camera System
 
 The camera is a 700x700 window that shows the objects within that view. 
 
 
'''

fun_mode = False

WIN_WIDTH = 700
WIN_HEIGHT = 600
ACTIVE_ZONE_WIDTH = WIN_WIDTH
FPS = 60
SPACE = pymunk.Space()

# Collision types
PLANET = 0
PLAYER = 1
LASER  = 2

camera_x, camera_y = 0, WIN_HEIGHT

DISPLAY_SURF: pygame.Surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

# Game modes
MENU = 0
PLAY = 1
GAME_OVER = 2

crash_sound = pygame.mixer.Sound

circle_shapes = []
lasers = []
planets = []
planet_shapes = []

score = 0

global player_health
player_health = 100


def world_coordinates(pygame_x, pygame_y):
    """Converts pygame coordinates and returns world coordinates"""
    world_x = camera_x + pygame_x
    world_y = camera_y - pygame_y
    return world_x, world_y


def pygame_coordinates(world_x, world_y):
    """Converts world coordinates and returns pygame coordinates. Pygame coordinates must be integers"""
    pygame_x = int(world_x - camera_x)
    pygame_y = int(camera_y - world_y)
    return pygame_x, pygame_y


def draw_objects(objects):
    """Draws all of the objects in list "objects" onto the screen (DISPLAY_SURF)
       Objects in "objects" have world coordinates that will be converted to pygame coordinates before drawing"""
    for sprite in objects:
        sprite.draw()


def draw_pymunk_circles(shapes: [pymunk.Shape]):
    """Draws circular pymunk bodies so they appear in the correct location"""
    for shape in shapes:
        shape.pg_center = pygame_coordinates(*shape.body.position)
        pygame.draw.circle(DISPLAY_SURF, shape.color, shape.pg_center, int(shape.radius))
        # This line points what direction the shape's body is facing. It's kinda janky, not sure why it works
        # the way it does.
        pygame.draw.line(DISPLAY_SURF, color.THECOLORS['black'],
                         shape.pg_center, shape.pg_center + Vec2d(shape.radius, 0).rotated(shape.body.angle), 2)


def draw_lasers(laser_list: [pymunk.Shape]):
    for laser in laser_list:
        laser.tip_coords = pygame_coordinates(*laser.body.position)
        laser.back_coords = pygame_coordinates(*(Vec2d(20, 0).rotated(laser.body.angle) + laser.body.position))
        pygame.draw.line(DISPLAY_SURF, laser.color, laser.tip_coords, laser.back_coords, 3)


def terminate():
    """Ends the program"""
    pygame.quit()
    sys.exit()


def is_in_active_zone(subject):
    """Returns True if object is at least partially within the active zone, False if entirely outside"""
    object_rect = pygame.rect.Rect(subject.pg_left, subject.pg_top, subject.width, subject.height)
    active_rect = pygame.rect.Rect(0 - ACTIVE_ZONE_WIDTH,             0 - ACTIVE_ZONE_WIDTH,
                                   WIN_WIDTH + 2 * ACTIVE_ZONE_WIDTH, WIN_HEIGHT + 2 * ACTIVE_ZONE_WIDTH)
    return active_rect.colliderect(object_rect)


def is_in_camera_zone(subject=None, coords=None):
    """Returns True if object is at least partially within the camera zone, False if entirely outside"""
    camera_rect = pygame.rect.Rect(0, 0, WIN_WIDTH, WIN_HEIGHT)
    if subject is not None:
        object_rect = pygame.rect.Rect(subject.pg_left, subject.pg_top, subject.width, subject.height)
        return camera_rect.colliderect(object_rect)
    if coords is not None:
        return camera_rect.collidepoint(pygame_coordinates(*coords))
    return None


def random_position_in_active_zone():
    """Returns a random (x, y) world position within the active zone"""
    x_pos = random.randint(camera_x - ACTIVE_ZONE_WIDTH, camera_x + WIN_WIDTH + ACTIVE_ZONE_WIDTH)
    y_pos = random.randint(camera_y - WIN_HEIGHT - ACTIVE_ZONE_WIDTH, camera_y + ACTIVE_ZONE_WIDTH)
    return x_pos, y_pos


def random_position_out_of_view():
    """Returns a random (x, y) position that is within the active zone, but not in view of the camera"""
    # Keeps generating random points until it finds one not in the active zone
    inside_camera_view = True
    x_pos, y_pos = 0, 0
    while inside_camera_view:
        x_pos, y_pos = random_position_in_active_zone()
        inside_camera_view = is_in_camera_zone(coords=(x_pos, y_pos))

    return x_pos, y_pos


def screen_center():
    """Returns the centermost point of the camera in world coordinates"""
    x_pos = camera_x + WIN_WIDTH/2
    y_pos = camera_y - WIN_HEIGHT/2
    return x_pos, y_pos


def center_camera_on(focus_object: pymunk.Body):
    """Moves the camera so that the focus_object is in the dead center
    (Based on the Body.position of the object"""
    global camera_x, camera_y
    camera_center_x, camera_center_y = focus_object.position
    camera_x = int(camera_center_x - WIN_WIDTH/2)
    camera_y = int(camera_center_y + WIN_HEIGHT/2)
    return camera_x, camera_y


def draw_gauge(level, x_pos, max=100, gauge_color = color.THECOLORS['red']):
    percentage = int(level / max * 100)
    full_rect = Rect(x_pos, WIN_HEIGHT - (100)       , 20, 100)
    gauge_rect = Rect(x_pos, WIN_HEIGHT - (percentage), 20, percentage)
    pygame.draw.rect(DISPLAY_SURF, gauge_color, gauge_rect)
    pygame.draw.rect(DISPLAY_SURF, color.THECOLORS['gray'], full_rect, 2)


def draw_fuel(fuel_level):
    """This function draws a fuel gauge. fuel_level is a number between 0 and 100"""
    draw_gauge(fuel_level, 10, 100, color.THECOLORS['orange'])


def draw_health(health_level):
    """This function draws a red fuel gauge. health_level is a number between 0 and 100"""
    draw_gauge(health_level, 35, 100, color.THECOLORS['red'])


def draw_ammo(ammunition):
    draw_gauge(ammunition, 60, 100, color.THECOLORS['green'])


def create_player_ammunition(player: pymunk.Shape, ammunition_color=color.THECOLORS['green']):
    """Function that creates a new ammunition blast using the angle and position of the shape creating it (player)
    Returns the ammunition body and shape

    The body is the head of the laser, and the shape is just a circle with radius 2"""
    ammunition_body = pymunk.Body(mass=.1, moment=pymunk.moment_for_circle(.1, 0, 2))
    ammunition_shape = pymunk.Circle(ammunition_body, 2)
    player_position = player.body.position
    ammunition_body.velocity = Vec2d(1000, 0).rotated(-player.body.angle) + player.body.velocity
    ammunition_body.angle = -player.body.angle
    ammunition_body.position = Vec2d(20, 0).rotated(-player.body.angle) + player_position
    ammunition_shape.collision_type = LASER

    ammunition_shape.color = ammunition_color
    return ammunition_body, ammunition_shape

# ------------------------------ Collision Types ---------------------------------


def player_planet_collision(arbiter, space, data):
    global player_health
    damage: Vec2d = arbiter.total_impulse.get_length() / 1000
    random_sound_path = 'resources/explosions/explosion' + str(random.randint(1, 5)) + '.ogg'
    explosion_sound = pygame.mixer.Sound(random_sound_path)
    explosion_sound.stop()
    explosion_sound.play()
    player_health -= damage
    return True


def laser_planet_collision(arbiter, space, data):
    global score
    global lasers, planets
    laser_shape = arbiter.shapes[0]
    planet_shape = arbiter.shapes[1]
    if planet_shape not in planet_shapes:
        planet_shapes.remove(planet_shape)
    planets.remove(planet_shape.object)
    lasers.remove(laser_shape)
    space.remove(laser_shape, laser_shape.body)
    space.remove(planet_shape, planet_shape.body)

    score += planet_shape.radius
    print(score)

    random_sound_path = 'resources/explosions/explosion' + str(random.randint(1, 5)) + '.ogg'
    explosion_sound = pygame.mixer.Sound(random_sound_path)
    explosion_sound.stop()
    explosion_sound.play()

    new_planet = Planet(50)
    planet_shapes.append(new_planet.shape)
    planets.append(new_planet)
    return True


class Planet:
    """
    Class that holds the information about a given planet.
    Location is an (x, y) coordinate of the center in world coordinates

    This class is a work in progress, it doesn't do anything remarkable yet

    pg_XXX variables are the planet's position in pygame coordinates
    """
    def __init__(self, radius=100, mass=1000, location=None, object_color=None,
                 body: pymunk.Body = None, shape: pymunk.Shape = None):
        self.radius = radius
        self.mass = mass

        self.location = location
        if self.location is None:
            self.location = random_position_out_of_view()
        self.x_pos, self.y_pos = self.location

        self.width, self.height = (self.radius * 2, self.radius * 2)

        self.color = object_color
        if self.color is None:
            self.color = random.choice(list(pygame.color.THECOLORS.values()))

        self.body = body
        self.shape = shape
        if self.body is None or self.shape is None:
            self.body, self.shape = Planet.create_planet(SPACE, self.radius, self.mass, self.location, self.color)

        self.shape.object = self
        SPACE.add(self.body)
        SPACE.add(self.shape)

        self.update_pg_coords()

    def __str__(self):
        return 'radius: ' + str(self.radius)

    def draw(self):
        # Update the coordinates, then draw
        self.update_pg_coords()
        pygame.draw.circle(DISPLAY_SURF, self.color, self.pg_location, self.radius)

    def update_pg_coords(self):
        self.location = self.body.position
        self.pg_location = pygame_coordinates(*self.location)
        self.pg_x, self.pg_y = pygame_coordinates(self.x_pos, self.y_pos)
        self.pg_left, self.pg_top = pygame_coordinates((self.x_pos - self.radius), (self.y_pos + self.radius))
        if not is_in_active_zone(self):
            planet_shapes.remove(self.shape)
            planets.remove(self)
            SPACE.remove(self.shape, self.body)
            new_planet = Planet(random.randint(30, 60))
            planet_shapes.append(new_planet.shape)
            planets.append(new_planet)
            del(self)

    def create_planet(space: pymunk.Space, radius_in, mass_in, position, color=None):
        """Function for creating a "planet". it takes several arguments, and colors it a random shade of green.
        Returns a body and a shape for the planet"""
        planet_body = pymunk.Body(mass_in, moment=pymunk.moment_for_circle(mass_in, 0, radius_in))
        planet_shape = pymunk.Circle(planet_body, radius_in)
        planet_body.position = position
        planet_body.velocity = Vec2d(random.randint(0, 20), 0).rotated(random.random() * 6.2)
        planet_shape.friction = 0.5
        planet_shape.elasticity = .7
        planet_shape.collision_type = PLANET

        if color is None:
            planet_shape.color = (0, random.randint(50, 255), 0, 255)
        else:
            planet_shape.color = color
        return planet_body, planet_shape


class Star:
    """Class about the stars (dots in the background). Stars operate in a way such that whenever one goes out of the
    active area, a new one will be spawned off screen. The total number of stars stays constant.

    pg_XXX variables are pygame coordinates
    """
    _stars = []
    DOT = 0
    CROSS = 1

    def __init__(self, location=None, size=0, type=DOT, color=color.THECOLORS['white'], on_screen=False):
        self.location = location
        if self.location is None:
            if not on_screen:
                self.location = random_position_out_of_view()
            else:
                self.location = random_position_in_active_zone()

        self.x_pos, self.y_pos = self.location
        self.size = int(size)
        self.width, self.height = (self.size * 2, self.size * 2)
        self.type = type
        self.color = color
        self.update_pg_coords()
        # Whenever the star is created, add itself to the list of stars
        Star._stars.append(self)

    # Essentially, this says that two stars will be considered the same if they have the same location
    def __eq__(self, other):
        return self.location == other.location

    def draw(self):
        """Draw self on DISPLAY_SURF"""
        self.update_pg_coords()
        pygame.draw.circle(DISPLAY_SURF, self.color, self.pg_location, self.size)

    def update_pg_coords(self):
        """Update pygame coordinates to match the current world coordinates"""
        self.pg_location = pygame_coordinates(*self.location)
        self.pg_left, self.pg_top = pygame_coordinates((self.x_pos - self.size), (self.y_pos + self.size))
        if not is_in_active_zone(self):
            if self in Star._stars:
                Star(size=self.size, type=self.type, color=self.color)
                Star._stars.remove(self)


# The Game itself #################################################################################################
def main():
    # Some global variables used by many functions
    global DISPLAY_SURF, FPS_CLOCK, camera_x, camera_y, crash_sound, player_health, circle_shapes, lasers, planets, planet_shapes

    # Start up pygame settings
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption('Space Game')
    FPS_CLOCK = pygame.time.Clock()

    # Set up pymunk physics
    circle_shapes = []
    lasers = []

    # Create player body (space ship thing)
    player_body = pymunk.Body(mass=100, moment=pymunk.moment_for_circle(100, 0, 10))
    player_shape = pymunk.Circle(player_body, 15)
    player_shape.friction = 0.5
    player_shape.elasticity = 0.9
    player_shape.color = color.THECOLORS['coral']
    player_shape.collision_type = PLAYER
    circle_shapes.append(player_shape)

    # Create camera center body. This invisible body moves around to follow the player, and the camera is constantly
    # centered on it
    camera_body = pymunk.Body(mass=.00000001, moment=pymunk.moment_for_circle(1, 0, 3))

    # Add bodies to space
    SPACE.add(player_shape)
    SPACE.add(player_body)
    SPACE.add(camera_body)
    player_body.position = (0, 0)
    camera_body.position = (0, 0)

    for i in range(100):
        planets.append(Planet(radius=random.randint(30, 60), mass=1000 - 1 * i))
        planet_shapes.append(planets[i].shape)

    # Generate 1000 stars. These will be automatically added to the Star._stars list, and will replace themselves with
    # new stars if they exit the active zone
    for i in range(1000):
        pass
        Star(color=random.choice(list(color.THECOLORS.values())), size=0, on_screen=True)

    # Collision handling stuff
    player_planet_handler = SPACE.add_collision_handler(PLAYER, PLANET)
    player_planet_handler.post_solve = player_planet_collision
    laser_planet_handler  = SPACE.add_collision_handler(LASER, PLANET)
    laser_planet_handler.begin = laser_planet_collision

    # ------------------------------------- Sound --------------------------------------------------------
    # Play Music
    pygame.mixer.init(22100, -16, 2, 64)
    pygame.mixer.music.load('resources/punch-deck-feel-the-pulse.mp3')
    pygame.mixer.music.play(-1, 0.0)

    # Load sound effects
    crash_sound = pygame.mixer.Sound('resources/click.ogg')
    rocket_boost_sound = pygame.mixer.Sound('resources/rocket_boost.ogg')
    if not fun_mode:
        laser_sound = pygame.mixer.Sound('resources/laser.ogg')
    else:
        laser_sound = pygame.mixer.Sound('resources/fun_laser.ogg')

    # Create sound channels
    rocket_boost_channel: pygame.mixer.Channel = pygame.mixer.Channel(0)
    rocket_boost_channel.play(rocket_boost_sound, -1)                      # Play a sound but pause it, to be unpaused
    rocket_boost_channel.pause()                                           # When the rocket is boosting

    # Initialize player values for fuel, health, etc.
    rocket_fuel = 100
    player_health = 100
    ammunition = 100
    game_over_string = ''

    # Set the starting game mode, the menu
    game_mode = MENU
    title_font = pygame.font.Font('resources/Airstream.ttf', 64)
    button_font = pygame.font.Font('resources/Airstream.ttf', 24)

    start_button_rect = pygame.rect.Rect(WIN_WIDTH / 2 - 60, WIN_HEIGHT * (2 / 3), 120, 50)

    start_time = 0

    # ------------------------------------ Game Loop ---------------------------------------------------
    while True:

        # Deal with events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate()
                if event.key == pygame.K_UP and game_mode == PLAY and rocket_fuel > 0:
                    rocket_boost_channel.unpause()
                if event.key == pygame.K_SPACE:
                    if game_mode == PLAY and ammunition > 0:
                        laser_sound.stop()
                        laser_sound.play()
                        laser_body, laser_shape = create_player_ammunition(player_shape)
                        lasers.append(laser_shape)
                        SPACE.add(laser_body, laser_shape)
                        ammunition -= 1

            player_body.angular_velocity = 0

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP and game_mode == PLAY:
                    rocket_boost_channel.pause()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_mode==MENU and start_button_rect.collidepoint(*pygame.mouse.get_pos()):
                    start_game_sound = pygame.mixer.Sound('resources/click_button.ogg')
                    start_game_sound.play()
                    game_mode = PLAY
                    start_time = pygame.time.get_ticks()

        if game_mode == MENU:
            # Draw background
            DISPLAY_SURF.fill(color.Color(7, 0, 15, 255))
            draw_objects(Star._stars)

            # Draw the menu button
            mouse_pos = pygame.mouse.get_pos()
            start_button_color = color.Color(0, 180, 255, 255) if start_button_rect.collidepoint(*mouse_pos) \
                                                               else color.Color(0, 100, 150, 255)
            pygame.draw.rect(DISPLAY_SURF, start_button_color, start_button_rect)
            pygame.draw.rect(DISPLAY_SURF, color.Color(160, 160, 160, 255), start_button_rect, 2)

            button_text = button_font.render('START', True, color.THECOLORS['black'])
            button_text_rect = button_text.get_rect()
            button_text_rect.center = start_button_rect.center
            DISPLAY_SURF.blit(button_text, button_text_rect)

            instructions_one_text = button_font.render('Fly with arrow keys, fire with spacebar.', True, color.THECOLORS['orange'])
            instructions_one_rect = instructions_one_text.get_rect()
            instructions_one_rect.center = (WIN_WIDTH/2, WIN_HEIGHT * 1/2)
            DISPLAY_SURF.blit(instructions_one_text, instructions_one_rect)

            instructions_two_text = button_font.render("Don't crash, and don't let fuel, time, or ammo run out!", True,
                                                       color.THECOLORS['orange'])
            instructions_two_rect = instructions_two_text.get_rect()
            instructions_two_rect.center = (WIN_WIDTH / 2, WIN_HEIGHT * 1/2 + 35)
            DISPLAY_SURF.blit(instructions_two_text, instructions_two_rect)

            # Draw the title text
            title_text = title_font.render('Space Game', True, color.THECOLORS['white'])
            title_text_rect = title_text.get_rect()
            title_text_rect.center = (WIN_WIDTH/2, WIN_HEIGHT/3)
            DISPLAY_SURF.blit(title_text, title_text_rect)

        if game_mode == PLAY:
            '''This stuff is only to be run if the game is in "play" mode'''
            time_elapsed = round((pygame.time.get_ticks() - start_time)/1000)
            time_remaining = 60 - time_elapsed

            # React to held keys
            keys = pygame.key.get_pressed()
            if keys[K_UP]:
                # Provide forward force in direction the player is pointing
                if rocket_fuel > 0:
                    player_body.apply_impulse_at_local_point(Vec2d(800, 0).rotated(-2 * player_body.angle))
                    rocket_fuel -= .25

            if keys[K_LEFT]:
                player_body.angle -= .13
            if keys[K_RIGHT]:
                player_body.angle += .13

            # Check for game overs
            if rocket_fuel <= 0:
                rocket_fuel = 0
                rocket_boost_channel.pause()
                game_mode = GAME_OVER
                game_over_string = 'Out of fuel!'
                pygame.mixer.music.stop()
                game_over_sound = pygame.mixer.Sound('resources/out_of_gas.ogg')
                game_over_sound.play()

            if player_health <= 0:
                player_health = 0
                game_mode = GAME_OVER
                game_over_string = 'Your ship wrecked!'
                pygame.mixer.music.stop()
                game_over_sound = pygame.mixer.Sound('resources/crash.ogg')
                game_over_sound.play()

            if ammunition <= 0:
                ammunition = 0
                game_mode = GAME_OVER
                game_over_string = 'Out of ammunition!'
                pygame.mixer.music.stop()
                game_over_sound = pygame.mixer.Sound('resources/out_of_ammo.ogg')
                game_over_sound.play()

            if time_remaining <= 0:
                game_mode = GAME_OVER
                game_over_string = "Time's up!"
                pygame.mixer.music.stop()
                game_over_sound = pygame.mixer.Sound('resources/times_up.ogg')
                game_over_sound.play()

            player_body.angular_velocity = 0

            # Move the camera body and center the camera on it
            camera_body.velocity = player_body.velocity * .8 + (player_body.position - camera_body.position) * 2
            center_camera_on(camera_body)

            # Check for stars going outside
            for star in Star._stars:
                star.update_pg_coords()

            # Draw stuff
            DISPLAY_SURF.fill(color.Color(7, 0, 15, 255))
            draw_objects(Star._stars)
            draw_objects(planets)
            draw_lasers(lasers)
            draw_pymunk_circles(circle_shapes)

            draw_fuel(rocket_fuel)
            draw_health(player_health)
            draw_ammo(ammunition)


            # Draw timer/score box
            box_rectangle = Rect(0, 0, 200, 60)
            box_rectangle.center = (WIN_WIDTH/2, WIN_HEIGHT/10)
            pygame.draw.rect(DISPLAY_SURF, color.THECOLORS['black'], box_rectangle)
            pygame.draw.rect(DISPLAY_SURF, color.THECOLORS['white'], box_rectangle, 2)
            # Draw timer
            timer_text = button_font.render(str(time_remaining), True, color.THECOLORS['white'])
            timer_text_rect = timer_text.get_rect()
            timer_text_rect.center = (WIN_WIDTH/2, WIN_HEIGHT/12)
            DISPLAY_SURF.blit(timer_text, timer_text_rect)

            # Draw score
            score_text = button_font.render(str(score), True, color.THECOLORS['gray'])
            score_text_rect = score_text.get_rect()
            score_text_rect.center = (WIN_WIDTH/2, WIN_HEIGHT/12 + 25)
            DISPLAY_SURF.blit(score_text, score_text_rect)

            # Physics tick
            dt = 1. / FPS
            SPACE.step(dt)

        if game_mode == GAME_OVER:
            rocket_boost_sound.stop()
            # Display background
            DISPLAY_SURF.fill(color.Color(7, 0, 15, 255))
            draw_objects(Star._stars)

            # Large "GAME OVER" text
            game_over_text = title_font.render('Game Over!', True, color.THECOLORS['white'])
            game_over_text_rect = game_over_text.get_rect()
            game_over_text_rect.center = (WIN_WIDTH / 2, WIN_HEIGHT / 3)
            DISPLAY_SURF.blit(game_over_text, game_over_text_rect)

            # Score
            score_text = title_font.render(str(score), True, color.THECOLORS['gray'])
            score_text_rect = score_text.get_rect()
            score_text_rect.center = (WIN_WIDTH/2, WIN_HEIGHT/2)
            DISPLAY_SURF.blit(score_text, score_text_rect)

            # Details on how the player lost
            loss_details_text = button_font.render(game_over_string, True, color.THECOLORS['white'])
            loss_details_text_rect = loss_details_text.get_rect()
            loss_details_text_rect.center = (WIN_WIDTH/2, WIN_HEIGHT * 2/3)
            DISPLAY_SURF.blit(loss_details_text, loss_details_text_rect)



        # Update display
        pygame.display.update()
        FPS_CLOCK.tick(FPS)


if __name__ == '__main__':
    main()
