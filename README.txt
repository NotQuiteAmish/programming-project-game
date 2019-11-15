-------- Caleb's Python Project ----------

- Project 1 - November 7, 2019 -

Hello there, welcome to my project! I'm not entirely sure what my endgoal with this project is, but currently I am
working with the python library "pymunk". It is a physics engine that integrates well with pygame. It takes care of
collisions between objects, and it will also calculate any movement that I cause using forces and impulses.

The first project I made with this library is "bouncinginspace.py". It was made almost entirely from scratch, however
some barebones code snippets were taken from the pymunk example program "pymunkarrows.py". I included this in the
repository as a citation of sorts, but none of it is my original code.

bouncinginspace.py is a program that simulates several bodies floating in space. You can input force by clicking to send a
ball crashing into the planets. However, there is also additionally an option to enable gravity. The gravity code was
written entirely by me. Essentially, the code will loop through all of the objects on the screen and calculate the
gravitational interaction between them, and apply forces accordingly. The gravity can be turned up or down using the
arrow keys, or turned off entirely using the space bar.

Overall, I am very satisfied with how this turned out! I spent about 2 hours interacting with the example program to
familiarize myself with the library, and about 5 hours coding the program itself, as well as an hour or so on other aspects
of the program, such as setting up git to interact with GitHub, or downloading and creating assets for the program.

(Note - you may need to do "pip install pymunk" to get this to work. I haven't looked at all at how libraries work on
other peoples' machines)



- Project 2 - November 14, 2019 -

The new part of my project this week is "flyinginspace.py". I think my end goal for this project will be some game that
takes place in space. So, I want to be able to move around freely in the space and have the camera track the player
wherever they move.

The majority of the work on this program were the following things:
    - Code to make the camera follow the player
    - Code to generate stars in the background of space
    - Making pymunk work well with pygame in complex situations
    - Further practice with git and GitHub.

In all, I think I spent about 7 hours on this project between my last presentation on Monday, 11/11, and today,
Thursday, 11/14. All of the code is original except for small bare bones bits I used from bouncinginspace.py. I did a
*lot* of documentation so hopefully its commented well enough


