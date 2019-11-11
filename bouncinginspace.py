# Space simulator with gravity and collisions
# Caleb Hostetler 11/6/2019
# Some code snippets taken from pymunk example program "pymunkarrows.py"
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
click_sound = None

# How many planets to create - for higher planet quantities the gravitational
# constant will be set to a lower default value
num_planets = 20


# Function for creating a "planet" it takes several arguments, and colors it a random shade of green
def create_planet(space: pymunk.Space, radius_in, mass_in, position):
    """Function for creating a "planet". it takes several arguments, and colors it a random shade of green.
    Returns a body and a shape for the planet"""
    planet_body = pymunk.Body(mass_in, moment=pymunk.moment_for_circle(mass_in, 0, radius_in))
    planet_shape = pymunk.Circle(planet_body, radius_in)
    planet_body.position = position
    planet_shape.friction = 0.5
    planet_shape.elasticity = .7
    planet_shape.collision_type = PLANET

    planet_shape.color = (0, random.randint(50, 255), 0, 255)
    return planet_body, planet_shape


def run_gravity(body_1: pymunk.Body, body_2: pymunk.Body, g):
    """Function that can be called to apply gravitational impulses between two bodies.
    g is the gravitational constant"""
    distance = 2 * math.sqrt((body_1.position[0] - body_2.position[0]) ** 2 + (body_1.position[1] - body_2.position[0]) ** 2)
    force = body_1.mass * body_2.mass / (distance ** 2) * g
    impulse = Vec2d(force, 0)
    impulse = impulse.rotated((body_1.position - body_2.position).angle)
    if distance >= 5:
        body_1.apply_impulse_at_world_point(impulse.rotated(math.pi), body_2.position)
        body_2.apply_impulse_at_world_point(impulse, body_2.position)


# Collision handler setup
def planet_collision(arbiter, space, data):
    """Function to be called upon a collision between two planets. Should play a sound"""
    # TODO: Allow more sounds to play
    pass
    # pygame.mixer.Channel(0).stop()
    # pygame.mixer.Channel(0).play(click_sound)




# Game start
def main():
    # Start up the game
    pygame.init()
    screen: Surface = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    running = True

    space = pymunk.Space()

    # This gravity would be if we wanted to have every object move in one direction, not towards each other
    space.gravity = (0, 0)

    # Allow pymunk to draw to pygame screen
    draw_options = pygame_util.DrawOptions(screen)

    # Sound to play when planets collide
    global click_sound
    click_sound = pygame.mixer.Sound('resources/click.ogg')

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
        planet_body, planet_shape = create_planet(space, size, math.pi * size ** 2, (random.randint(15, screen.get_width() - 15), random.randint(15, screen.get_height() - 15)))
        space.add(planet_shape)
        space.add(planet_body)
        planets.append(planet_body)

    # Set gravitational constant for planets - more planets means lower starting constant
    grav_const = 200 / num_planets
    gravity_enabled = True

    # Set up collision sounds between planets (see planet_collision)
    # handler = space.add_collision_handler(PLANET, PLANET)
    # handler.post_solve = planet_collision

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
                print(pygame.mouse.get_pos())
                if not music_started:
                    # Background Music
                    pygame.mixer.music.load('resources/moon.ogg')
                    pygame.mixer.music.play(-1, 0.0)
                    music_started = True
                mouse_position = pymunk.pygame_util.from_pygame(Vec2d(pygame.mouse.get_pos()), screen)
                mouse_angle = (mouse_position - ball_body.position).angle
                impulse = ball_body.mass * 1000 * Vec2d(1, 0)
                impulse.rotate(mouse_angle)
                ball_body.apply_impulse_at_world_point(impulse, ball_body.position)

            if event.type == KEYDOWN:
                # If up or down is pressed, change the gravitational constant by a factor of 10
                if event.key == K_UP:
                    grav_const *= 1.5
                    print("Gravity:", grav_const)
                if event.key == K_DOWN:
                    print("Gravity:", grav_const)
                    grav_const /= 1.5

                # Enable / Disable gravity with space
                if event.key == K_SPACE:
                    gravity_enabled = not gravity_enabled

        if gravity_enabled:
            for i, planet_1 in enumerate(planets):
                # run_gravity(planet_1, ball_body, grav_const)
                for planet_2 in planets[i+1:]:
                    run_gravity(planet_1, planet_2, grav_const)

        # Graphics ---------------------------------------------------------------------------

        # Clear Screen
        screen.fill(pygame.color.THECOLORS['black'])

        # Use pygame interactivity to draw pymunk stuff
        space.debug_draw(draw_options)

        # Draw the rest of the stuff
        # screen.blit(pygame.transform.rotate(marble_img, ball_body.rotation_vector.angle_degrees), (ball_body.position[0] - ball_shape.radius, screen.get_height() - ball_body.position[1] - ball_shape.radius))
        font = pygame.font.SysFont("Arial", 13)
        # pygame.draw.rect(screen, color.THECOLORS['gray'], Rect(0, 0, 260, 60), 0)
        screen.blit(font.render("Click anywhere to fire the red ball towards the mouse", 1, color.THECOLORS["white"]), (5, 5))
        screen.blit(font.render("Press up or down to change the strength of gravity, space to enable/disable", 1, color.THECOLORS["white"]), (5, 20))
        screen.blit(font.render("Gravitational Strength:", 1, color.THECOLORS["white"]), (5, 40))
        screen.blit(font.render(str(round(grav_const, 3)), 1, color.THECOLORS["yellow"]), (115, 40))

        gravity_color, gravity_text = (color.THECOLORS['green'], 'Enabled') if gravity_enabled else (color.THECOLORS['red'], 'Disabled')
        screen.blit(font.render("Gravity:", 1, color.THECOLORS["white"]), (5, 55))
        screen.blit(font.render(gravity_text, 1, gravity_color), (45, 55))

        # Update the screen
        pygame.display.flip()

        # Update physics and pygame clock
        fps = 60
        dt = 1. / fps
        space.step(dt)

        clock.tick(fps)


if __name__ == '__main__':
    sys.exit(main())
