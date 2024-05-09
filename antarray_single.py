#!/usr/bin/env python3
import numpy as np
from time import sleep

'''
Rules for ant pheromone simulation within an array:
- Main array can contain: empty-0, hive-1001, food-1002, walls-1003, 1010-1017 (foodingAnt directions), 1020-1027 (homingAnt directions)
- Pheromones are left as: negative values by foodingAnts, positive by HomingAnts, both decreasing to 0 as they "evaporate"
- ants can either be in fooding-mode or homing-mode, and leave corresponding pheromones as they move, to indicate where they came from
- ants decide to move based on the spaces around them in the array, ignoring the spot they're on, and the spot "behind" the ant
- each "round" ants move onto the space of their target pheromone, with the lowest value, if multiple of those pheromones present
- ants cannot move into spaces already occupied by other ants, the hive, food, or walls
- when a foodingAnt finds food, it changes to homingAnt, and homingAnts change back to foodingAnts when they find hive
- when target pheromones not detected, continue in same direction with occasional random variation +/- 1 (to avoid getting stuck in a corner)
- if only the non-targeted pheromone is present (in front), move the towards strongest of that type, to hopefully follow similar-ants
- when an ant moves onto a spot with an existing pheromone, that value will be added to the pheromone the ant will leave behind it
'''
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔') # for printing simulation state later, ants will be arrows indicating direction
symbols = {0: ' ', 1001: '\x1b[33m⭖\x1b[0m', 1002: '\x1b[32m☘\x1b[0m', 1003: '▒'} # empty, hive, food, wall
directions = ((-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)) # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (40,120)  # size of array - simulation space, fits in terminal
p_lvl = 50  # initial strength-level of pheromones ants put out

class AntArray:

    def __init__(self, size=sim_size, num_ants=20, num_food=1, ant_radius=10, food_radius=sim_size[1]//2):
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
        for row in self.array:
            row_symbols = []
            for value in row.tolist():
                if 0 < value < 1000:
                    row_symbols.append(f'\x1b[48;2;0;{int(value)};0m \x1b[0m') # green
                elif 0 > value:
                    row_symbols.append(f'\x1b[48;2;{int(-value)};0;0m \x1b[0m') # red
                elif value in symbols:
                    row_symbols.append(symbols[value])
                elif 1000 < value < 1028:
                    color = f'\x1b[31m\x1b[48;2;{p_lvl};0;0m' if 1010 <= value <= 1017 else f'\x1b[32m\x1b[48;2;0;{p_lvl};0m' if 1020 <= value <= 1027 else ''
                    arrow = arrows[value % 10]
                    row_symbols.append(color + arrow + '\x1b[0m')
            output += ''.join(row_symbols) + "\n"
        print(output)

    def update(self):
        # use scent_bubble function on indexs with hive and food, np.argwhere(self.array == 1001), np.argwhere(self.array == 1002), each
        self.array = scent_bubble(self.array, tuple(np.argwhere(self.array == 1001)[0]), radius=15, negative=True)
        for efood in np.argwhere(self.array == 1002):
            self.array = scent_bubble(self.array, efood, radius=10)
        # Iterate over all cells with ants
        ant_indices = np.argwhere((self.array >= 1010) & (self.array <= 1027))
        for x, y in ant_indices:
            # Determine the ant's current state (fooding or homing) and direction
            is_fooding = 1010 <= self.array[x, y] <= 1017
            ant_direction = self.array[x, y] % 10
            #surrounds = [self.array[x + dx, y + dy] if (dx, dy) != directions[(ant_direction + 4) % 8] else 1003 for dx, dy in directions]
            #surrounds = self.array[(x + np.array(directions)[:, 0]) % self.array.shape[0], (y + np.array(directions)[:, 1]) % self.array.shape[1]]
            surrounds = self.array[x + np.array(directions)[:, 0], y + np.array(directions)[:, 1]]#.tolist()
            surrounds[(ant_direction + 4) % 8] = 0 if surrounds[(ant_direction + 4) % 8] < 1000 else 1003 #ignore phero behind
            sees = [surrounds[ant_direction]]
            for offset in range(1, 4): # Add elements with offsets of +/- 1, 2, 3 with wrap-around behavior
                sees.append(surrounds[(ant_direction + offset)%8])
                sees.append(surrounds[(ant_direction - offset)%8])
            # Determine the ant's new direction  based on the surrounding pheromones
            if is_fooding and 1002 in surrounds: #if fooding and food present, change to homing
                self.array[x, y] = (self.array[x, y] % 10) + 1020
                is_fooding = False
            elif not is_fooding and 1001 in surrounds: #if homing and hive present, change to fooding
                self.array[x, y] = (self.array[x, y] % 10) + 1010
                is_fooding = True
            
            if is_fooding and any(0<i<1000 for i in surrounds): #follow food phero in direction originated
                ant_direction = np.argmin(np.where(surrounds > 0, surrounds, np.inf)) # set ant_direction to index of surrounds value that's closest to 0
            #elif is_fooding and any(0 > i > -1000 for i in surrounds): #follow like paths (results in circles)
            #    ant_direction = np.argmin(surrounds) # set ant_direction to index of most negative surrounds value
            elif not is_fooding and any(0 > i > -1000 for i in surrounds): #move in direction of negative closest to 0
                ant_direction = np.argmax(np.where(surrounds < 0, surrounds, -np.inf))
            #if all of sees[0:3] are 1003, randomly choose an index from surrounds that is below 1000
            elif all(i == 1003 for i in sees[0:3]):
                ant_direction = np.random.choice(np.where(surrounds < 1000)[0])
            else:
                # one-third chance for the ant to turn left or right
                ant_direction = (ant_direction + np.random.choice([-1, 0, 1], p=[1/6, 2/3, 1/6])) % 8  # [1/8, 3/4, 1/8]
            # Calculate the new position based on the ant's current direction
            nx, ny = np.add([x,y], directions[ant_direction])
            # Check if the new position is valid
            if self.array[nx, ny] < 1000:
                # Update the ant's position
                self.array[x, y] = (-p_lvl if is_fooding else p_lvl) + self.array[nx, ny]
                self.array[x, y] = max(-255, min(255, self.array[x, y]))
                self.array[nx, ny] = ant_direction + (1010 if is_fooding else 1020)

        # Evaporate pheromones
        self.array[(0 < self.array) & (self.array < 1000)] -= 1
        self.array[0 > self.array] += 1

def scent_bubble(arr, center, radius=10, negative=False):
    center_y, center_x = center
    y_dim, x_dim = arr.shape
    for x in range(max(0, center_x-radius), min(x_dim, center_x+radius+1)):
        for y in range(max(0, center_y-radius), min(y_dim, center_y+radius+1)):
            if arr[y, x] > 1000 or (arr[y,x] > 0 and negative) or (arr[y,x]<0 and not negative):  # If the current point is an ant, skip it
                continue
            #dist = abs(x - center_x) + abs(y - center_y)
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)  # Euclidean distance
            if dist <= radius:
                value = int(dist)
                if negative:
                    arr[y, x] = min(arr[y, x], -value)
                else:
                    arr[y, x] = max(arr[y, x], value)
    return arr

if __name__ == '__main__':
    ant_array = AntArray()
    # Main simulation loop
    while True:
        ant_array.print_state()
        sleep(0.2)
        ant_array.update()
