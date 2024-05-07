#!/usr/bin/env python3
import numpy as np
from time import sleep

'''
Rules for ant pheromone simulation within an array:
- Main array can contain: empty-0, hive-1001, food-1002, walls-1003, 1010-1017 (foodingAnt directions), 1020-1027 (homingAnt directions)
- Pheromones are left as: negative values by foodingAnts, positive by HomingAnts, both decreasing to 0 as they "evaporate"
- as they move, ants leave "pheromone" values in the corresponding spot in the pheromone array, to indicate whatever it just came from, food or hive
- ants can either be in fooding-mode or homing-mode, and leave corresponding pheromones as they move
- ants are processed based on the 8 spaces around them in both arrays, ignoring the spot they're on, and the 3 spots "behind" the ant
- each "round" ants move onto the space of their target pheromone, with the lowest value, if multiple of those pheromones present
- ants cannot move into spaces already occupied by other ants, the hive, food, or walls.
- when a foodingAnt finds food, it changes to homingAnt, and homingAnts change back to foodingAnts when they find hive
- when target pheromones not detected, continue in same direction with occasional random variation +/- 1 (to avoid getting stuck in a corner)
- if only the non-targeted pheromone is present (in front), move the towards strongest of that type, to hopefully follow similar-ants
- when an ant moves onto a spot with an existing pheromone, that value will be added to the pheromone the ant will leave behind it
'''
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔') # for printing simulation state later, ants will be arrows indicating direction
symbols = {0: ' ', 1001: '\x1b[33m⭖\x1b[0m', 1002: '\x1b[32m☘\x1b[0m', 1003: '▒'} # for printing simulation state
directions = ((-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)) # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (40,120)  # size of array - simulation space, fits in terminal
p_lvl = 20  # initial strength-level of pheromones ants put out

class AntArray:

    def __init__(self, size=sim_size, num_ants=10, num_food=1, ant_radius=7, food_radius=sim_size[1]//2):
        self.array = np.zeros(size, dtype=np.int16)
        self.array[[0, -1], :] = self.array[:, [0, -1]] = 1003  # place walls on edges of array
        # place hive into middle of array
        hive_x, hive_y = size[0]//2, size[1]//4
        self.array[hive_x, hive_y] = 1001
        # calculate the distance from each point to the hive
        x_indices, y_indices = np.indices(size)
        distances = np.sqrt((x_indices - hive_x)**2 + (y_indices - hive_y)**2)
        # place ants into array, randomly within ant_radius of the hive
        a_indices = np.argwhere((self.array == 0) & (distances <= ant_radius))
        a_chosen = a_indices[np.random.choice(a_indices.shape[0], num_ants, replace=False)]
        self.array[tuple(a_chosen.T)] = np.random.randint(1010, 1018, num_ants)
        # place food sources into array, randomly outside of food_radius from the hive
        f_indices = np.argwhere((self.array == 0) & (distances > food_radius))
        f_chosen = f_indices[np.random.choice(f_indices.shape[0], num_food, replace=False)]
        self.array[tuple(f_chosen.T)] = 1002

    def print_state(self):
        output = ""
        for i, row in enumerate(self.array):
            row_symbols = []
            for j, value in enumerate(row.tolist()):
                if 0 < value < 1000:
                    row_symbols.append(f'\x1b[48;2;0;{int(value)};0m \x1b[0m') # green
                elif 0 > value:
                    row_symbols.append(f'\x1b[48;2;{int(-value)};0;0m \x1b[0m') # red
                elif value in symbols:
                    row_symbols.append(symbols[value])
                elif 1000 < value < 1028:
                    color = f'\x1b[31m\x1b[48;2;{p_lvl};0;0m' if 1010 <= value <= 1017 else f'\x1b[32m\x1b[48;2;0;{p_lvl};0m' if 1020 <= value <= 1027 else ''
                    arrow = arrows[(value % 10) - 1]
                    row_symbols.append(color + arrow + '\x1b[0m')
                
            output += ''.join(row_symbols) + "\n"
        print(output)

    def update(self):
        # Iterate over all cells with ants
        ant_indices = np.argwhere((self.array >= 1010) & (self.array <= 1027))
        for x, y in ant_indices:
            # Determine the ant's current state (fooding or homing) and direction
            is_fooding = 1010 <= self.array[x, y] <= 1017
            ant_direction = (self.array[x, y] % 10) - 1

            # Calculate the new position based on the ant's current direction
            nx, ny = np.add([x,y], directions[ant_direction])
            # Check if the new position is valid
            if self.array[nx, ny] < 1000:
                # Update the ant's position
                self.array[x, y] = (-p_lvl if is_fooding else p_lvl) + self.array[nx, ny]
                self.array[x, y] = max(-255, min(255, self.array[x, y]))
                self.array[nx, ny] = ant_direction + (1010 if is_fooding else 1020) + 1

        # Evaporate pheromones
        self.array[(0 < self.array) & (self.array < 1000)] -= 1  # 0 < self.array < 1000
        self.array[0 > self.array] += 1  # 0 > self.array

if __name__ == '__main__':
    ant_array = AntArray()
    # Main simulation loop
    while True:
        ant_array.print_state()
        sleep(0.2)
        ant_array.update()
