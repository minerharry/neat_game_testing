from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig
from baseGame import EvalGame, StarSmash
import os
import neat

game = EvalGame(StarSmash);
continueRun = False;
continueRunRun = 6;
newRun = False;
currentRun = 9;
reRun = True;
reRunGen = 251;
reRunRun = 8;
steps_threshold = 1000;
def getFitness(inputs):
    if (inputs.get('steps') > steps_threshold*3-1):
        return inputs.get('score')-(steps_threshold/2-inputs.get('steps'))/100 + 5;
    if (inputs.get('steps') > steps_threshold/2):
        return inputs.get('score')-(steps_threshold/2-inputs.get('steps'))/100;
    return inputs.get('score');
def getRunning(inputs):
    if ((inputs.get('steps') > steps_threshold) and (inputs.get('score')-(steps_threshold/2-inputs.get('steps'))/100 <= 0.2)):
        return False;
    if (inputs.get('steps') > steps_threshold*3):
        return False;
    return inputs.get('alive');

runConfig = RunnerConfig(getFitness,getRunning,parallel=True,returnData=['height','level','first_asteroid_height','first_asteroid_distance'],gameName='Star Smash',num_trials=75,num_generations=None);
runConfig.playback_fps = 10;

runner = GameRunner(game,runConfig);
if (continueRun):
    winner = runner.continue_run('run_' + str(continueRunRun));
    print('\nBest genome:\n{!s}'.format(winner));
else:
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-starsmash-gamerunner')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    if (newRun):
        winner = runner.run(config,'run_' + str(currentRun));
        print('\nBest genome:\n{!s}'.format(winner))
    if (reRun):
        runner.replay_best(reRunGen,config,'run_' + str(reRunRun),net=True);
