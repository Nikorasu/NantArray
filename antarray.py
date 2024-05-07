#!/usr/bin/env python3
import numpy as np
from time import sleep

'''
Rules for ant pheromone simulation within an array:
- Main array can contain: empty-0, hive-1, food-2, walls-3, 10-17 (fooding ants), 20-27 (homing ants) (to indicate direction last moved)
- Secondary array for pheromones: negative left by foodingAnts, positive by HomingAnts, both decreasing to 0 as they "evaporate"
- as they move, ants leave "pheromone" values in the corresponding spot in the pheromone array, to indicate whatever it just came from, food or hive
- ants can either be in fooding food mode (10-17), or bringing food home (20-27), and leave corresponding pheromones as they move
- ants are processed based on the 8 spaces around them in both arrays, ignoring the spot they're on, and the 3 spots "behind" the ant
- each "round" ants move onto the space of their target pheromone, with the lowest value, if multiple pheromones present
- ants cannot move into spaces already occupied by other ants, the hive, food, or walls.
- when a foodingAnt finds food, it changes to homingAnt, and homingAnts change back to foodingAnts when they find hive
- when target pheromones not detected, continue in same direction with occasional random variation +/- 1 (to avoid getting stuck in a corner)
- if only the non-targeted pheromone is present (in front), move the towards strongest of that type, to hopefully follow similar-ants
- when an ant moves onto a spot with an existing pheromone in the phero array, that value is added to the pheromone the ant would've left
'''
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔') # for printing simulation state later, ants will be arrows indicating direction
symbols = {0: ' ', 1: '\x1b[33m⭖\x1b[0m', 2: '\x1b[32m☘\x1b[0m', 3: '▒'} # for printing simulation state later, ants will be symbols indicating direction
directions = ((-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)) # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (40,120)  # size of array - simulation space, fits in terminal
p_lvl = 20  # initial strength-level of pheromones ants put out

class AntArray:

    def __init__(self, size=sim_size, num_ants=10, num_food=1, ant_radius=7, food_radius=sim_size[1]//2):
        self.array = np.zeros(size, dtype=np.int16)
        self.phero = np.zeros(size, dtype=np.int16)
        self.array[[0, -1], :] = self.array[:, [0, -1]] = 3  # place walls on edges of array
        # place hive into middle of array
        hive_x, hive_y = size[0]//2, size[1]//4
        self.array[hive_x, hive_y] = 1
        # calculate the distance from each point to the hive
        x_indices, y_indices = np.indices(size)
        distances = np.sqrt((x_indices - hive_x)**2 + (y_indices - hive_y)**2)
        # place ants into array, randomly within ant_radius of the hive
        a_indices = np.argwhere((self.array == 0) & (distances <= ant_radius))
        a_chosen = a_indices[np.random.choice(a_indices.shape[0], num_ants, replace=False)]
        self.array[tuple(a_chosen.T)] = np.random.randint(10, 18, num_ants)
        self.phero[tuple(a_chosen.T)] = -p_lvl  # each ant will leave pheromone in its spot in the phero array
        # place food sources into array, randomly outside of food_radius from the hive
        f_indices = np.argwhere((self.array == 0) & (distances > food_radius))
        f_chosen = f_indices[np.random.choice(f_indices.shape[0], num_food, replace=False)]
        self.array[tuple(f_chosen.T)] = 2

    def print_state(self):
        for i, row in enumerate(self.array):
            row_symbols = []
            for j, value in enumerate(row.tolist()):
                phero_value = self.phero[i][j]
                if phero_value > 0:
                    bg_color = f'\x1b[48;2;0;{int(phero_value)};0m' # green
                elif phero_value < 0:
                    bg_color = f'\x1b[48;2;{int(-phero_value)};0;0m' # red
                else:
                    bg_color = ''
                if value in symbols:
                    row_symbols.append(bg_color + symbols[value] + '\x1b[0m')
                else:
                    color_code = '\x1b[33m' if 10 <= value <= 17 else '\x1b[32m'
                    arrow = arrows[(value % 10) - 1]
                    row_symbols.append(bg_color + color_code + arrow + '\x1b[0m')
            print(''.join(row_symbols))
        #for row in self.array: print(' '.join([symbols[value] if value in symbols else ('\x1b[33m' if 10 <= value <= 17 else '\x1b[32m') + arrows[(value % 10) - 1] + '\x1b[0m' for value in row.tolist()]))

    def update(self):
        # Iterate over all cells with ants
        ant_indices = np.argwhere((self.array >= 10) & (self.array <= 27))
        for x, y in ant_indices:
            # Determine the ant's current state (fooding or homing) and direction
            is_fooding = 10 <= self.array[x, y] <= 17
            ant_direction = (self.array[x, y] % 10) - 1

            # Calculate the new position based on the ant's current direction
            #nx, ny = x + directions[ant_direction][0], y + directions[ant_direction][1]
            nx, ny = np.add([x,y], directions[ant_direction])
            # Check if the new position is valid
            if self.array[nx, ny] == 0:
                # Update the ant's position
                self.array[x, y] = 0
                self.array[nx, ny] = ant_direction + (10 if is_fooding else 20) + 1
                # Leave pheromones in the new position
                self.phero[nx, ny] += -p_lvl if is_fooding else p_lvl
                self.phero[nx, ny] = max(-255, min(255, self.phero[nx, ny]))

        # Evaporate pheromones
        self.phero[self.phero > 0] -= 1
        self.phero[self.phero < 0] += 1

if __name__ == '__main__':
    ant_array = AntArray()
    # Main simulation loop
    while True:
        ant_array.print_state()
        sleep(0.2)
        ant_array.update()
