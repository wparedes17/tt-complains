from lifelines import CoxPHFitter
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple
import pandas as pd
import numpy as np


class DriverSurvivalAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.cph = CoxPHFitter()
        self.fitted = False

    def prepare_data(self) -> pd.DataFrame:
        """
        Prepare data for survival analysis.
        """
        # Create duration column (time from start until quit or censoring)
        survival_data = self.data.copy()

        # Convert categorical variables to dummy variables
        survival_data = pd.get_dummies(
            survival_data,
            columns=['sex', 'most_common_complaint_topic'],
            drop_first=True
        )

        # Standardize continuous variables
        continuous_vars = [
            'age', 'experience', 'number_of_complaints',
            'avg_inter_complaint_time', 'avg_inter_trip_time',
            'time_since_last_trip'
        ]

        for var in continuous_vars:
            if var in survival_data.columns:
                mean = survival_data[var].mean()
                std = survival_data[var].std()
                survival_data[var] = (survival_data[var] - mean) / std

        return survival_data

    def fit_model(self) -> Tuple[pd.DataFrame, float]:
        """
        Fit Cox Proportional Hazard model and return summary.
        """
        survival_data = self.prepare_data()

        # Fit the model
        self.cph.fit(
            survival_data,
            duration_col='experience',
            event_col='has_quit',
            show_progress=True
        )

        self.fitted = True

        # Get model summary
        summary = self.cph.print_summary()
        concordance = self.cph.score(survival_data)

        return summary, concordance

    def plot_hazard_ratio(self, variable: str) -> None:
        """
        Plot hazard ratio for a specific variable.
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")

        self.cph.plot_partial_effects(variable)
        plt.title(f'Hazard Ratio for {variable}')
        plt.grid(True)
        return plt.gcf()

    def plot_feature_importance(self) -> None:
        """
        Plot feature importance based on coefficient magnitude.
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")

        # Get coefficients
        coef_df = pd.DataFrame({
            'coef': np.abs(self.cph.params_),
            'feature': self.cph.params_.index
        }).sort_values('coef', ascending=True)

        # Create plot
        plt.figure(figsize=(10, 6))
        sns.barplot(data=coef_df, x='coef', y='feature')
        plt.title('Feature Importance (Absolute Coefficient Magnitude)')
        plt.xlabel('|Coefficient|')
        plt.grid(True)
        return plt.gcf()

    def plot_survival_curves(self, num_profiles: int = 3) -> None:
        """
        Plot survival curves for different driver profiles.
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")

        # Create different profiles based on percentiles
        profiles = []
        percentiles = np.linspace(0, 1, num_profiles)

        for p in percentiles:
            profile = {}
            for column in self.cph.params_.index:
                profile[column] = self.data[column].quantile(p)
            profiles.append(profile)

        # Plot survival curves
        for i, profile in enumerate(profiles):
            self.cph.plot_partial_effects(
                profile,
                label=f'Profile {i + 1}'
            )

        plt.title('Survival Curves for Different Driver Profiles')
        plt.grid(True)
        return plt.gcf()
