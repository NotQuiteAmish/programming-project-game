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

WIN_WIDTH = 700
WIN_HEIGHT = 600
ACTIVE_ZONE_WIDTH = WIN_WIDTH/2
FPS = 60
SPACE = pymunk.Space()

PLANET = 0

camera_x, camera_y = 0, WIN_HEIGHT

DISPLAY_SURF: pygame.Surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))


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


def draw_circle_shapes(shapes: [pymunk.Shape]):
    """Draws circular pymunk bodies so they appear in the correct location"""
    for shape in shapes:
        shape.pg_center = pygame_coordinates(*shape.body.position)
        pygame.draw.circle(DISPLAY_SURF, shape.color, shape.pg_center, int(shape.radius))
        # This line points what direction the shape's body is facing. It's kinda janky, not sure why it works
        # the way it does.
        pygame.draw.line(DISPLAY_SURF, color.THECOLORS['black'],
                         shape.pg_center, shape.pg_center + Vec2d(shape.radius, 0).rotated(shape.body.angle))


def terminate():
    """Ends the program"""
    pygame.quit()
    sys.exit()


def is_in_active_zone(object):
    """Returns True if object is at least partially within the active zone, False if entirely outside"""
    object_rect = pygame.rect.Rect(object.pg_left, object.pg_top, object.width, object.height)
    active_rect = pygame.rect.Rect(0 - ACTIVE_ZONE_WIDTH,             0 - ACTIVE_ZONE_WIDTH,
                                   WIN_WIDTH + 2 * ACTIVE_ZONE_WIDTH, WIN_HEIGHT + 2 * ACTIVE_ZONE_WIDTH)
    return active_rect.colliderect(object_rect)


def is_in_camera_zone(object=None, coords=None):
    """Returns True if object is at least partially within the camera zone, False if entirely outside"""
    camera_rect = pygame.rect.Rect(0, 0, WIN_WIDTH, WIN_HEIGHT)
    if object is not None:
        object_rect = pygame.rect.Rect(object.pg_left, object.pg_top, object.width, object.height)
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


class Planet:
    """
    Class that holds the information about a given planet.
    Location is an (x, y) coordinate of the center in world coordinates

    This class is a work in progress, it doesn't do anything remarkable yet

    pg_XXX variables are the planet's position in pygame coordinates
    """
    def __init__(self, radius=100, mass=1000, location=None, object_color=None, body:pymunk.Body=None, shape:pymunk.Shape=None):
        self.radius = radius
        self.mass = mass

        self.location = location
        if self.location is None:
            self.location = random_position_in_active_zone()
        self.x_pos, self.y_pos = self.location

        self.width, self.height = (self.radius * 2, self.radius * 2)

        self.color = object_color
        if self.color is None:
            self.color = random.choice(list(pygame.color.THECOLORS.values()))

        self.body = body
        self.shape = shape
        if self.body is None or self.shape is None:
            self.body, self.shape = Planet.create_planet(SPACE, self.radius, self.mass, self.location, self.color)

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

    def create_planet(space: pymunk.Space, radius_in, mass_in, position, color=None):
        """Function for creating a "planet". it takes several arguments, and colors it a random shade of green.
        Returns a body and a shape for the planet"""
        planet_body = pymunk.Body(mass_in, moment=pymunk.moment_for_circle(mass_in, 0, radius_in))
        planet_shape = pymunk.Circle(planet_body, radius_in)
        planet_body.position = position
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
    global DISPLAY_SURF, FPS_CLOCK, camera_x, camera_y

    # Start up pygame settings
    pygame.init()
    FPS_CLOCK = pygame.time.Clock()

    # Set up pymunk physics
    draw_options = pygame_util.DrawOptions(DISPLAY_SURF)
    circle_shapes = []

    # Create player body (space ship thing)
    player_body = pymunk.Body(mass=100, moment=pymunk.moment_for_circle(100, 0, 10))
    player_shape = pymunk.Circle(player_body, 10)
    player_shape.friction = 0.5
    player_shape.elasticity = 0.9
    player_shape.color = color.THECOLORS['coral']
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

    planets = []
    for i in range(100):
        pass
        # planets.append(Planet(radius=100 - 1 * i))

    # Generate 1000 stars. These will be automatically added to the Star._stars list, and will replace themselves with
    # new stars if they exit the active zone
    for i in range(1000):
        Star(color=random.choice(list(color.THECOLORS.values())), size=0, on_screen=True)

    # ------------------------------------- Sound --------------------------------------------------------
    # Play Music
    pygame.mixer.music.load('resources/punch-deck-feel-the-pulse.mp3')
    pygame.mixer.music.play(-1, 10.0)

    # Load sound effects
    rocket_boost_sound = pygame.mixer.Sound('resources/rocket_boost.ogg')

    # Create sound channels
    rocket_boost_channel: pygame.mixer.Channel = pygame.mixer.Channel(0)
    rocket_boost_channel.play(rocket_boost_sound, -1)                      # Play a sound but pause it, to be unpaused
    rocket_boost_channel.pause()                                           # When the rocket is boosting

    # Initialize player values for fuel, health, etc.
    rocket_fuel = 100
    boosting = False

    # ------------------------------------ Game Loop ---------------------------------------------------
    while True:

        # Deal with events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate()

        # React to held keys
        keys = pygame.key.get_pressed()
        if keys[K_UP]:
            # Provide forward force in direction the player is pointing
            player_body.apply_impulse_at_local_point(Vec2d(400, 0).rotated(-2 * player_body.angle))
            rocket_fuel -= .2
            rocket_boost_channel.unpause()
        else:
            rocket_boost_channel.pause()

        if keys[K_LEFT]:
            # Rotate the player
            player_body.angle -= .1
        elif keys[K_RIGHT]:
            player_body.angle += .1
        else:
            if player_body.angular_velocity != 0:
                player_body.angular_velocity = 0

        # Play ongoing sounds


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
        # SPACE.debug_draw(draw_options)
        draw_circle_shapes(circle_shapes)
        draw_fuel(rocket_fuel)
        draw_health(100)

        # Physics tick
        dt = 1. / FPS
        SPACE.step(dt)

        # Update display
        pygame.display.update()
        FPS_CLOCK.tick(FPS)


if __name__ == '__main__':
    main()
