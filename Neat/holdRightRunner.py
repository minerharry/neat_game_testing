from game_runner_neat import GameRunner 
from runnerConfiguration import RunnerConfig
from baseGame import EvalGame, HoldRightGame
import os
import neat

game = EvalGame(HoldRightGame);

runConfig = RunnerConfig(lambda inputs:inputs.get('position'),lambda inputs:inputs.get('steps') < 150,returnData=['position'],gameName='Hold Right to Win');
runConfig.rightCoeff = 1.0;
runConfig.animation_pixel_per_unit = 20;
runConfig.animation_unit_per_sign = 5;
runConfig.playback_fps = 30;

runner = GameRunner(game,runConfig);

local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'config-gamerunner')
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

winner = runner.run(config,'run_2');
print('\nBest genome:\n{!s}'.format(winner))


runner.render_genome(winner,config);
