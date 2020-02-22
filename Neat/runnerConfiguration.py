import numpy as np


class RunnerConfig:

    def __init__(self,gameFitnessFunction,gameRunningFunction,logging=False,logPath='',recurrent=False,trial_fitness_aggregation='average',custom_fitness_aggregation=None,time_step=0.05,num_trials=10,parallel=False,returnData=[],gameName='game',num_generations=300,fitness_collection_type=None):

        self.logging = logging;
        self.logPath = logPath;
        self.generations = num_generations;
        self.recurrent = recurrent;
        self.gameName = gameName;
        self.parallel = parallel;
        self.time_step = time_step;
        self.numTrials = num_trials;
        self.fitnessFromGameData = gameFitnessFunction;
        self.gameStillRunning = gameRunningFunction;
        self.fitness_collection_type = fitness_collection_type;

        self.returnData = returnData;
##        for (datum in returnData):
##            if (isinstance(datum,IOData)):
##                [returnData.append(x) for x in datum.getSplitData()];
##            else:
##                returnData.append(datum);
##        
        if (trial_fitness_aggregation == 'custom'):
            self.fitnessFromArray = custom_fitness_aggregation;

        if (trial_fitness_aggregation == 'average'):
            self.fitnessFromArray = lambda fitnesses : sum(fitnesses)/len(fitnesses);

        if (trial_fitness_aggregation == 'max'):
            self.fitnessFromArray = lambda fitnesses : max(fitnesses);

        if (trial_fitness_aggregation == 'min'):
            self.fitnessFromArray = lambda fitnesses : min(fitnesses);

    def flattened_return_data(self):
        result = [];
        for datum in self.returnData:
            if (isinstance(datum,IOData)):
                [result.append(x) for x in datum.getSplitData()];
            else:
                result.append(datum);
        print(result);
        return result;

    def return_data_shape(self):
        result = [];
        for datum in self.returnData:
            if (isinstance(datum,IOData)):
                result.append(datum.toNamedArray());
                print('name array of {0}: {1}'.format(datum,datum.toNamedArray()));
            else:
                result.append(datum);
        return result;          
                


def get_array_cell_names(array_size):
    if (len(array_size) == 1):
        return [str(i) for i in range(array_size[0])];
    return [str(i) + '-' + j for i in range(array_size[0]) for j in get_array_cell_names(array_size[1:])];

class IOData:
    convertable_types = [list];
    
    def __init__(self,name,data_type,array_size=None):
        self.data_type = data_type;
        self.name = name;
        self.array_size = array_size;
        
    def getSplitData(self):
        if (self.data_type == 'float'):
            return [self.name];
        if (self.data_type in ['array','ndarray']):
            return [self.name + ' ' + x for x in get_array_cell_names(self.array_size)];

    def toNamedArray(self):
        return self.toNameArray(self.name,self.array_size,' ');

    def toNameArray(self,name,shape,splitterChar):
        result = [];
        if (len(shape) == 1):
            for i in range(shape[0]):
                result.append(str(name) + splitterChar + str(i));
        else:
            for i in range(shape[0]):
                result.append(self.toNameArray(str(name) + splitterChar + str(i),shape[1:],'-'));
        print(result);
        return (name,result);

    @staticmethod
    def convertableType(datum):
        for convertType in convertable_types:
            if (isinstance(datum,convertType)):
                return true;
        return false;

    @classmethod
    def datify(cls,datum,name):
        if (isinstance(datum,list)):
            return;



