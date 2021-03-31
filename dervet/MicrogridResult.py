"""
Result.py

"""

import pandas as pd
from storagevet.Result import Result
from storagevet.ErrorHandling import *


class MicrogridResult(Result):
    """

    """

    def __init__(self, scenario):
        """ Initialize all Result objects, given a Scenario object with the following attributes.

            Args:
                scenario (MicrogridScenario.MicrogridScenario): scenario object after optimization has run to completion
        """
        super().__init__(scenario)
        self.deferral_sizing = scenario.deferral_sizing
        self.reliability_sizing = scenario.reliability_sizing
        self.opt_engine = scenario.opt_engine
        self.sizing_df = pd.DataFrame()
        for der in self.poi.der_list:
            if der.tag == "Battery":
                # if degradation module is turned on, then reset all CBA attributes to reflect yearly cycle counts
                der.set_end_of_life_based_on_degradation_cycle(self.opt_years, self.start_year, self.end_year, self.cost_benefit_analysis.ecc_mode)

    def collect_results(self):
        """ Collects any optimization variable solutions or user inputs that will be used for drill down
        plots, as well as reported to the user. No matter what value stream or DER is being evaluated, these
        dataFrames should always be made and reported to the user

        Three attributes are edited in this method: TIME_SERIES_DATA, MONTHLY_DATA, TECHNOLOGY_SUMMARY
        """
        super().collect_results()
        self.sizing_df = self.poi.sizing_summary()

    def create_drill_down_dfs(self):
        """ Tells ServiceAggregator and POI to build drill down reports. These are reports
        that are service or technology specific.

        Returns: Dictionary of DataFrames of any reports that are value stream specific
            keys are the file name that the df will be saved with

        """
        if self.opt_engine:
            self.drill_down_dict.update(self.poi.drill_down_dfs(monthly_data=self.monthly_data, time_series_data=self.time_series_data,
                                                                technology_summary=self.technology_summary, sizing_df=self.sizing_df))
        self.drill_down_dict.update(self.service_agg.drill_down_dfs(monthly_data=self.monthly_data, time_series_data=self.time_series_data,
                                                                    technology_summary=self.technology_summary, sizing_df=self.sizing_df,
                                                                    der_list=self.poi.der_list))
        TellUser.debug("Finished post optimization analysis")

    def calculate_cba(self):
        """ Calls all financial methods that will result in a series of dataframes to describe the cost benefit analysis for the
        case in question.

        """
        if self.opt_engine:
            super().calculate_cba()

    def save_as_csv(self, instance_key, sensitivity=False):
        """ Save useful DataFrames to disk in csv files in the user specified path for analysis.

        Args:
            instance_key (int): string of the instance value that corresponds to the Params instance that was used for
                this simulation.
            sensitivity (boolean): logic if sensitivity analysis is active. If yes, save_path should create additional
                subdirectory

        Prints where the results have been saved when completed.
        """
        super().save_as_csv(instance_key, sensitivity)
        if sensitivity:
            savepath = self.dir_abs_path / str(instance_key)
        else:
            savepath = self.dir_abs_path
        self.sizing_df.to_csv(path_or_buf=Path(savepath, 'size' + self.csv_label + '.csv'), index=False)
        self.cost_benefit_analysis.equipment_lifetime_report.to_csv(path_or_buf=Path(savepath, 'equipment_lifetimes' + self.csv_label + '.csv'))
        if self.cost_benefit_analysis.tax_calculations is not None:
            self.cost_benefit_analysis.tax_calculations.to_csv(path_or_buf=Path(savepath,
                                                                                'tax_breakdown' +
                                                                                self.csv_label + '.csv'))
        if self.cost_benefit_analysis.ecc_df is not None:
            self.cost_benefit_analysis.ecc_df.to_csv(path_or_buf=Path(savepath, 'ecc_breakdown' + self.csv_label + '.csv'))
        TellUser.info(f'DER results have been saved to: {savepath}')