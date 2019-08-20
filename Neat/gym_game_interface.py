from baseGame import RunGame
from nes_py.wrappers import JoypadSpace
from runnerConfiguration import RunnerConfig, IOData
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
                         recurrent=recurrent,
                         trial_fitness_aggregation=trial_fitness_aggregation,
                         custom_fitness_aggregation=custom_fitness_aggregation,
                         time_step=time_step,
                         num_trials=num_trials,
                         returnData=returnData,
                         gameName=gameName,
                         num_generations=num_generations);
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
                 used_buttons=['right','left','down','up','B','A']):
        super().__init__(gameFitnessFunction,
                         gameRunningFunction=gameRunningFunction,
                         recurrent=recurrent,
                         trial_fitness_aggregation=trial_fitness_aggregation,
                         custom_fitness_aggregation=custom_fitness_aggregation,
                         time_step=time_step,
                         num_trials=num_trials,
                         returnData=returnData,
                         gameName=gameName,
                         num_generations=num_generations,
                         gym_action_function=gym_action_function);
        self.used_buttons = used_buttons;
        
class GymEnvGame(RunGame):
    def __init__(self,runnerConfig,kwargs):
        super().__init__(runnerConfig,kwargs);
        self.done = False
        self.info = {};
        self.env = kwargs['env'];
        self.runConfig = runnerConfig;
        self.processInput([]);

    def processInput(self, inputs):
        #print('processing');
        state, reward, done, info = self.env.step(self.do_action_function(inputs));
        #print(info);
        self.env.render();
        self.info = info;
        self.info['done'] = done;
        self.info['gym-reward'] = reward;
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
        return not(self.done);

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
       # print(inputs);
        for name, val in inputs.items():
            if (val > 0):
                action_int |= button_map[name];
        return action_int;


    def renderInput(self,inputs):
        self.process_input(inputs);
        return Image.fromarray(self.state);
        
   
