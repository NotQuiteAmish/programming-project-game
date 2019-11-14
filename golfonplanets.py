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
      

 
 
'''

WIN_WIDTH = 700
WIN_HEIGHT = 700
ACTIVE_ZONE_WIDTH = WIN_WIDTH/2
FPS = 60

camera_x, camera_y = 0, WIN_HEIGHT


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
    """Draws all of the objects in list "objects" onto the screen (DISPLAYSURF)
       Objects in "objects" have world coordinates that will be converted to pygame coordinates before drawing"""
    for sprite in objects:
        sprite.draw()


def draw_circle_shapes(shapes: [pymunk.Shape]):
    """Draws circular pymunk bodies so they appear in the correct location"""
    for shape in shapes:
        shape.pg_center = pygame_coordinates(*shape.body.position)
        pygame.draw.circle(DISPLAYSURF, shape.color, shape.pg_center, int(shape.radius))
        pygame.draw.line(DISPLAYSURF, color.THECOLORS['black'],
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
    x_pos = camera_x + WIN_WIDTH/2
    y_pos = camera_y - WIN_HEIGHT/2
    return x_pos, y_pos


def center_camera_on(focus_object: pymunk.Body):
    global camera_x, camera_y
    camera_center_x, camera_center_y = focus_object.position
    camera_x = int(camera_center_x - WIN_WIDTH/2)
    camera_y = int(camera_center_y + WIN_HEIGHT/2)
    return camera_x, camera_y


class Planet:
    """
    Class that holds the information about a given planet.
    Location is an (x, y) coordinate of the center in world coordinates
    """
    def __init__(self, radius=100, mass=1000, location=None, object_color=None):
        self.radius = radius
        self.mass = mass
        if location is None:
            location = random_position_in_active_zone()
        self.x_pos, self.y_pos = location
        self.width, self.height = (self.radius * 2, self.radius * 2)

        self.pg_left, self.pg_top = pygame_coordinates((self.x_pos - self.radius), (self.y_pos + self.radius))

        self.pg_x, self.pg_y = pygame_coordinates(self.x_pos, self.y_pos)
        self.color = object_color
        if self.color is None:
            self.color = random.choice(list(pygame.color.THECOLORS.values()))

    def __str__(self):
        return 'radius: ' + str(self.radius)

    def draw(self):
        self.pg_x, self.pg_y = pygame_coordinates(self.x_pos, self.y_pos)
        # Coordinates must be converted to integers for pygame to draw them
        self.pg_x = int(self.pg_x)
        self.pg_y = int(self.pg_y)
        pygame.draw.circle(DISPLAYSURF, self.color, (self.pg_x, self.pg_y), self.radius)


class Star:
    """Class about the stars (dots in the background). Stars operate in a way such that whenever one goes out of the
    active area, a new one will be spawned off screen. The total number of stars stays constant.
    """
    _stars = []
    DOT = 0
    CROSS = 1

    def __init__(self, location=None, size=0, type=DOT, color=color.THECOLORS['white']):
        self.location = location
        if self.location is None:
            self.location = random_position_out_of_view()

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
        self.update_pg_coords()
        pygame.draw.circle(DISPLAYSURF, self.color, self.pg_location, self.size)

    # The pg_XXXX
    def update_pg_coords(self):
        self.pg_location = pygame_coordinates(*self.location)
        self.pg_left, self.pg_top = pygame_coordinates((self.x_pos - self.size), (self.y_pos + self.size))
        if not is_in_active_zone(self):
            if self in Star._stars:
                Star(size=self.size, type=self.type, color=self.color)
                Star._stars.remove(self)


# The Game itself #################################################################################################
def main():
    global DISPLAYSURF, FPSCLOCK, camera_x, camera_y

    # Start up pygame settings
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    # Set up pymunk physics
    space = pymunk.Space()
    draw_options = pygame_util.DrawOptions(DISPLAYSURF)
    circle_shapes = []

    # Create player body
    player_body = pymunk.Body(mass=100, moment=pymunk.moment_for_circle(100, 0, 10))
    player_shape = pymunk.Circle(player_body, 10)
    player_shape.friction = 0.5
    player_shape.elasticity = 0.9
    player_shape.color = color.THECOLORS['coral']
    circle_shapes.append(player_shape)

    # Create camera center body
    camera_body = pymunk.Body(mass=.00000001, moment=pymunk.moment_for_circle(1, 0, 3))

    # Add bodies to space
    space.add(player_shape)
    space.add(player_body)
    space.add(camera_body)
    player_body.position = (0, 0)
    camera_body.position = (0, 0)


    planets = []
    for i in range(100):
        planets.append(Planet(radius=400 - 4 * i))

    for i in range(400):
        Star(color=random.choice(list(color.THECOLORS.values())))

    while True:

        # Deal with events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

        # React to held keys
        keys = pygame.key.get_pressed()
        if keys[K_UP]:
            player_body.apply_impulse_at_local_point(Vec2d(1000, 0).rotated(-2 * player_body.angle))
        if keys[K_LEFT]:
            player_body.angle = player_body.angle - (math.pi/60)
            print(player_body.angle)
        if keys[K_RIGHT]:
            player_body.angle = player_body.angle + (math.pi/60)
            print(player_body.angle)

        # Move the camera body and center the camera on it
        camera_body.velocity = player_body.velocity * .6 + (player_body.position - camera_body.position) * 3
        center_camera_on(camera_body)

        # Check for stars going outside
        for star in Star._stars:
            star.update_pg_coords()

        # Draw stuff
        DISPLAYSURF.fill(color.Color(7, 0, 15, 255))
        draw_objects(Star._stars)
        # draw_objects(planets)
        # space.debug_draw(draw_options)
        draw_circle_shapes(circle_shapes)

        # Physics tick
        dt = 1. / FPS
        space.step(dt)

        pygame.display.update()
        FPSCLOCK.tick(FPS)


if __name__ == '__main__':
    main()
