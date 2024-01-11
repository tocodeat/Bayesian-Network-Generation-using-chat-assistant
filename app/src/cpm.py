from typing import Dict, List, Union

import pandas as pd
import numpy as np

class CPMCalculator(object):
    def __init__(self, activities: Dict[str, List[str]], durations: Dict[str, int]) -> None:
        """
        Initialize the CPMCalculator with activities and their durations. Note that the
        activities must be in topological order (i.e. all dependencies must be listed before
        the activity itself).

        Parameters
        ----------
        activities : dict
            A dictionary where keys are activity names and values are lists of their predecessor activities.
        durations : dict
            A dictionary where keys are activity names and values are their durations.

        Attributes
        ----------
        activity_names : list
            List of activity names.
        n : int
            Number of activities.
        adj_matrix : ndarray
            Adjacency matrix representing the relationships between activities.
        durations : ndarray
            Array of activity durations.
        ES_EF : ndarray
            Array containing Earliest Start and Earliest Finish times for each activity.
        LS_LF : ndarray
            Array containing Latest Start and Latest Finish times for each activity.
        TF : ndarray
            Array containing Total Float for each activity.
        project_end : float
            The project end time.
        """

        self.activity_names = list(activities.keys())
        self.n = len(self.activity_names)
        
        # Create an adjacency matrix for activities
        self.adj_matrix = np.zeros((self.n, self.n), dtype=int)
        for activity, preds in activities.items():
            for pred in preds:
                i = self.activity_names.index(pred)
                j = self.activity_names.index(activity)
                self.adj_matrix[i, j] = 1
        
        self.durations = np.array([durations[activity] for activity in self.activity_names])
        self.ES_EF = np.zeros((self.n, 2))
        self.LS_LF = np.zeros((self.n, 2))
        self.TF = np.zeros(self.n)
        self.project_end = None

    def compute_es_ef(self) -> None:
        """
        Compute the Earliest Start (ES) and Earliest Finish (EF) for each activity. This is a 
        forward pass that starts with the first activity and computes the ES and EF for each
        activity in topological order.
        """
        for i in range(self.n):
            predecessors = np.where(self.adj_matrix[:, i] == 1)[0]
            if len(predecessors) == 0:
                self.ES_EF[i, 0] = 0
                self.ES_EF[i, 1] = self.durations[i]
            else:
                max_ef = np.max(self.ES_EF[predecessors, 1])
                self.ES_EF[i, 0] = max_ef
                self.ES_EF[i, 1] = max_ef + self.durations[i]
        self.project_end = np.max(self.ES_EF[:, 1])

    def compute_ls_lf(self) -> None:
        """
        Compute the Latest Start (LS) and Latest Finish (LF) for each activity. This is a
        backward pass that starts with the last activity and computes the LS and LF for each
        activity in reverse topological order.
        """
        for i in reversed(range(self.n)):
            successors = np.where(self.adj_matrix[i, :] == 1)[0]
            if len(successors) == 0:
                self.LS_LF[i, 1] = self.project_end
                self.LS_LF[i, 0] = self.project_end - self.durations[i]
            else:
                min_ls = np.min(self.LS_LF[successors, 0])
                self.LS_LF[i, 1] = min_ls
                self.LS_LF[i, 0] = min_ls - self.durations[i]

    def compute_tf(self) -> None:
        """
        Compute the Total Float (TF) for each activity. The total float represents the amount 
        of time that you can delay a task without delaying the project. It provides a buffer 
        period. In essence, it gives the difference between when an activity could start at 
        the earliest (ES) and when it must start at the latest (LS) without affecting the 
        project's end date.
        """
        self.TF = self.LS_LF[:, 0] - self.ES_EF[:, 0]

    def get_results(self) -> pd.DataFrame:
        """
        Compute and return the CPM results for each activity.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame containing the results of the CPM analysis for each activity as a row.
        """
        self.compute_es_ef()
        self.compute_ls_lf()
        self.compute_tf()
        
        data = {
            'D': self.durations,
            'ES': self.ES_EF[:, 0],
            'EF': self.ES_EF[:, 1],
            'LS': self.LS_LF[:, 0],
            'LF': self.LS_LF[:, 1],
            'TF': self.TF
        }
        
        df = pd.DataFrame(data, index=self.activity_names).astype(np.int8)
        
        return df