from __future__ import print_function

import visualize
import neat
import os
import random

NUM_TRIALS = 10


def eval_genomes(genomes,config):
  numNodes = config.genome_config.num_inputs
  inputs = randomInputs(NUM_TRIALS,numNodes);
  for genomeid, genome in genomes:
    net = neat.nn.FeedForwardNetwork.create(genome, config);
    fitnessSum = 0.0;
    for inputArray in inputs:
      outputs = net.activate(inputArray);
      fitnessSum += sum([abs(inputArray[i] + outputs[i])/2 for i in range(numNodes)])
    genome.fitness = fitnessSum / NUM_TRIALS;

def randomInputs(numInputs,numNodes):
  return [[random.randint(0,1)*2 - 1 for j in range(numNodes)] for i in range(numInputs)];

def run(config_file):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

        
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True));
    stats = neat.StatisticsReporter();
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5,filename_prefix='checkpoints\\reproduce_image\\feedforward-checkpoint-'))

    winner = p.run(eval_genomes, 300);

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)

    visualize.draw_net(config, winner, True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'photo_reproduction_config')
    run(config_path)
    
