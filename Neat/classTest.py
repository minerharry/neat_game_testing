from baseGame import EvalGame, HoldRightGame
from runnerConfiguration import RunnerConfig

config = RunnerConfig(lambda inputs: inputs.get('position'),lambda inputs:inputs.get('steps') < 100, returnData=['position']);
config.rightCoeff =10;

gameBase = EvalGame(HoldRightGame);

runningGame = gameBase.start(config);

print(runningGame.getData());

runningGame.processInput([1]);

print(runningGame.getData());

runningGame.close();

print(runningGame.getFitnessScore());
