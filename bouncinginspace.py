# Game for moving around a 2d area with recoil
# Caleb Hostetler 11/6/2019
# Some code taken from pymunk example programs
import sys

import pygame
from pygame import Surface
from pygame.locals import *

import random
import math

import pymunk
from pymunk.vec2d import Vec2d
from pymunk import pygame_util



width, height = 700, 700
marble_img:Surface = pygame.image.load('resources/marble.png')

# Collision types
BALL = 0
PLANET = 1

num_planets = 10


def create_planet(space: pymunk.Space, radius_in, mass_in, position):
    planet_body = pymunk.Body(mass_in, moment=pymunk.moment_for_circle(mass_in, 0, radius_in))
    planet_shape = pymunk.Circle(planet_body, radius_in)
    planet_body.position = position
    planet_shape.friction = 0.5
    planet_shape.elasticity = 0.7
    planet_shape.collision_type = PLANET

    planet_shape.color = (0, random.randint(50, 255), 0, 255)
    return planet_body, planet_shape



# Game start
def main():
    # Start up the game
    pygame.init()
    screen: Surface = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    running = True
    font = pygame.font.SysFont("Arial", 16)

    space = pymunk.Space()
    space.gravity = (0, 0)

    # Allow pymunk to draw to pygame screen
    draw_options = pygame_util.DrawOptions(screen)

    clicks = 1

    # Initialize physical objects ---------------------------------------------------------------------------
    # Ball
    ball_body = pymunk.Body(mass=1000, moment=pymunk.moment_for_circle(1000, 0, marble_img.get_width()/2))
    ball_shape = pymunk.Circle(ball_body, marble_img.get_width()/2)
    ball_shape.friction = 0.5
    ball_shape.elasticity = .9
    ball_shape.collision_type = BALL
    ball_shape.color = color.THECOLORS['coral']

    # add ball to the scene
    space.add(ball_shape)
    space.add(ball_body)

    # Planets
    planets = []
    for i in range(num_planets):
        size = random.randint(10, 15)
        planet_body, planet_shape = create_planet(space, size, size**2, (random.randint(15, screen.get_width() - 15), random.randint(15, screen.get_height() - 15)))
        space.add(planet_shape)
        space.add(planet_body)
        planets.append(planet_body)

    # Walls
    walls = [pymunk.Segment(space.static_body, (0, 0),                                    (0, screen.get_width()), 2),
             pymunk.Segment(space.static_body, (0, screen.get_width()),                   (screen.get_height(), screen.get_width()), 2),
             pymunk.Segment(space.static_body, (screen.get_height(), screen.get_width()), (screen.get_height(), 0), 2),
             pymunk.Segment(space.static_body, (screen.get_height(), 0),                  (0, 0), 2),
             ]
    for wall in walls:
        wall.friction = 0.1
        wall.elasticity = 0.999
    space.add(walls)


    # Collision handler setup
    def ball_planet_collision(space, ball, planet, position, data):
        pass


    music_started = False
    ball_body.position = (300, 400)
    # Main game loop ----------------------------------------------------------------------------------------
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == QUIT or \
                    event.type == KEYDOWN and (event.key in [K_ESCAPE, K_q]):
                running = False
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if not music_started:
                    # Background Music
                    pygame.mixer.music.load('resources/moon.ogg')
                    pygame.mixer.music.play(-1, 0.0)
                    music_started = True
                clicks += 1
                print("Click!", clicks)
                mouse_position = pymunk.pygame_util.from_pygame(Vec2d(pygame.mouse.get_pos()), screen)
                mouse_angle = (mouse_position - ball_body.position).angle
                impulse = ball_body.mass * 1000 * Vec2d(1, 0)
                impulse.rotate(mouse_angle)
                ball_body.apply_impulse_at_world_point(impulse, ball_body.position)

        for i, planet_1 in enumerate(planets):
            for planet_2 in planets[i+1:]:
                g = 200 / num_planets
                distance = math.sqrt((planet_1.position[0] - planet_2.position[0]) ** 2 + (planet_1.position[1] - planet_2.position[1]) ** 2)
                force = planet_1.mass * planet_2.mass / (distance ** 2 + 10) * g
                impulse = Vec2d(force, 0)
                impulse = impulse.rotated((planet_1.position-planet_2.position).angle)
                planet_1.apply_impulse_at_world_point(impulse.rotated(math.pi), planet_1.position)
                planet_2.apply_impulse_at_world_point(impulse, planet_2.position)

        # Graphics ---------------------------------------------------------------------------

        # Clear Screen
        screen.fill(pygame.color.THECOLORS['black'])

        # Use pygame interactivity to draw pymunk stuff
        space.debug_draw(draw_options)

        # Draw the rest of the stuff
        screen.blit(pygame.transform.rotate(marble_img, ball_body.rotation_vector.angle_degrees), (ball_body.position[0] - ball_shape.radius, screen.get_height() - ball_body.position[1] - ball_shape.radius))


        # Update the screen
        pygame.display.flip()

        # Update physics and pygame clock
        fps = 60
        dt = 1. / fps
        space.step(dt)

        clock.tick(fps)


if __name__ == '__main__':
    sys.exit(main())
