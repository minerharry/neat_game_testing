from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig, IOData
from baseGame import EvalGame
from dinosaur_game import DinosaurGame
import os
import neat

game = EvalGame(DinosaurGame);
continueRun = True;
newRun = False;
reRun = False;
run = 4;

reRunGen = 50;

max_length = 100000;

def getFitness(inputs):
    return inputs['steps']

def getRunning(inputs):
    return not inputs['dead'] and inputs['steps'] < max_length;
game_name = 'dinosaur_game'


runConfig = RunnerConfig(getFitness,getRunning,parallel=False,gameName=game_name,
                         returnData=['yPos','speed',IOData('near_obstacles','array',array_size=[3,4])],num_trials=20,num_generations=None);
runConfig.logging = True;
runConfig.logPath = f'logs\\{game_name}\\run-{run}-log.txt';
runConfig.playback_fps = 20;
print(runConfig.gameName);

runner = GameRunner(game,runConfig);
if (continueRun):
    winner = runner.continue_run('run_' + str(run));
    print('\nBest genome:\n{!s}'.format(winner));
else:
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-dinosaur-runner')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    #runner.render_worst_genome(reRunGen,config,'run_' + str(reRunRun),net=True);
    
    if (newRun):
        winner = runner.run(config,'run_' + str(run));
        print('\nBest genome:\n{!s}'.format(winner))
    if (reRun):
        runner.replay_best(reRunGen,config,'run_' + str(run),net=True,randomReRoll=True);
