#!/usr/bin/env python3
import numpy as np
from time import sleep
from scipy.ndimage import convolve
import os
if os.name == 'nt': import msvcrt # for Windows keyboard input
else: import sys, termios, tty, select # for Linux keyboard input

''' Newest Version - added Ant age-layer - changed datatype to float
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
ants = 80
p_lvl = 200  # initial strength-level of pheromones ants put out
wander = [.05, .9, .05]   # probabilities of: turning left, going straight, or turning right. (must sum to 1?)[1/10,4/5,1/10]
hivemult = 100
sees = 3  # how much of the ant's view it can usually see, can only be 3, 5 or 7. 3 seems best.
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔')  # for printing simulation state later, ants will be arrows indicating direction
symbols = {1: '\x1b[31;1m⭖\x1b[0m', 2: '\x1b[32;1m☘\x1b[0m', 3: '▒'}  # hive, food, wall
directions = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))  # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (os.get_terminal_size().lines, os.get_terminal_size().columns)

class AntArray:

    def __init__(self, size=(*sim_size,4), gap=20, num_food=2):
        self.array = np.zeros(size, dtype=np.float64) # Initialize a 3D array
        # Place walls on edges of array on the first layer
        self.array[[0, -1], :, 0] = self.array[:, [0, -1], 0] = 3
        # Place wall with gap down middle of array
        gap_start = np.random.randint(0, self.array.shape[0] - gap)
        self.array[:gap_start, self.array.shape[1]//2, 0] = 3
        self.array[gap_start + gap:, self.array.shape[1]//2, 0] = 3
        # Place hive into middle of array on the first layer
        self.hive = (size[0]//2, size[1]//4)
        self.array[self.hive[0], self.hive[1], 0] = 1
        # calculate the distance from each point to the hive
        x_indices, y_indices = np.indices((size[0], size[1]))
        distances = np.sqrt((x_indices - self.hive[0])**2 + (y_indices - self.hive[1])**2)
        # place food sources into array, randomly outside of food_dist from the hive
        f_indices = np.argwhere((self.array[:, :, 0] == 0) & (distances > sim_size[1]//2))
        f_chosen = f_indices[np.random.choice(f_indices.shape[0], num_food, replace=False)]
        self.array[f_chosen[:, 0], f_chosen[:, 1], 0] = 2
        self.array[f_chosen[:, 0], f_chosen[:, 1], 3] = 100 # intended to be times ants can touch food before food respawns
        self.died = 0  # for scoring, not implemented yet..
        self.returned = 0
    
    def spawn_ant(self, health=200):
        near_hive = [self.array[self.hive[0] + dx, self.hive[1] + dy, 0] for dx, dy in directions]
        free_spaces = np.argwhere(np.array(near_hive) == 0).flatten()
        if free_spaces.size > 0:
            dir_idx = np.random.choice(free_spaces)
            new_pos = directions[dir_idx]
            self.array[self.hive[0] + new_pos[0], self.hive[1] + new_pos[1], 0] = 10 + dir_idx
            self.array[self.hive[0] + new_pos[0], self.hive[1] + new_pos[1], 3] = health
    
    def scent_bubble(self, center, radius=10, layer=1, cmax=255):
        center_y, center_x = center
        y_dim, x_dim, _ = self.array.shape
        for x in range(max(0, center_x-radius), min(x_dim, center_x+radius+1)):
            for y in range(max(0, center_y-radius), min(y_dim, center_y+radius+1)):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)  # Euclidean distance
                if dist <= radius:
                    scaled_dist = int((1 - dist/radius) * cmax)
                    self.array[y, x, layer] = max(self.array[y, x, layer], scaled_dist) if cmax else max(self.array[y, x, layer], int(radius-dist))
    
    def diffuse(self, coefficient=.3, evap=.5):
        # Define your diffusion kernel for 2D
        kernel = np.array( [[0, .05, 0],
                            [.05, .8, .05],
                            [0, .05, 0]])
        for i in range(1, 3):  # Only apply to layers 1 and 2
            layer = self.array[:, :, i]#.astype(float) # Convert to float
            diffused = convolve(layer, kernel, mode='constant', cval=0)
            layer += coefficient * (diffused - layer)
            self.array[:, :, i] = np.clip(layer-evap, 0, 255)#.astype(np.uint8) # Convert back to uint8
    
    def update(self):
        for hive in np.argwhere(self.array[:, :, 0] == 1): self.scent_bubble(hive, radius=10, layer=1, cmax=255)
        for efood in np.argwhere(self.array[:, :, 0] == 2): self.scent_bubble(efood, radius=5, layer=2, cmax=100)
        # place value of 255 on corresponding layers under hive:
        self.array[self.hive[0], self.hive[1], 1] = 255
        # same for under food:
        for food in np.argwhere(self.array[:, :, 0] == 2):
            self.array[food[0], food[1], 2] = 255
        ant_indices = np.argwhere((self.array[:, :, 0] >= 10) & (self.array[:, :, 0] <= 27))
        if len(ant_indices) < ants:  # if there are not enough ants, spawn more
            self.spawn_ant()
        for x, y in ant_indices:
            if self.array[x, y, 1] > 100 and self.array[x, y, 2] > 100:
                self.array[x, y, 3] -= 1  # decrement health if ant is on both pheros
            if self.array[x, y, 3] == 0:  # if ant health reaches 0, remove it from the array
                self.array[x, y, 0] = 0
                self.died += 1
                continue
            # Determine the ant's current state (fooding or homing) and direction
            ant_mode = (10 <= self.array[x, y, 0] <= 17) + 1
            ant_dir = int(self.array[x, y, 0] % 10)
            # Record what currently surrounds the ant
            surrounds = np.zeros((8, 4), dtype=np.float64)  # maybe add weight to surrounds in direction of hive? (or food?)
            for i, (dx, dy) in enumerate(directions): surrounds[i] = self.array[x + dx, y + dy]
                #if (dx, dy) != directions[(ant_dir + 4) % 8]: surrounds[i] = self.array[x + dx, y + dy]
            if ant_mode == 1: # try weighing the surround options by direction to hive (maybe weigh mode2 away from hive)
                # Calculate distances to hive for surrounding positions
                h_dists = np.array([np.sqrt((nx - self.hive[0])**2 + (ny - self.hive[1])**2)
                                    for nx, ny in [(x + dx, y + dy) for dx, dy in directions]])
                # Subtract the minimum distance from all, then roll to other side, to weigh towards hive
                rolled_dists = np.roll(h_dists - min(h_dists), 4) * hivemult # times multiplier
                largest = np.argsort(rolled_dists)[-3:]
                closer_dists = np.zeros_like(rolled_dists)
                closer_dists[largest] = rolled_dists[largest]
                # Apply the shifted distances as weights to the hive pheromone layer
                surrounds[:, 1] = np.clip(surrounds[:, 1] + closer_dists, 0, 255)
                #surrounds[:, 1] = np.where(surrounds[:, 1] > 0, np.clip(surrounds[:, 1] + closer_dists, 0, 255), surrounds[:, 1])
            # Prioritize stuff in front of ant, ordered by front, left, right
            vkey = [0,-1,1,-2,2,-3,3] # Key for seeing in the relative direction, ant_dir = (ant_dir + vkey[targets[0]]) % 8
            view = np.zeros((7, 4), dtype=np.float64) # 7 because we ignore what's directly behind ant
            view[0] = surrounds[ant_dir]  # What's in front of the ant first
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
                #if self.array[x, y, 2] > 0:
                ant_dir = (ant_dir + vkey[np.argmax(view[:sees, ant_mode])]) % 8  #np.where(view[:sees, ant_mode] > 0, view[:sees, ant_mode], -np.inf)
                #else:
                #    ant_dir = (ant_dir + vkey[np.argmin(np.where(view[:sees, ant_mode] > 0, view[:sees, ant_mode], np.inf))]) % 8
                #actions = {(0,1,0):0,(1,0,1):0,(1,1,1):0,(1,1,0):1,(1,0,0):3,(0,1,1):2,(0,0,1):4}
                #ant_dir = (ant_dir + vkey[actions.get(tuple(view[:3, ant_mode] > 0))]) % 8
            else: # if nothing else, wander randomly
                ant_dir = (ant_dir + np.random.choice([-1, 0, 1], p=wander)) % 8
            # Calculate the new position based on the ant's current direction
            nx, ny = np.add([x,y], directions[ant_dir])
            # Check if the new position is valid
            if self.array[nx, ny, 0] != 0 and len(avail := np.where(view == 0)[0]): # if something in the way
                ant_dir = (ant_dir + vkey[np.random.choice(avail)]) % 8 #surrounds[:, 0]
                nx, ny = np.add([x,y], directions[ant_dir])
            if self.array[nx, ny, 0] == 0:
                # Update the ant's position
                self.array[x, y, 0] = 0
                self.array[nx, ny, 0] = ant_dir + (10 if ant_mode-1 else 20)
                # Move the ant's age value to the new position then remove from old spot
                self.array[nx, ny, 3] = self.array[x, y, 3]
                self.array[x, y, 3] = 0
                # Add pheromones to the layer corresponding to the ant's state
                self.array[x, y, 1 if ant_mode-1 else 2] = min(255, self.array[x, y, 1 if ant_mode-1 else 2] + p_lvl)
        # diffuse and evaporate pheromones
        self.diffuse()
        #self.array[:, :, 1:3][self.array[:, :, 1:3] > 0] -= 1
    
    def print_state(self):
        output = "\x1b[H"
        for i, row in enumerate(self.array[:, :, 0]):  # iterate over rows of layer 0
            row_symbols = []
            for j, value in enumerate(row):  # iterate over each value in the row
                if value in symbols:  # symbol values represent the solid stuff, hive, food, walls, ants
                    row_symbols.append(symbols[value])
                elif 10 <= value < 28:
                    color = '\x1b[31m' if 10 <= value <= 17 else '\x1b[32m' if 20 <= value <= 27 else ''
                    bgcol = f'\x1b[48;2;0;{int(self.array[i, j, 2])};{int(self.array[i, j, 1])}m'
                    arrow = arrows[int(value) % 10]
                    row_symbols.append(color + bgcol + arrow + '\x1b[0m')
                else:
                    row_symbols.append(f'\x1b[48;2;0;{int(self.array[i, j, 2])};{int(self.array[i, j, 1])}m \x1b[0m')
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
