import neat
import baseGame
import runnerConfiguration
import os.path
import os
import visualize
import random
import concurrent.futures
from renderer import Renderer as RendererReporter
from videofig import videofig as vidfig
from neat.six_util import iteritems, itervalues



#requires get_genome_frame.images to be set before call
def get_genome_frame(f,axes):
    images = get_genome_frame.images;
    if not get_genome_frame.initialized:
        get_genome_frame.im = axes.imshow(images[f],animated=True);
        get_genome_frame.initialized = True;
    else:
        get_genome_frame.im.set_array(images[f]);
            
class GameRunner:

    #if using default version, create basic runner and specify game to run
    def __init__(self,game,runnerConfig):
        self.game = game;
        self.runConfig = runnerConfig;

    def continue_run(self,run_name,render=False):
        checkpoint_folder = 'checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_');
        files = os.listdir(checkpoint_folder);
        maxGen = -1;
        for file in files:
            if (int(file.split('run-checkpoint-')[1])>maxGen):
                maxGen = int(file.split('run-checkpoint-')[1]);
        pop = neat.Checkpointer.restore_checkpoint(checkpoint_folder + '\\run-checkpoint-' + str(maxGen));

        return self.run(pop.config,run_name,render=render,pop=pop);

    def run(self,config,run_name,render=False,pop=None):
        if (pop is None):
            pop = neat.Population(config);
            continuing = False;
        else:
            continuing = True;
        stats = neat.StatisticsReporter();
        pop.add_reporter(stats);
        pop.add_reporter(neat.StdOutReporter(True));

        if (not(os.path.exists('checkpoints'))):
            os.mkdir('checkpoints');
        if (not(os.path.exists('checkpoints\\games'))):
            os.mkdir('checkpoints\\games');
        if (not(os.path.exists('checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')))):
            os.mkdir('checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_'));
        if (not(os.path.exists('checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')))):
            os.mkdir('checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_'));
        
        pop.add_reporter(neat.Checkpointer(1,filename_prefix='checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')+'\\run-checkpoint-'));

        if (render):
            pop.add_reporter(RendererReporter(self));
        if (continuing):
            pop.complete_generation();
        
        winner = pop.run(self.eval_genomes,self.runConfig.generations);

        return winner;

    def check_output_connections(self,generation,config,run_name,target_output,render=False):
        file = 'checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')+'\\run-checkpoint-' + str(generation);
        pop = neat.Checkpointer.restore_checkpoint(file);
        connected = [];
        for g in itervalues(pop.population):
            for connection in g.connections:
                if (connection[1] == target_output):
                    connected.append(g);
                    break;
        [print (connectedGenome) for connectedGenome in connected];

    def render_worst_genome(self,generation,config,run_name,net=False):
        file = 'checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')+'\\run-checkpoint-' + str(generation);
        pop = neat.Checkpointer.restore_checkpoint(file);
        worst = None
        for g in itervalues(pop.population):
            if worst is None or g.fitness < worst.fitness:
                worst = g
        self.render_genome_by_id(worst.key,generation,config,run_name,net=net);

    def render_genome_by_id(self,genomeId,generation,config,run_name,net=False):
        file = 'checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')+'\\run-checkpoint-' + str(generation);
        pop = neat.Checkpointer.restore_checkpoint(file);
        genome = None;
        for g in itervalues(pop.population):
            if g.key == genomeId:
                genome = g;
                break;
        self.render_genome(genome,config,net=net);
                    
                

    def replay_best(self,generation,config,run_name,net=False,randomReRoll=False):
        file = 'checkpoints\\games\\'+self.runConfig.gameName.replace(' ','_')+'\\'+run_name.replace(' ','_')+'\\run-checkpoint-' + str(generation);
        pop = neat.Checkpointer.restore_checkpoint(file);
        #self.eval_genomes(list(iteritems(pop.population)),config);
        if (randomReRoll):
            random.seed();
        best = None
        for g in itervalues(pop.population):
            if best is None or g.fitness > best.fitness:
                best = g
        print(best);
        self.render_genome(best,config,net=net);
        

    def render_genome(self,genome,config,net=False):
        if (self.runConfig.recurrent):
            self.render_genome_recurrent(genome,config,net=net);
        else:
            self.render_genome_feedforward(genome,config,net=net);



    #render a genome with the game as a recurrent neural net
    def render_genome_recurrent(self, genome, config,net=False):
        runnerConfig = self.runConfig;
        time_const = runnerConfig.time_step;

        if (net):
            flattened_data = runnerConfig.flattened_return_data();
            shaped_data = runnerConfig.return_data_shape();
            visualize.draw_net(config,genome,view=True,node_names=dict([(-i-1,flattened_data[i]) for i in range(len(flattened_data))]),nodes_shape=shaped_data);
            
        if (runnerConfig.parallel and False):
            return;
            #TODO: implement parallel game processing
        else:
            net = neat.ctrnn.CTRNN.create(genome,config,time_const);
            runningGame = self.game.start(runnerConfig);
            images = [];
            while (runningGame.isRunning()):
                    #get the current inputs from the running game, as specified by the runnerConfig
                gameData = runningGame.getData();

                gameInput = net.advance(gameData, time_const, time_const);

                images.append(runningGame.renderInput(gameInput));

                        
            runningGame.close();
            get_genome_frame.images = images;
            get_genome_frame.initialized = False;
            vidfig(len(images),get_genome_frame,play_fps=runnerConfig.playback_fps);

        

    #render a genome with the game as a feedforward neural net
    def render_genome_feedforward(self, genome, config,net=False):
        runnerConfig = self.runConfig;
        if (net):
            flattened_data = runnerConfig.flattened_return_data();
            shaped_data = runnerConfig.return_data_shape();
            visualize.draw_net(config,genome,view=True,node_names=dict([(-i-1,flattened_data[i]) for i in range(len(flattened_data))]),nodes_shape=shaped_data);
            
            
        if (runnerConfig.parallel and False):
            return;
            #TODO: implement parallel game processing
        else:
            
            net = neat.nn.FeedForwardNetwork.create(genome,config);
            runningGame = self.game.start(runnerConfig);
            images = [];
            while (runningGame.isRunning()):
                #get the current inputs from the running game, as specified by the runnerConfig
                gameData = runningGame.getData();

                gameInput = net.activate(gameData);

                images.append(runningGame.renderInput(gameInput));

                        
            runningGame.close();
            get_genome_frame.images = images;
            get_genome_frame.initialized = False;
            vidfig(len(images),get_genome_frame,play_fps=runnerConfig.playback_fps);

            
    def eval_genomes(self,genomes,config):
        if (self.runConfig.recurrent):
            self.eval_genomes_recurrent(genomes,config);
        else:
            self.eval_genomes_feedforward(genomes,config);
    

    #evaluate a population with the game as a recurrent neural net
    def eval_genomes_recurrent(self, genomes, config):
        runnerConfig = self.runConfig;
        time_const = runnerConfig.time_step;
        if (runnerConfig.parallel):
            return;
            #TODO: implement parallel game processing
        else:
            for genome_id, genome in genomes:
                net = neat.ctrnn.CTRNN.create(genome,config,time_const);
                fitnesses = [];
                for trial in range(runnerConfig.numTrials):
                    
                    runningGame = self.game.start(runnerConfig);
                    fitness = 0;
                    while (runningGame.isRunning()):
                        #get the current inputs from the running game, as specified by the runnerConfig
                        gameData = runningGame.getData();

                        gameInput = net.advance(gameData, time_const, time_const);

                        runningGame.processInput(gameInput);
                        if (runnerConfig.fitness_collection_type != None and runnerConfig.fitness_collection_type == 'continuous'):
                            fitness += runningGame.getFitnessScore();
                    fitness += runningGame.getFitnessScore();
                    fitnesses.append(fitness);
                    runningGame.close();
                fitness = runnerConfig.fitnessFromArray(fitnesses);
                genome.fitness = fitness;
        

    #evaluate a population with the game as a feedforward neural net
    def eval_genomes_feedforward(self, genomes, config):
        if (self.runConfig.parallel):
            executor = concurrent.futures.ThreadPoolExecutor();
            futures = [executor.submit(self.eval_genome_feedforward,genome,config) for genome_id,genome in genomes];
            concurrent.futures.wait(futures);
            return;
        else:
            for genome_id, genome in genomes:
                self.eval_genome_feedforward(genome,config)

    def eval_genome_feedforward(self,genome,config):
        #print('genome evaluation triggered');
        runnerConfig = self.runConfig;
        net = neat.nn.FeedForwardNetwork.create(genome,config);
        fitnesses = [];
        for trial in range(runnerConfig.numTrials):
            #print('evaluating genome with id {0}, trial {1}'.format(genome.key,trial));
            fitness = 0;
            runningGame = self.game.start(runnerConfig);
            while (runningGame.isRunning()):
                #get the current inputs from the running game, as specified by the runnerConfig
                gameData = runningGame.getData();

                #print('input: {0}'.format(gameData));
                gameInput = net.activate(gameData);

                
                runningGame.processInput(gameInput);

                if (runnerConfig.fitness_collection_type != None and runnerConfig.fitness_collection_type == 'continuous'):
                    fitness += runningGame.getFitnessScore();
                    
            fitness += runningGame.getFitnessScore();
            fitnesses.append(fitness);
            runningGame.close();

        fitness = runnerConfig.fitnessFromArray(fitnesses);
        genome.fitness = fitness;
        #print(genome.fitness);



        
