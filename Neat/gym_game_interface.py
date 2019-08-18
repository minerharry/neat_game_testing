import baseGame.RunGame
from nes_py.wrappers import JoypadSpace
from runnerConfiguration import RunnerConfig
from PIL import Image

button_map = {
        'right':  0b10000000,
        'left':   0b01000000,
        'down':   0b00100000,
        'up':     0b00010000,
        'start':  0b00001000,
        'select': 0b00000100,
        'B':      0b00000010,
        'A':      0b00000001,
        'NOOP':   0b00000000,
    }

class GymRunnerConfig(RunnerConfig):
    def __init__(self,
                 gameFitnessFunction,
                 gameRunningFunction=None,
                 recurrent=False,
                 trial_fitness_aggregation='average',
                 custom_fitness_aggregation=None,
                 time_step=0.05,
                 num_trials=10,
                 parallel=False,
                 returnData=[],
                 gameName='gym_game',
                 num_generations=300,
                 gym_action_function=None):
        super().__init__(gameFitnessFunction,
                         gameRunningFunction,
                         recurrent,
                         trial_fitness_aggregation,
                         custom_fitness_aggregation,
                         time_step,
                         num_trials,
                         returnData,
                         gameName,
                         num_generations);
        self.action_function = gym_action_function;

class NESGymRunnerConfig(GymRunnerConfig):
    def __init__(self,
                 gameFitnessFunction,
                 gameRunningFunction=None,
                 recurrent=False,
                 trial_fitness_aggregation='average',
                 custom_fitness_aggregation=None,
                 time_step=0.05,
                 num_trials=10,
                 parallel=False,
                 returnData=[],
                 gameName='gym_game',
                 num_generations=300,
                 gym_action_function=None,
                 used_buttons=['right','left','down','up','b','a']):
        super().__init__(gameFitnessFunction,
                         gameRunningFunction,
                         recurrent,
                         trial_fitness_aggregation,
                         custom_fitness_aggregation,
                         time_step,
                         num_trials,
                         returnData,
                         gameName,
                         num_generations,
                         gym_action_function);
        self.used_buttons = used_buttons;
        
class GymEnvGame(baseGame.RunGame):
    def __init__(self,runnerConfig,kwargs):
        
        self.env = kwargs['env'];
        self.runConfig = runnerConfig;

    def processInput(self, inputs):
        state, reward, done, info = self.env.step(self.do_action_function(inputs));
        self.info = info;
        self.info['done'] = done;
        self.done = done;
        self.state = state;

    def do_action_function(self,inputs):
        if (self.runConfig.action_function == None):
            return self.gym_action_function(inputs);
        return self.runConfig.action_function(inputs);

    def gym_action_function(self,inputs):
        raise NotImplementedError();

    def isRunning(self):
        if (self.runConfig.gameStillRunning != None):
            return self.runConfig.gameStillRunning(self.getMappedData());
        return self.done;

    def close(self):
        self.env.reset();

    def getOutputData(self):
        return self.info;

class NesPyGymGame(GymEnvGame):
    def __init__(self,runnerConfig,env):
        super().__init__(runnerConfig,env);

    def gym_action_function(self,inputs):
        used_buttons = button_map.keys();
        if (self.runConfig.used_buttons != None):
            used_buttons = self.runConfig.used_buttons;
        inputs = dict(zip(used_buttons,inputs));
        action_int = 0;
        for name,val in inputs:
            if (val > 0):
                action_int |= button_map[name];
        return action_int;

    def render_input(self,inputs):
        self.process_input(inputs);
        return Image.fromarray(self.state);
        
   
