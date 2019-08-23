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
##        #print('processing');
##        self.env.ram[0x0773] = 0x02;
##        self.env.ram[0x074E] = 0x01;
##        #print(self.env.ram[0x0744]);
##        self.env.ram[0x000F] = 0x00;
##        array = ([[self.env.ram[16*i+j+0x0500] for j in range(16)] for i in range (13)]);
##        #[print(array[i]) for i in range(len(array))];
##        array = ([[self.env.ram[16*i+j+0x05D0] for j in range(16)] for i in range (13)]);
##        #[print(array[i]) for i in range(len(array))];
##        #print(len(array));
##        self.env.ram[0x0744] = 0x0F;
##        #self.env.ram[0x05C0] = 43;
##        print("page left: ",self.env.ram[0x071a]);
##        print("page right: ",self.env.ram[0x071b]);
##        #print("screen left: ",self.env.ram[0x071c]);
##        #print("6b: ",self.env.ram[0x6b]);
##        #print("mario x: ",self.env.ram[0x071c] + self.env.ram[0x86]);
##        #print("mario block: ",(self.env.ram[0x071c] + self.env.ram[0x86])/16);
##        print("mario x 2: ", self.env.ram[0x6d]*0x100 + self.env.ram[0x86]);
##        print("mario block 2: ",(self.env.ram[0x6d]*0x100 + self.env.ram[0x86])/16);
##        #print("mario vLow: ",self.env.ram[0x00b5]);
##        #print("mario vHi: ",self.env.ram[0x00ce]);
##        #print("mario vRel: ",self.env.ram[0x03b8]);
##        
        state, reward, done, info = self.env.step(self.do_action_function(inputs));
        #print(info);
##        [print(info['blocks'][i]) for i in range(len(info['blocks']))];
##        if (self.env.ram[0x00CE] > 20):
##            self.env.ram[0x00CE] = 0;
        #self.env.render();
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
        self.processInput(inputs);
        self.env.render();
        return Image.fromarray(self.state);
        
   
