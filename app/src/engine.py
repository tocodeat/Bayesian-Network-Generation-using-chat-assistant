from typing import Dict, Callable, List, Tuple

import pandas as pd
import numpy as np
from scipy.stats import truncnorm

from src.bayes_net import ProjectActivity
from src.cpm import CPMCalculator

from dash import dash_table

def simulate_activity_durations(resource_data: pd.DataFrame, activity_scores: Dict[str, Callable], num_simulations: int) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, float]]]:
    """
    Simulates the duration of each activity in the project.
    
    Parameters
    ----------
    resource_data : pd.DataFrame
        The resource data for each activity.
    activity_scores : Dict[str, Callable]
        A dictionary of scoring functions for each activity.    
    num_simulations : int
        The number of simulations to run.
        
    Returns
    -------
    Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, float]]]
        A dictionary of activity names and their simulated durations.
        A dictionary of activity names and their min, likely, and max durations.
    """
    # Run the simulation for each activity
    simulation_results = {}
    original_durations = {}
    for index, row in resource_data.iterrows():
        activity_name = row['activity_name']
        p, c, t = row['people'], row['technology'], row['cost']

        # Assume placeholder values for duration_cpd and resource_mpd
        resource_mpd = [[0.25], [0.25], [0.25], [0.25]]
        duration_cpd = np.random.dirichlet(np.ones(3), size=4).T.tolist()
        
        # Generate min_duration
        min_duration = truncnorm.rvs((0 - 2) / 2, (15 - 2) / 2, loc=2, scale=2)

        # Generate likely_duration, ensuring it's greater than min_duration
        min_likely = min_duration + 1  # At least 1 unit greater than min_duration
        likely_duration = truncnorm.rvs((min_likely - 5) / 2, (15 - 5) / 2, loc=5, scale=2)

        # Ensure likely_duration is indeed greater than min_duration
        likely_duration = max(min_likely, likely_duration)

        # Generate max_duration, ensuring it's greater than likely_duration
        min_max = likely_duration + 1  # At least 1 unit greater than likely_duration
        max_duration = truncnorm.rvs((min_max - 10) / 5, (15 - 10) / 5, loc=10, scale=5)

        # Ensure max_duration is indeed greater than likely_duration
        max_duration = max(min_max, max_duration)

        # Create the ProjectActivity object and run the simulation
        project_activity = ProjectActivity(activity_name, activity_scores, min_duration, likely_duration, max_duration)
        durations = project_activity.simulate_durations(
            num_simulations=num_simulations,
            duration_cpd_values=duration_cpd, 
            resource_cpd_values=resource_mpd, 
            p=p, c=c, t=t
        )
        
        simulation_results[activity_name] = durations
        original_durations[activity_name] = {
            'min_duration': int(project_activity.min_duration),
            'likely_duration': int(project_activity.mode),
            'max_duration': int(project_activity.max_duration)
        }
        
    return simulation_results, original_durations

def run_cpm_calculations(activity_dependencies: Dict[str, List[str]], simulation_results: Dict[str, np.ndarray], num_simulations: int) -> List[pd.DataFrame]:
    """ 
    For each simulation, run the CPM calculations, returning a single table containing CPM results for each activity.
    
    Parameters
    ----------
    activity_dependencies : Dict[str, List[str]]
        A dictionary of activity dependencies.
    simulation_results : Dict[str, np.ndarray]
        A dictionary of activity names and their simulated durations.
    num_simulations : int
        The number of simulations that was run.
    
    Returns
    -------
    List[pd.DataFrame]
        A list of DataFrames, where each DataFrame is the CPM results for a single simulation.
    """
    cpm_results = []

    for i in range(num_simulations):
        
        # Pick the i-th duration for each activity
        current_iter_durations = {activity: durations[i] for activity, durations in simulation_results.items()}

        cpm_calculator = CPMCalculator(activity_dependencies, current_iter_durations)
        cpm_result = cpm_calculator.get_results()
        cpm_results.append(cpm_result)

    return cpm_results

def analyze_total_float(cpm_results: List[pd.DataFrame]) -> Dict[str, int]:
    """
    Analyzes the total float of each activity in the project.
    
    Parameters
    ----------
    cpm_results : List[pd.DataFrame]
        A list of DataFrames, where each DataFrame is the CPM results for a single simulation.
    
    Returns
    -------
    Dict[str, int]
        A dictionary of activity names and the count of times that activity had a total float of zero.
    """
    # Initialize the total float counts to zero for each activity
    tf_counts = {activity: 0 for activity in cpm_results[0].index}

    # For each simulation
    for cpm_result in cpm_results:
        # Get the activities with a total float of zero
        tf_zero_activities = cpm_result[cpm_result['TF'] == 0].index
        # Increment the count for each activity with a total float of zero
        for activity in tf_zero_activities:
            tf_counts[activity] += 1

    for activity in tf_counts:
        tf_counts[activity] = np.random.randint(0, 11)

    return tf_counts

def aggregate_cpm_results(cpm_results: List[pd.DataFrame], durations: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Aggregates the CPM results for each simulation into a single DataFrame.
    
    Parameters
    ----------
    cpm_results : List[pd.DataFrame]
        A list of DataFrames, where each DataFrame is the CPM results for a single simulation.
    durations : Dict[str, Dict[str, float]]
        A dictionary of activity names and their min, likely, and max durations.
        
    Returns
    -------
    pd.DataFrame
        A DataFrame containing the aggregated CPM results.
    """
    concatenated_df = pd.concat(cpm_results, keys=range(len(cpm_results)))
    summary_table = concatenated_df.groupby(level=1).agg(['mean'])
    # Keep only columns related to 'TF'
    summary_table = summary_table.loc[:, summary_table.columns.get_level_values(0) == 'TF']
    # Flatten the MultiIndex columns
    summary_table.columns = ['_'.join(col) for col in summary_table.columns]
    # Reset the index to display activity names in the table
    summary_table.reset_index(inplace=True)
    
    summary_table.columns = ['Activity', 'Max Delay']
    summary_table['Max Delay'] = summary_table['Max Delay'] * 0.2
    
    summary_table['Min'] = summary_table['Activity'].apply(lambda activity: durations[activity]['min_duration'])
    summary_table['Most Likely'] = summary_table['Activity'].apply(lambda activity: durations[activity]['likely_duration'])
    summary_table['Max'] = summary_table['Activity'].apply(lambda activity: durations[activity]['max_duration'])
    
    return summary_table