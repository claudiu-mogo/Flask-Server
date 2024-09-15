""" Process and store the data, providing methods to compute means """

import csv

class DemoIngestor:
    """ Parse the csv and provide necessary methods """

    def __init__(self, csv_path: str):
        # Read csv from csv_path

        # Format like: keys=question, having as value a sub-dictionary
        # Subdictionary: keys=location, values: list of tuples (value, stratif, category)
        self.all_questions = {}

        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)

            # Read the headers from the first line and save the relevant ones
            headers = next(reader)
            self.__QUESTION = headers.index("Question")
            self.__LOCATION = headers.index("LocationDesc")
            self.__VALUE = headers.index("Data_Value")
            self.__STRAT1 = headers.index("Stratification1")
            self.__STRAT_CAT1 = headers.index("StratificationCategory1")

            # Read the data per se
            for entry in reader:
                question = entry[self.__QUESTION]
                location = entry[self.__LOCATION]
                val = entry[self.__VALUE]
                strat1 = entry[self.__STRAT1]
                strat_cat1 = entry[self.__STRAT_CAT1]

                # convert to float
                val = float(val)

                # check new question
                if question not in self.all_questions:
                    self.all_questions[question] = {}
                    self.all_questions[question][location] = []

                # check new location for an existent question
                elif location not in self.all_questions[question]:
                    self.all_questions[question][location] = []

                # add the (value, stratif, category) to list for that <question, location> pair
                self.all_questions[question][location].append((val, strat1, strat_cat1))


        self.questions_best_is_min = [
            'Percent of adults aged 18 years and older who have an overweight classification',
            'Percent of adults aged 18 years and older who have obesity',
            'Percent of adults who engage in no leisure-time physical activity',
            'Percent of adults who report consuming fruit less than one time daily',
            'Percent of adults who report consuming vegetables less than one time daily'
        ]

        self.questions_best_is_max = [
            'Percent of adults who achieve at least 150 minutes a week of moderate-intensity aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic activity (or an equivalent combination)',
            'Percent of adults who achieve at least 150 minutes a week of moderate-intensity aerobic physical activity or 75 minutes a week of vigorous-intensity aerobic physical activity and engage in muscle-strengthening activities on 2 or more days a week',
            'Percent of adults who achieve at least 300 minutes a week of moderate-intensity aerobic physical activity or 150 minutes a week of vigorous-intensity aerobic activity (or an equivalent combination)',
            'Percent of adults who engage in muscle-strengthening activities on 2 or more days a week',
        ]

    def get_global_mean(self, question):
        """ Iterate through all possible Data_Values and compute mean """
        count = 0
        total_sum = 0
        for val_list in self.all_questions[question].values():
            for val in val_list:
                val = val[0]
                count += 1
                total_sum += val
        return total_sum / count

    def get_state_mean(self, question, state):
        """ Iterate through all possible Data_Values for that state and compute mean """
        count = 0
        total_sum = 0
        for val in self.all_questions[question][state]:
            val = val[0]
            count += 1
            total_sum += val
        return total_sum / count

    def get_states_mean(self, question):
        """ Compute Data_Value mean for all the states separately """
        ret = {}
        for state in self.all_questions[question]:
            ret[state] = self.get_state_mean(question, state)

        # generate a sorted dictionary
        ret = dict(sorted(ret.items(), key=lambda entry: entry[1]))
        return ret

    def get_best5(self, question):
        """ Get the best 5 states as mean for that question """

        # Since we already have a sorted dictionary/list, we can just get the first/last elements
        all_states = self.get_states_mean(question)
        if question in self.questions_best_is_min:
            return dict(list(all_states.items())[:5])
        return dict(list(all_states.items())[-5:])

    def get_worst5(self, question):
        """ Get the worst 5 states as mean for that question """

        # Since we already have a sorted dictionary/list, we can just get the first/last elements
        all_states = self.get_states_mean(question)
        if question in self.questions_best_is_max:
            return dict(list(all_states.items())[:5])
        return dict(list(all_states.items())[-5:])

    def get_diff_from_mean(self, question):
        """ Compute difference from mean for all the states separately """
        ret = {}

        # get reference mean
        glob_mean = self.get_global_mean(question)

        # compute difference per se
        for state in self.all_questions[question].keys():
            ret[state] = glob_mean - self.get_state_mean(question, state)
        return ret

    def get_state_diff_from_mean(self, question, state):
        """ Compute difference from mean for only one state """
        return {state: self.get_global_mean(question) - self.get_state_mean(question, state)}

    def get_mean_by_category(self, question):
        """ Compute all tuples (state, category, stratification_category) for all states """
        total_values = {}
        total_count = {}
        for state in self.all_questions[question].keys():
            for val in self.all_questions[question][state]:

                # avoid NaN values for stratification
                if val[2] == "" or val[1] == "":
                    continue
                tup = str((state, val[2], val[1]))

                # check whether it is the first time encountering a tuple
                if tup not in total_values:
                    total_values[tup] = val[0]
                    total_count[tup] = 1
                else:
                    total_values[tup] += val[0]
                    total_count[tup] += 1

        for tup in total_values:
            total_values[tup] = total_values[tup] / total_count[tup]

        return total_values

    def get_state_mean_by_category(self, question, state):
        """ Compute all tuples (state, category, stratification_category) for a state """
        total_values = {}
        total_count = {}

        for val in self.all_questions[question][state]:
            # avoid NaN values for stratification
            if val[2] == "" or val[1] == "":
                continue
            tup = str((val[2], val[1]))

            # check whether it is the first time encountering a tuple
            if tup not in total_values:
                total_values[tup] = val[0]
                total_count[tup] = 1
            else:
                total_values[tup] += val[0]
                total_count[tup] += 1

        for tup in total_values:
            total_values[tup] = total_values[tup] / total_count[tup]

        return {state: total_values}
