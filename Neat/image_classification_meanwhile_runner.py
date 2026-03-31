from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig, IOData
from baseGame import EvalGame
from image_classification import ImageClassification
from digit_data import mnist_loader
import os
import neat


imageset_size = 2000;
imageset = mnist_loader.load_data()[0];
imageset = (imageset[0][:imageset_size+2],imageset[1][:imageset_size+2]);

game = EvalGame(ImageClassification,images=imageset);
continueRun = False;
continueRunRun = 0;
newRun = False;
currentRun = 1;
reRun = True;
reRunGen = 289;
reRunRun = 1;

def getFitness(inputs):
    return (1 if inputs['digit'] == inputs['best_digit'] else 0);

def getRunning(inputs):
    return inputs['steps'] <= imageset_size;


runConfig = RunnerConfig(getFitness,getRunning,parallel=False,gameName='image_classification',
                         returnData=[IOData('image','ndarray',array_size=[784])],num_trials=1,num_generations=None);
runConfig.logging = True;
runConfig.logPath = f'logs\\image-classification\\run-{currentRun}-log.txt';
runConfig.playback_fps = 20;
runConfig.fitness_collection_type='continuous'
print(runConfig.gameName);

runner = GameRunner(game,runConfig);
if (continueRun):
    winner = runner.continue_run('run_' + str(continueRunRun));
    print('\nBest genome:\n{!s}'.format(winner));
else:
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-image-classification')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    #runner.render_worst_genome(reRunGen,config,'run_' + str(reRunRun),net=True);
    
    if (newRun):
        winner = runner.run(config,'run_' + str(currentRun));
        print('\nBest genome:\n{!s}'.format(winner))
    if (reRun):
        #runner.render_genome_by_id(626,reRunGen,config,'run_' + str(reRunRun),net=True);

        runner.replay_best(reRunGen,config,'run_' + str(reRunRun),net=True,randomReRoll=True);
