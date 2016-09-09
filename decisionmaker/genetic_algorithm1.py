'''
Assesses the log file and checks how the parameters in strategies.xml need to be adjusted to optimize playing
'''
from debug_logger import *
from mongo_manager import *


class GeneticAlgorithm(object):
    def __init__(self, write_update, logger, L):
        self.logger = logger
        self.output = ''
        p = StrategyHandler()
        p.read_strategy()
        p_name = p.current_strategy
        logger.debug("Strategy to analyse: "+p_name)
        self.load_log(p_name, L)
        self.improve_strategy(L, p)
        if (p.modified and write_update==True) or write_update=="Force":
            p.save_strategy()
            config = ConfigObj("config.ini")
            config['last_strategy'] = p.current_strategy
            config.write()
            self.logger.info("Genetic algorithm: New strategy saved")

    def get_results(self):
        return self.output

    def load_log(self, p_name, L):
        self.gameResults = {}
        L.get_stacked_bar_data('Template', p_name, 'stackedBar')
        self.recommendation = dict()

    def assess_call(self, p, L, decision, stage, coeff1, coeff2, coeff3, coeff4, change):
        A = L.d[decision, stage, 'Won'] > L.d[decision, stage, 'Lost'] * coeff1  # Call won > call lost * c1
        B = L.d[decision, stage, 'Lost'] > L.d['Fold', stage, 'Lost'] * coeff2  # Call Lost > Fold lost
        C = L.d[decision, stage, 'Won'] + L.d['Bet', stage, 'Won'] < L.d[
                                                                         'Fold', stage, 'Lost'] * coeff3  # Fold Lost*c3 > Call won + bet won
        if A and B:
            self.recommendation[stage, decision] = "ok"
        elif A and B == False and C:
            self.recommendation[stage, decision] = "more agressive"
            p.modify_strategy(stage + 'MinCallEquity', -change)
            p.modify_strategy(stage + 'CallPower', -change * 25)
            self.changed += 1
        elif A == False and B == True:
            self.recommendation[stage, decision] = "less agressive"
            p.modify_XML(stage + 'MinCallEquity', +change)
            p.modify_XML(stage + 'CallPower', +change * 25)
            self.changed += 1
        else:
            self.recommendation[stage, decision] = "inconclusive"
        self.logger.info(stage + " " + decision + ": " + self.recommendation[stage, decision])
        self.output += stage + " " + decision + ": " + self.recommendation[stage, decision] + '\n'

    def assess_bet(self, p, L, decision, stage, coeff1, change):
        A = L.d['Bet', stage, 'Won'] > (L.d['Bet', stage, 'Lost']) * coeff1  # Bet won bigger Bet lost
        B = L.d['Check', stage, 'Won'] > L.d['Check', stage, 'Lost']  # check won bigger check lost
        C = L.d['Bet', stage, 'Won'] < (L.d['Bet', stage, 'Lost']) * 1  # Bet won bigger Bet lost

        if A and not B:
            self.recommendation[stage, decision] = "ok"
        elif A and B:
            self.recommendation[stage, decision] = "more agressive"
            p.modify_strategy(stage + 'MinBetEquity', -change)
            p.modify_strategy(stage + 'BetPower', -change * 25)
            self.changed += 1
        elif C and not B:
            self.recommendation[stage, decision] = "less agressive"
            p.modify_XML(stage + 'MinBetEquity', +change)
            p.modify_XML(stage + 'BetPower', +change * 25)
            self.changed += 1
        else:
            self.recommendation[stage, decision] = "inconclusive"
        self.logger.info(stage + " " + decision + ": " + self.recommendation[stage, decision])
        self.output += stage + " " + decision + ": " + self.recommendation[stage, decision] + '\n'

    def improve_strategy(self, L, p):
        self.changed = 0
        maxChanges = 2
        if self.changed <= maxChanges:
            coeff1 = 2
            coeff2 = 1
            coeff3 = 2
            coeff4 = 1
            stage = 'River'
            decision = 'Call'
            change = 0.02
            self.assess_call(p, L, decision, stage, coeff1, coeff2, coeff3, coeff4, change)

        if self.changed < maxChanges:
            coeff1 = 2
            coeff2 = 1.5
            coeff3 = 2
            stage = 'Turn'
            decision = 'Call'
            change = 0.02
            self.assess_call(p, L, decision, stage, coeff1, coeff2, coeff3, coeff4, change)

        if self.changed < maxChanges:
            coeff1 = 2
            coeff2 = 1.5
            coeff3 = 2
            stage = 'Flop'
            decision = 'Call'
            change = 0.01
            self.assess_call(p, L, decision, stage, coeff1, coeff2, coeff3, coeff4, change)

        if self.changed < maxChanges:
            coeff1 = 2
            coeff2 = 2.5
            coeff3 = 2
            stage = 'PreFlop'
            decision = 'Call'
            change = 0.03
            self.assess_call(p, L, decision, stage, coeff1, coeff2, coeff3, coeff4, change)

        self.changed = 0
        if self.changed < maxChanges:
            coeff1 = 2
            stage = 'River'
            decision = 'Bet'
            change = 0.02
            self.assess_bet(p, L, decision, stage, coeff1, change)

        if self.changed < maxChanges:
            coeff1 = 2
            stage = 'Turn'
            decision = 'Bet'
            change = 0.02
            self.assess_bet(p, L, decision, stage, coeff1, change)

        if self.changed < maxChanges:
            coeff1 = 2
            stage = 'Flop'
            decision = 'Bet'
            change = 0.02
            self.assess_bet(p, L, decision, stage, coeff1, change)

        if self.changed < maxChanges:
            coeff1 = 2
            stage = 'PreFlop'
            decision = 'Bet'
            change = 0.02
            self.assess_bet(p, L, decision, stage, coeff1, change)


def run_genetic_algorithm(write, logger):
    logger.info("===Running genetic algorithm===")
    L = GameLogger()
    GeneticAlgorithm(write, logger, L)


if __name__ == '__main__':
    import logging

    logger = logging
    logger.basicConfig(level=logging.DEBUG)
    run_genetic_algorithm(False, logger)

    user_input = input("Run again and modify (Y)=Force / N? ")
    if user_input.upper() == "Y":
        run_genetic_algorithm("Force", logger)
