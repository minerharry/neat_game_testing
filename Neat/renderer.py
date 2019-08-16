from neat.reporting import BaseReporter

class Renderer(BaseReporter):

    def __init__(self,runner):
        self.runner = runner;

    def post_evaluate(self,config, population, species,best):
        self.runner.render_genome(best,config);
        return;

    
