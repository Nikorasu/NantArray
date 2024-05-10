#!/usr/bin/env python3
import numpy as np
from time import sleep
import os

'''
Rules for ant pheromone simulation within an array:
- Solid layer contains: empty-0, hive-1, food-2, walls-3, ants-10-17 (foodingAnt directions), 20-27 (homingAnt directions)
- Pheromone layers are uint8: 0-255 for food pheromones and hive pheromones
- Ants leave pheromones in the corresponding layer based on their mode (fooding or homing)
- Ants decide to move based on the spaces around them, ignoring the spot they're on and the spot "behind" the ant
- Each "round" ants move onto the space of their target pheromone with the lowest value, if multiple of those pheromones present
- Ants cannot move into spaces already occupied by other ants, the hive, food, or walls
- When a foodingAnt finds food, it changes to homingAnt, and homingAnts change back to foodingAnts when they find hive
- When target pheromones not detected, continue in same direction with occasional random variation +/- 1 (to avoid getting stuck in a corner)
- If only the non-targeted pheromone is present (in front), move towards strongest of that type, to hopefully follow similar-ants
- When an ant moves onto a spot with an existing pheromone, that value will be added to the pheromone the ant will leave behind it
'''
arrows = ('🡑', '🡕', '🡒', '🡖', '🡓', '🡗', '🡐', '🡔')  # for printing simulation state later, ants will be arrows indicating direction
symbols = {1: '\x1b[31;1m⭖\x1b[0m', 2: '\x1b[32;1m☘\x1b[0m', 3: '▒'}  # empty, hive, food, wall
directions = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))  # up, up-right, right, down-right, down, down-left, left, up-left
sim_size = (os.get_terminal_size().lines, os.get_terminal_size().columns)
p_lvl = 50  # initial strength-level of pheromones ants put out

class AntArray:

    def __init__(self, size=(*sim_size,3), num_ants=20, num_food=1, ant_radius=10, food_radius=sim_size[1]//2):
        # Initialize a 3D array
        self.array = np.zeros(size, dtype=np.uint8)
        # Place walls on edges of array on the first layer
        self.array[[0, -1], :, 0] = self.array[:, [0, -1], 0] = 3
        # Place hive into middle of array on the first layer
        hive_x, hive_y = size[0]//2, size[1]//4
        self.array[hive_x, hive_y, 0] = 1
        # calculate the distance from each point to the hive
        x_indices, y_indices = np.indices((size[0], size[1]))
        distances = np.sqrt((x_indices - hive_x)**2 + (y_indices - hive_y)**2)
        # place ants into array, randomly within ant_radius of the hive
        a_indices = np.argwhere((self.array[:, :, 0] == 0) & (distances <= ant_radius))
        a_chosen = a_indices[np.random.choice(a_indices.shape[0], num_ants, replace=False)]
        self.array[a_chosen[:, 0], a_chosen[:, 1], 0] = np.random.randint(10, 18, num_ants)
        #self.array[a_chosen[:, 0], a_chosen[:, 1], 1] = p_lvl  # not needed, update handles now
        # place food sources into array, randomly outside of food_radius from the hive
        f_indices = np.argwhere((self.array[:, :, 0] == 0) & (distances > food_radius))
        f_chosen = f_indices[np.random.choice(f_indices.shape[0], num_food, replace=False)]
        self.array[f_chosen[:, 0], f_chosen[:, 1], 0] = 2
    
    def print_state(self):
        output = ""
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
                    # merge the pheromone values into a single RGB color code
                    row_symbols.append(f'\x1b[48;2;{int(self.array[i, j, 1])};{int(self.array[i, j, 2])};0m \x1b[0m')
            output += ''.join(row_symbols) + "\n"
        print(output[:-1], end='\r')
    
    def scent_bubble(self, center, radius=10, layer=1):
        center_y, center_x = center
        y_dim, x_dim, _ = self.array.shape
        for x in range(max(0, center_x-radius), min(x_dim, center_x+radius+1)):
            for y in range(max(0, center_y-radius), min(y_dim, center_y+radius+1)):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)  # Euclidean distance
                if dist <= radius:
                    value = int(dist)
                    self.array[y, x, layer] = max(self.array[y, x, layer], value)
    
    def update(self):
        for hive in np.argwhere(self.array[:, :, 0] == 1):
            self.scent_bubble(hive, radius=15, layer=1)
        for efood in np.argwhere(self.array[:, :, 0] == 2):
            self.scent_bubble(efood, radius=10, layer=2)
        ant_indices = np.argwhere((self.array[:, :, 0] >= 10) & (self.array[:, :, 0] <= 27))
        for x, y in ant_indices:
            is_fooding = 10 <= self.array[x, y, 0] <= 17
            ant_direction = self.array[x, y, 0] % 10
            # Create a 3D surrounds array
            surrounds = np.zeros((8, 3))
            for i, (dx, dy) in enumerate(directions):
                if (dx, dy) != directions[(ant_direction + 4) % 8]: surrounds[i] = self.array[x + dx, y + dy]
            # Create a 1D sees array
            sees = np.zeros(8)
            sees[0] = surrounds[ant_direction, 0]  # What's in front of the ant first
            for offset in range(1, 4):  # Add elements with offsets of +/- 1, 2, 3 with wrap-around behavior
                sees[2*offset-1] = surrounds[(ant_direction + offset)%8, 0]
                sees[2*offset] = surrounds[(ant_direction - offset)%8, 0]
            if is_fooding and 2 in surrounds[:, 0]: #if fooding and food present, change to homing
                self.array[x, y, 0] = self.array[x, y, 0] + 10 #(self.array[x, y] % 10) + 20
                is_fooding = False
            elif not is_fooding and 1 in surrounds[:, 0]: #if homing and hive present, change to fooding
                self.array[x, y, 0] = self.array[x, y, 0] - 10 #(self.array[x, y] % 10) + 10
                is_fooding = True
            # Check if 3 or more values in surround's first layer are walls, and if they are, randomly choose one of the directions which is 0
            if np.sum(sees[:3] == 3) > 2:
                ant_direction = np.random.choice(np.where(surrounds[:, 0] == 0)[0])
            elif is_fooding and any(0 < i <= 255 for i in surrounds[:, 2]): #follow food phero in direction originated
                ant_direction = np.argmin(np.where(surrounds[:, 2] > 0, surrounds[:, 2], np.inf))
            elif not is_fooding and any(0 < i <= 255 for i in surrounds[:, 1]): #follow hive phero in direction originated
                ant_direction = np.argmin(np.where(surrounds[:, 1] > 0, surrounds[:, 1], np.inf))
            else: # one-third chance for the ant to turn left or right
                ant_direction = (ant_direction + np.random.choice([-1, 0, 1], p=[1/8, 3/4, 1/8])) % 8
            # Calculate the new position based on the ant's current direction
            nx, ny = np.add([x,y], directions[ant_direction])
            # Check if the new position is valid
            if self.array[nx, ny, 0] != 0:
                ant_direction = np.random.choice(np.where(surrounds[:, 0] == 0)[0])
                nx, ny = np.add([x,y], directions[ant_direction])
            if self.array[nx, ny, 0] == 0:
                # Update the ant's position
                self.array[x, y, 0] = 0
                self.array[nx, ny, 0] = ant_direction + (10 if is_fooding else 20)
                # Add pheromones to the layer corresponding to the ant's state
                self.array[x, y, 1 if is_fooding else 2] = min(255, self.array[x, y, 1 if is_fooding else 2] + p_lvl)
        # Evaporate pheromones
        mask = self.array[:, :, 1:3] > 0
        self.array[:, :, 1:3][mask] -= 1

if __name__ == '__main__':
    ant_array = AntArray()
    # Main simulation loop
    while True:
        ant_array.print_state()
        sleep(0.1)
        ant_array.update()