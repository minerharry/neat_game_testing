from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig, IOData
from baseGame import EvalGame
from tetris import Tetris, TetrisRunnerConfig
import os
import neat

game = EvalGame(Tetris);
continueRun = False;
continueRunRun = 5;
newRun = False;
currentRun = 5;
reRun = True;
reRunGen = 90;
reRunRun = 5;
steps_threshold = 10000;

def getFitness(inputs):
    return inputs['cleared_lines']+(0.01*inputs['density'])+(0.00001 * inputs['steps']);

def getRunning(inputs):
    return inputs['is_alive'] and (inputs['steps']<steps_threshold);

runConfig = TetrisRunnerConfig(getFitness,getRunning,parallel=False,returnData=['piece_id','piece_x','piece_y','piece_rotation',IOData('contours','array',array_size=[10])],gameName='Tetris',num_trials=100,num_generations=None);
runConfig.playback_fps = 40;

runner = GameRunner(game,runConfig);
if (continueRun):
    winner = runner.continue_run('run_' + str(continueRunRun));
    print('\nBest genome:\n{!s}'.format(winner));
else:
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-tetris-gamerunner')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    if (newRun):
        winner = runner.run(config,'run_' + str(currentRun));
        print('\nBest genome:\n{!s}'.format(winner))
    if (reRun):
        runner.replay_best(reRunGen,config,'run_' + str(reRunRun),net=True,randomReRoll=True);
    #runner.check_output_connections(reRunGen,config,'run_' + str(reRunRun),0);
    #runner.render_genome_by_id(14074,reRunGen,config,'run_' + str(reRunRun),net=True);
