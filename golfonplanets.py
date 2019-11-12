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
    """Converts world coordinates and returns pygame coordinates"""
    pygame_x = world_x - camera_x
    pygame_y = camera_y - world_y
    return pygame_x, pygame_y


def draw_objects(objects):
    """Draws all of the objects in list "objects" onto the screen (DISPLAYSURF)
       Objects in "objects" have world coordinates that will be converted to pygame coordinates before drawing"""
    for sprite in objects:
        sprite.draw()


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
        return camera_rect.collidepoint(*coords)
    return None


def random_position_in_active_zone():
    """Returns a random (x, y) position within the active zone"""
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
    DOT = 0
    CROSS = 1

    def __init__(self, location=None, size=0, type=DOT, color=color.THECOLORS['white']):
        self.location = location
        if self.location is None:
            self.location = random_position_out_of_view()

        self.x_pos, self.y_pos = self.location
        self.pg_location = pygame_coordinates(*self.location)
        self.size = size
        self.width, self.height = (self.size * 2, self.size * 2)
        self.pg_left, self.pg_top = pygame_coordinates((self.x_pos - self.size), (self.y_pos + self.size))
        self.type = type
        self.color = color

    def draw(self):
        self.pg_location = pygame_coordinates(*self.location)
        pygame.draw.circle(DISPLAYSURF, self.color, self.pg_location, self.size)



def main():
    global DISPLAYSURF, FPSCLOCK, camera_x, camera_y

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    planets = []
    for i in range(100):
        planets.append(Planet(radius=400 - 4 * i))

    stars = []
    for i in range(400):
        stars.append(Star(color=random.choice(list(color.THECOLORS.values()))))

    while True:


        # Deal with events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

        # React to held keys
        keys = pygame.key.get_pressed()
        if keys[K_DOWN]:
            camera_y -= 3
        if keys[K_UP]:
            camera_y += 3
        if keys[K_LEFT]:
            camera_x -= 3
        if keys[K_RIGHT]:
            camera_x += 3

        #


        # Check for stars going outside
        for star in stars:
            print(star.x_pos)
            if not is_in_active_zone(star):
                print('outside!')
                del(star)
                stars.append(Star())

        # Draw stuff
        DISPLAYSURF.fill(color.Color(7, 0, 15, 255))
        draw_objects(stars)
        # draw_objects(planets)

        pygame.display.update()
        FPSCLOCK.tick(FPS)


if __name__ == '__main__':
    main()
