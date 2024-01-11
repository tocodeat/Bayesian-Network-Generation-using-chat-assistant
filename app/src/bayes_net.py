from typing import List, Dict, Callable, Tuple

from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
import numpy as np

class ProjectActivity(object):
    """
    This class represents a project activity. It is used to simulate the duration of the activity
    based on the resource state (i.e., 0-25%, 25-50%, 50-75%, 75-100%).
    """
    def __init__(self, activity_name: str, activity_scores: Dict[str, Callable], min_duration: int, likely_duration: int, max_duration: int):
        """
        Constructor for the ProjectActivity class.
        
        Parameters
        ----------
        activity_name : str
            The name of the activity.
        activity_scores : Dict[str, Callable]
            A dictionary of scoring functions for each activity.
        min_duration : int
            The minimum duration of the activity.
        likely_duration : int
            The most likely duration of the activity.
        max_duration : int
            The maximum duration of the activity. 
        """
        self.activity_name = activity_name
        self.activity_scores = activity_scores
        self.min_duration = min_duration
        self.likely_duration = likely_duration
        self.max_duration = max_duration
        self.model = BayesianNetwork()
        self.model.add_edges_from([
            (f'Resource_{self.activity_name}', f'Duration_{self.activity_name}')
        ])
        self.duration_node = f'Duration_{self.activity_name}'
        self.resource_node = f'Resource_{self.activity_name}'

        # Initialize the Bayesian network structure
        self.model.add_nodes_from([self.duration_node])
        
    def _set_resource_mpd(self, marginal_values: List[float], variable_card: int = 4) -> None:
        """
        Sets the marginal probability distribution (MPD) for the Resource node. 
        """
        if len(marginal_values) != variable_card:
            raise ValueError('The length of MPD does not match the cardinality of the variable node')
        
        # Define the MPD for the Resource node
        resource_mpd = TabularCPD(variable=self.resource_node,
                                  variable_card=variable_card,
                                  values=marginal_values)
        self.model.add_cpds(resource_mpd)

    def _set_duration_cpd(self, duration_cpd_values: List[List[float]], variable_card: int = 3, evidence_card: int = 4) -> None:
        """
        Sets the conditional probability distribution (CPD) for the Duration node.
        
        Parameters
        ----------
        duration_cpd_values : List[List[float]]
            The CPD values for the Duration node.
        variable_card : int, optional
            The cardinality of the Duration node, by default 3.
        evidence_card : int, optional
            The cardinality of the evidence node (i.e., Resource node), by default 4.
            
        Raises
        ------
        ValueError
            If the number of CPD values does not match the cardinality of the evidence node. 
        """
        if any(len(row) != evidence_card for row in duration_cpd_values):
            raise ValueError('The columns of CPD does not match the cardinality of the evidence node')
        if len(duration_cpd_values) != variable_card:
            raise ValueError('The rows of CPD does not match the cardinality of the variable node')
        
        # Define the CPD for the Duration node dynamically based on the resource state
        duration_cpd = TabularCPD(variable=self.duration_node,
                                  variable_card=3,  # Min, likely, and max durations
                                  values=duration_cpd_values,
                                  evidence=[self.resource_node],
                                  evidence_card=[evidence_card])
        self.model.add_cpds(duration_cpd)

    def _assign_bin(self, activity:str , p: int, c: int, t: int) -> Tuple[List[List[float]], str]:
        """
        Assigns a resource state bin probability distribution based on the provided values for p, c, and t.
        
        Parameters
        ----------
        activity : str
            The name of the activity.
        p : int
            The personnel value.
        c : int
            The cost value.
        t : int
            The technology value.
            
        Returns
        -------
        Tuple[List[List[float]], str]
            A tuple containing the resource state bin probabilities and the resource state bin.
        """
        score_function = self.activity_scores.get(activity)
        
        if not score_function:
            raise ValueError(f"No scoring function defined for activity '{activity}'")
        
        # Calculate the composite resource score for the activity
        scores = np.array(score_function(p, c, t))
        # Define the bin thresholds
        bins = np.array([25, 50, 75, 100])
        
        # Calculate how much of the score exceeds each bin's lower threshold, clipped at 0
        bin_differences = np.clip(scores - np.append(0, bins[:-1]), 0, None)
        
        # Determine the actual score assigned to each bin, which is of the minimum between the differences and the bin's capacity 
        # The bins are sequential and exclusive, a score that's higher than the first bin's threshold will fill this bin to its maximum and spill over into the next bin, and so on
        bin_scores = np.minimum(bin_differences, np.diff(np.append(0, bins)))

        # Sum the scores across all bins to get the total score
        total_score = bin_scores.sum()
        
        # Normalize the scores to get the probabilities
        # If the total score is zero (which should not occur in practice), default to equal probabilities (no information)
        probabilities = bin_scores / total_score if total_score > 0 else np.full(len(bins), 1 / len(bins))
        
        # Reshape the probabilities to match the number of resource states, which is expected by pgmpy
        probabilities = probabilities.reshape(4, -1).tolist()
        
        # Get the index of the resource state with the highest probability
        resource_state_index = np.argmax(probabilities)

        bin_mapping = {
            0: "0%-25%",
            1: "25%-50%",
            2: "50%-75%",
            3: "75%-100%"
        }

        return probabilities, bin_mapping.get(resource_state_index)

    def simulate_durations(self,
                           num_simulations: int, 
                           duration_cpd_values: List[List[int]], 
                           resource_cpd_values: List[List[int]],
                           p: int, 
                           c: int, 
                           t: int, 
                           weight_p: int = 1, 
                           weight_c: int = 1, 
                           weight_t: int = 1) -> np.ndarray:
        """ 
        Simulate duration estimates for CPM calculations.
        
        Parameters
        ----------
        num_simulations : int
            The number of simulations to run.
        duration_cpd_values : List[List[int]]
            The CPD values for the Duration node.
        resource_cpd_values : List[List[int]]
            The CPD values for the Resource node.
        p : int
            The personnel value.
        c : int
            The cost value.
        t : int
            The technology value.
        weight_p : int, optional
            The weight for the personnel value, by default 1.
        weight_c : int, optional
            The weight for the cost value, by default 1.
        weight_t : int, optional
            The weight for the technology value, by default 1.
            
        Returns
        -------
        np.ndarray
            An array of simulated durations.
        """
        # Assign the resource state bin probabilities
        resource_probabilities, resource_state_index = self._assign_bin(self.activity_name, p, c, t)
        self._set_resource_mpd(resource_cpd_values)
        self._set_duration_cpd(duration_cpd_values)
        
        # Get the index of the resource state with the highest probability
        resource_state_index = np.argmax(resource_probabilities)

        # Perform inference to get the probability distribution for duration
        inference = VariableElimination(self.model)
        duration_probabilities = inference.query(
            variables=[self.duration_node],
            evidence={self.resource_node: resource_state_index}
        ).values

        # Determine the mode's position relative to min and max durations
        mode_weighted_position = (
            duration_probabilities[0] * self.min_duration + 
            duration_probabilities[1] * self.likely_duration + 
            duration_probabilities[2] * self.max_duration
        ) / sum(duration_probabilities)

        # Ensure the mode is within the bounds
        self.mode = np.clip(mode_weighted_position, self.min_duration, self.max_duration)

        simulated_durations = np.random.triangular(
            left=self.min_duration,
            mode=self.mode,
            right=self.max_duration,
            size=num_simulations
        )
        simulated_durations = np.rint(simulated_durations).astype(int)
        
        return simulated_durations