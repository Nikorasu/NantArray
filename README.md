# NantArray

An array-based cellular-automata implementation of my ant pheromone simulation!

WIP

Instead of using a game engine like Pygame to simulate things, this time I've
coded things entirely using Numpy arrays!

My first version attempted to do everything on a single array layer, which ran
but not well, as pheromones couldn't overlap much. Ants always got lost.

The next version split things off onto separate array layers, going from a 2d
array, to a 3d one. And that works, but Ants still weren't following very well.

Currently I'm working on `antarray_alt.pt`. In this version, I inverted the
pheromone strength on the scent bubbles, and tweaked the rules a bit further.
Ants still don't follow quite good enough yet, to form efficient paths. But it
is starting to show signs of the behaviors I saw in my older simulations.

For now I will continue tweaking the rules, until it works more like it should.
If else manages to get it working better, please share, I'd love to see it! :)