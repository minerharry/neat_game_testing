from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig, IOData
from baseGame import EvalGame
from gym_game_interface import NESGymRunnerConfig,NesPyGymGame
import os
import neat
import gym_super_mario_bros

smb1Env = gym_super_mario_bros.make('SuperMarioBros-v0')
smb1Env.reset();
game = EvalGame(NesPyGymGame,env=smb1Env);
continueRun = False;
continueRunRun = 0;
newRun = True;
currentRun = 0;
reRun = False;
reRunGen = 8;
reRunRun = 1;
steps_threshold = 400;


def getFitness(inputs):
    return inputs['gym-reward'];

def getRunning(inputs):
    return (not(inputs['done']) and (not inputs['stillness_time'] > steps_threshold));


runConfig = NESGymRunnerConfig(getFitness,getRunning,parallel=False,gameName='gym_nes_smb1',returnData=['stage','status','world','x_pos','y_pos',IOData('enemy_type','array',array_size=[5]),IOData('enemy_x','array',array_size=[5]),IOData('enemy_y','array',array_size=[5]),IOData('blocks','array',array_size=[8,8]),'powerup_x','powerup_y'],num_trials=1,num_generations=None);
runConfig.playback_fps = 20;
runConfig.fitness_collection_type='continuous'
print(runConfig.gameName);

runner = GameRunner(game,runConfig);
if (continueRun):
    winner = runner.continue_run('run_' + str(continueRunRun));
    print('\nBest genome:\n{!s}'.format(winner));
else:
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-gym-nes-smb1')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    if (newRun):
        winner = runner.run(config,'run_' + str(currentRun));
        print('\nBest genome:\n{!s}'.format(winner))
    if (reRun):
        runner.replay_best(reRunGen,config,'run_' + str(reRunRun),net=True,randomReRoll=True);
