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


# Screen Size
width, height = 700


class Planet:
    def __init__(self, radius=100, mass=1000, location=(width/2, height/2), color=random.choice(list(color.THECOLORS.values()))):
        self.radius = radius
        self.mass = mass
        self.location = location
        self.color = color

print(Planet().color)

