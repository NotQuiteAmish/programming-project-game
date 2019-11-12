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
This program uses three sets of coordinates:
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
                                                  ^               V
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
        pg_coordinates = pygame_coordinates(int(sprite.x_pos), int(sprite.y_pos))
        pygame.draw.circle(DISPLAYSURF, sprite.color, pg_coordinates, sprite.radius)


def terminate():
    """Ends the program"""
    pygame.quit()
    sys.exit()


class Planet:
    """
    Class that holds the information about a given planet.
    Location is an x, y
    """
    def __init__(self, radius=100, mass=1000, location=(WIN_WIDTH/2, WIN_HEIGHT/2), object_color=None):
        self.radius = radius
        self.mass = mass
        self.x_pos, self.y_pos = location
        self.color = object_color
        if self.color is None:
            self.color = random.choice(list(pygame.color.THECOLORS.values()))

    def __str__(self):
        return 'radius: ' + str(self.radius)


def main():
    global DISPLAYSURF, FPSCLOCK

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    planets = []
    for i in range(100):
        planets.append(Planet(radius=400-4*i, object_color=color.THECOLORS['red']))

    draw_objects(planets)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.update()
        FPSCLOCK.tick(FPS)


if __name__ == '__main__':
    main()
