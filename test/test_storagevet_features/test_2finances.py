"""
This file tests features of the CBA module. All tests should pass.

The tests in this file can be run with .

"""
import pytest
from test_storagevet_features.TestingLib import assert_ran, run_case
from pathlib import Path
from storagevet.ErrorHandling import *
import pandas as pd
import numpy as np

DIR = Path("./test/model_params")


"""
Test Proforma: degradation, retailETS growth rate = 0, inflation rate = 3%,
no fixed or variable OM costs
"""

# run case
run_results = run_case(DIR / "040-Degradation_Test_MP.csv")
# get proforma
actual_proforma = run_results.proforma_df()
# get first results instance
results = run_results.instances.get(0)


def test_all_project_years_are_in_proforma():
    expected_index = pd.period_range(results.start_year, results.end_year, freq='y')
    expected_index = set(expected_index.values)
    expected_index.add('CAPEX Year')
    assert set(actual_proforma.index.values) == expected_index


def test_years_btw_and_after_optimization_years_are_filed():
    assert np.all(actual_proforma['Yearly Net Value'])


energy_charges = actual_proforma.loc[actual_proforma.index != 'CAPEX Year',
                                     'Avoided Energy Charge']


def test_older_opt_year_energy_charge_values_less():
    assert energy_charges[pd.Period(2017, freq='y')] > energy_charges[pd.Period(2022, freq='y')]


def test_non_opt_year_energy_charge_values_same_as_last_opt_year():
    last_opt_year = pd.Period(2022, freq='y')
    assert np.all((energy_charges[energy_charges.index > last_opt_year] / energy_charges[
        last_opt_year]) == 1)


"""
Test Proforma: no degradation, retailETS growth rate = 0%, inflation rate = 3%,
none zero fixed or variable OM costs
"""

# run case
run_results = run_case(DIR / "041-no_Degradation_Test_MP.csv")
# get proforma
actual_proforma = run_results.proforma_df()

energy_charges1 = actual_proforma.loc[actual_proforma.index != 'CAPEX Year',
                                      'Avoided Energy Charge']


def test_opt_year_energy_charge_values_same():
    # growth rate = 0, so all opt year (2017, 2022) values should be the same
    assert energy_charges1[pd.Period(2017, freq='y')] == energy_charges1[pd.Period(2022, freq='y')]


def test_non_opt_year_energy_charge_values():
    assert np.all((energy_charges1 / energy_charges1[pd.Period(2017, freq='y')]) == 1)


inflation_rate = [1.03**(year.year - 2017) for year in energy_charges1.index]


def test_variable_om_values_reflect_inflation_rate():
    variable_om = actual_proforma.loc[actual_proforma.index != 'CAPEX Year',
                                      'BATTERY: es Variable O&M Cost'].values
    deflated_cost = variable_om / inflation_rate
    compare_cost_to_base_year_value = list(deflated_cost / deflated_cost[0])
    # the years including and in between opt_years should be the same as base
    assert compare_cost_to_base_year_value[:2022-2017-1] == list(np.ones(2022-2017-1))
    # years after last opt_year should be same as inflation rate
    after_opt_yr_vals = compare_cost_to_base_year_value[2022-2017:]
    expected_inflation_after_max_opt_yr = [1.03**year for year in range(len(after_opt_yr_vals))]
    assert np.all(np.around(after_opt_yr_vals, decimals=5) == np.around(
        expected_inflation_after_max_opt_yr, decimals=5))


def test_fixed_om_values_reflect_inflation_rate():
    fixed_om = actual_proforma.loc[actual_proforma.index != 'CAPEX Year',
                                   'BATTERY: es Fixed O&M Cost'].values
    deflated_cost = fixed_om / inflation_rate
    compare_cost_to_base_year_value = list(deflated_cost / deflated_cost[0])
    # the years including and in between opt_years should be the same as base
    assert compare_cost_to_base_year_value[:2022 - 2017 - 1] == list(np.ones(2022 - 2017 - 1))
    # years after last opt_year should be same as inflation rate
    after_opt_yr_vals = compare_cost_to_base_year_value[2022 - 2017:]
    expected_inflation_after_max_opt_yr = [1.03 ** year for year in range(len(after_opt_yr_vals))]
    assert np.all(np.around(after_opt_yr_vals, decimals=5) == np.around(
        expected_inflation_after_max_opt_yr, decimals=5))


"""
Test Proforma: no degradation, retailETS growth rate = -10%, inflation rate = 3%,
none zero fixed or variable OM costs
"""

# run case
run_results = run_case(DIR / "042-no_Degradation_Test_MP_tariff_neg_grow_rate.csv")
# get proforma
actual_proforma = run_results.proforma_df()

energy_charges2 = actual_proforma.loc[actual_proforma.index != 'CAPEX Year',
                                      'Avoided Energy Charge']


def test_opt_year_energy_charge_values_should_reflect_growth_rate():
    # growth rate = 0, so all opt year (2017, 2022) values should be the same
    assert energy_charges2[pd.Period(2017, freq='y')] > energy_charges2[pd.Period(2022, freq='y')]


def test_years_beyond_max_opt_year_energy_charge_values_reflect_growth_rate():
    years_beyond_max = energy_charges2[pd.Period(2023, freq='y'):]
    max_opt_year_value = energy_charges2[pd.Period(2022, freq='y')]
    charge_growth_rate = [.9 ** (year.year-2022) for year in years_beyond_max.index]
    expected_values = years_beyond_max / charge_growth_rate
    assert np.all(np.around(expected_values.values, decimals=7) == np.around(max_opt_year_value, decimals=7))


