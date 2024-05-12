#!/usr/bin/env python3
import numpy as np
from time import sleep
from scipy.ndimage import convolve
import os
if os.name == 'nt': import msvcrt # for Windows keyboard input
else: import sys, termios, tty, select # for Linux keyboard input

''' Newest Version - added Ant age-layer
Rules for ant pheromone simulation within an array:
- Solid layer contains: empty-0, hive-1, food-2, walls-3, ants-10-17 (foodingAnt directions), 20-27 (homingAnt directions).
- Ants leave pheromones in the corresponding layer based on their mode (fooding or homing).
- Ants decide to move based on the spaces around them, with priority to spaces in front of ant.
- Each "round" ants move onto the space of their target pheromone. If multiple of those pheromones present, decide behavior.
- Ants cannot move into spaces already occupied by other ants, the hive, food, or walls.
- Ants start with a pseudo-age-limit of 255, but for now, only decreases when ants moves over somewhere with both pheromones.
- When a foodingAnt finds food, it changes to homingAnt, and homingAnts change back to foodingAnts when they find hive. Age resets.
- When target pheromones not detected, continue in same direction with occasional random variation +/- 1.
- If only the non-targeted pheromone is present (in front), move towards strongest of that type, to hopefully follow similar-ants.
- When an ant moves onto a spot with an existing pheromone, that value will be added to the pheromone the ant will leave behind it.
'''
ants = 100
wander = [.1, .8, .1]   # probabilities of: turning left, going straight, or turning right. (must sum to 1?)[1/10,4/5,1/10]
p_lvl = 200  # initial strength-level of pheromones ants put out
sees = 3  # how much of the ant's view it can usually see, can only be 3, 5 or 7
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔')  # for printing simulation state later, ants will be arrows indicating direction
symbols = {1: '\x1b[31;1m⭖\x1b[0m', 2: '\x1b[32;1m☘\x1b[0m', 3: '▒'}  # empty, hive, food, wall
directions = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))  # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (os.get_terminal_size().lines, os.get_terminal_size().columns)

class AntArray:

    def __init__(self, size=(*sim_size,4), num_food=1, food_radius=sim_size[1]//2):
        self.array = np.zeros(size, dtype=np.uint8) # Initialize a 3D array
        # Place walls on edges of array on the first layer
        self.array[[0, -1], :, 0] = self.array[:, [0, -1], 0] = 3
        # Place hive into middle of array on the first layer
        self.hive = (size[0]//2, size[1]//4)
        self.array[self.hive[0], self.hive[1], 0] = 1
        # calculate the distance from each point to the hive
        x_indices, y_indices = np.indices((size[0], size[1]))
        distances = np.sqrt((x_indices - self.hive[0])**2 + (y_indices - self.hive[1])**2)
        # place food sources into array, randomly outside of food_radius from the hive
        f_indices = np.argwhere((self.array[:, :, 0] == 0) & (distances > food_radius))
        f_chosen = f_indices[np.random.choice(f_indices.shape[0], num_food, replace=False)]
        self.array[f_chosen[:, 0], f_chosen[:, 1], 0] = 2
        self.evap = 0
    
    def spawn_ant(self):
        near_hive = [self.array[self.hive[0] + dx, self.hive[1] + dy, 0] for dx, dy in directions]
        free_spaces = np.argwhere(np.array(near_hive) == 0).flatten()
        if free_spaces.size > 0:
            dir_idx = np.random.choice(free_spaces)
            new_pos = directions[dir_idx]
            self.array[self.hive[0] + new_pos[0], self.hive[1] + new_pos[1], 0] = 10 + dir_idx
            self.array[self.hive[0] + new_pos[0], self.hive[1] + new_pos[1], 3] = 255
    
    def scent_bubble(self, center, radius=10, layer=1, cmax=255):
        center_y, center_x = center
        y_dim, x_dim, _ = self.array.shape
        for x in range(max(0, center_x-radius), min(x_dim, center_x+radius+1)):
            for y in range(max(0, center_y-radius), min(y_dim, center_y+radius+1)):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)  # Euclidean distance
                if dist <= radius:
                    scaled_dist = int((1 - dist/radius) * cmax)
                    self.array[y, x, layer] = max(self.array[y, x, layer], scaled_dist) if cmax else max(self.array[y, x, layer], int(radius-dist))
    
    def diffuse(self, coefficient=.25):
        # Define your diffusion kernel for 2D
        kernel = np.array( [[0, 1/4, 0],
                            [1/4, 0, 1/4],
                            [0, 1/4, 0]])
        for i in range(1, 3):  # Only apply to layers 1 and 2
            layer = self.array[:, :, i].astype(float)  # Convert to float
            diffused = convolve(layer, kernel, mode='constant', cval=0)
            layer += coefficient * (diffused - layer)
            self.array[:, :, i] = np.clip(layer, 0, 255).astype(np.uint8)  # Convert back to uint8'''
    
    def update(self):
        # place value of 255 on corresponding layers under hive:
        self.array[self.hive[0], self.hive[1], 1] = 255
        # same for under food:
        for food in np.argwhere(self.array[:, :, 0] == 2):
            self.array[food[0], food[1], 2] = 255
        #for hive in np.argwhere(self.array[:, :, 0] == 1): self.scent_bubble(hive, radius=30, layer=1, cmax=200)
        #for efood in np.argwhere(self.array[:, :, 0] == 2): self.scent_bubble(efood, radius=15, layer=2, cmax=100)
        ant_indices = np.argwhere((self.array[:, :, 0] >= 10) & (self.array[:, :, 0] <= 27))
        if len(ant_indices) < ants:
            self.spawn_ant()
        for x, y in ant_indices:
            if self.array[x, y, 1] > 0 and self.array[x, y, 2] > 0:
                self.array[x, y, 3] -= 1
            if self.array[x, y, 3] == 0:
                self.array[x, y, 0] = 0
                continue
            # Determine the ant's current state (fooding or homing) and direction
            ant_mode = (10 <= self.array[x, y, 0] <= 17) + 1
            ant_dir = self.array[x, y, 0] % 10
            # Record what currently surrounds the ant
            surrounds = np.zeros((8, 4), dtype=np.uint8)
            for i, (dx, dy) in enumerate(directions):
                if (dx, dy) != directions[(ant_dir + 4) % 8]: surrounds[i] = self.array[x + dx, y + dy]
            # Prioritize stuff in front of ant, ordered by front, left, right
            view = np.zeros((7, 4), dtype=np.uint8) # 7 because we ignore what's directly behind ant
            view[0] = surrounds[ant_dir]  # What's in front of the ant first
            vkey = [0,-1,1,-2,2,-3,3] # Key for seeing in the relative direction, ant_dir = (ant_dir + vkey[targets[0]]) % 8
            for i, offset in enumerate(vkey): # Add elements with offsets of +/- 1, 2, 3 with wrap-around behavior
                view[i] = surrounds[(ant_dir + offset)%8]  # view[2*offset-1]
            # Switch mode and direction when reached food or hive
            if ant_mode in surrounds[:, 0]:
                ant_dir = (ant_dir + 4) % 8
                self.array[x, y, 0] = ant_dir + ant_mode * 10
                self.array[x, y, 3] = 255
                ant_mode = (2 if ant_mode == 1 else 1)
            #elif np.sum(view[:sees] == 3) > 2: # If walls directly ahead, turn randomly
            #    ant_dir = np.random.choice(np.where(surrounds[:, 0] == 0)[0])
            # Determine direction based on pheromones
            elif any(0 < i <= 255 for i in view[:sees, ant_mode]):
                #current_value = self.array[x, y, 2]
                ant_dir = (ant_dir + vkey[np.argmax(view[:sees, ant_mode])]) % 8  #np.where(view[:sees, ant_mode] > 0, view[:sees, ant_mode], -np.inf)
                # instead of using choice with the max value, go forward when all 3 options have target pheromone, turn away when 1 doesn't
            else: # if nothing else, wander randomly
                ant_dir = (ant_dir + np.random.choice([-1, 0, 1], p=wander)) % 8
            # Calculate the new position based on the ant's current direction
            nx, ny = np.add([x,y], directions[ant_dir])
            # Check if the new position is valid
            if self.array[nx, ny, 0] != 0:
                ant_dir = (ant_dir + vkey[np.random.choice(np.where(view == 0)[0])]) % 8 #surrounds[:, 0]
                nx, ny = np.add([x,y], directions[ant_dir])
            #if self.array[nx, ny, 0] != 0:
            #    ant_dir = np.random.choice(np.where(surrounds[:, 0] == 0)[0])
            #    nx, ny = np.add([x,y], directions[ant_dir])
            if self.array[nx, ny, 0] == 0:
                # Update the ant's position
                self.array[x, y, 0] = 0
                self.array[nx, ny, 0] = ant_dir + (10 if ant_mode-1 else 20)
                # Move the ant's age value to the new position then remove from old spot
                self.array[nx, ny, 3] = self.array[x, y, 3]
                self.array[x, y, 3] = 0
                # Add pheromones to the layer corresponding to the ant's state
                self.array[x, y, 1 if ant_mode-1 else 2] = min(255, self.array[x, y, 1 if ant_mode-1 else 2] + p_lvl)
                # Decrease opposing pheromone under the ant's position, MIGHT resolve circles sooner?
                self.array[x, y, 2 if ant_mode-1 else 1] = max(0, self.array[x, y, 2 if ant_mode-1 else 1] - p_lvl//4)
        # Evaporate pheromones
        self.diffuse()
        if self.evap: # == 2:
            mask = self.array[:, :, 1:3] > 0
            self.array[:, :, 1:3][mask] -= 1
        self.evap = not self.evap #(self.evap + 1) % 3
    
    def print_state(self):
        output = "\x1b[H"
        for i, row in enumerate(self.array[:, :, 0]):  # iterate over rows of layer 0
            row_symbols = []
            for j, value in enumerate(row):  # iterate over each value in the row
                if value in symbols:  # symbol values represent the solid stuff, hive, food, walls, ants
                    row_symbols.append(symbols[value])
                elif 10 <= value < 28:
                    color = '\x1b[31m' if 10 <= value <= 17 else '\x1b[32m' if 20 <= value <= 27 else ''
                    bgcol = f'\x1b[48;2;{int(self.array[i, j, 1])};{int(self.array[i, j, 2])};0m'
                    arrow = arrows[value % 10]
                    row_symbols.append(color + bgcol + arrow + '\x1b[0m')
                else:
                    row_symbols.append(f'\x1b[48;2;{int(self.array[i, j, 1])};{int(self.array[i, j, 2])};0m \x1b[0m')
            output += ''.join(row_symbols) + "\n"
        print(output[:-1], end='\r')

if __name__ == '__main__':
    try:
        print('\n' * (sim_size[0]-1))  # preserves terminal
        print('\x1b[?25l\x1b]0;NantSim',end='\a',flush=True)
        ant_array = AntArray()
        if os.name == 'posix': # if on Linux
            oldsettings = termios.tcgetattr(sys.stdin) # store old terminal settings
            tty.setcbreak(sys.stdin) # set terminal to cbreak mode (so input doesn't wait for enter)
        # Main simulation loop
        while ...:
            ant_array.print_state()
            sleep(0.05)
            ant_array.update()
            if os.name == 'nt' and msvcrt.kbhit() and msvcrt.getch() in (b'\x1b',b'q'): break # ESC or q to quit
            elif os.name == 'posix' and sys.stdin in select.select([sys.stdin],[],[],0)[0] and sys.stdin.read(1) in ('\x1b','q'): break
    except KeyboardInterrupt: pass # catch Ctrl+C
    finally: # ensures these run even if program is interrupted, so terminal functions properly on exit
        if os.name == 'posix': termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldsettings) # restore terminal settings
        print('\x1b[?25h')
