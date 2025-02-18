import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from lifelines import KaplanMeierFitter


class SurvivalDataExplorer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.colors = px.colors.qualitative.Set3

    def plot_quit_distribution(self) -> go.Figure:
        """
        Plot the distribution of quit vs active drivers.
        """
        quit_counts = self.data['has_quit'].value_counts()
        labels = ['Active', 'Quit']

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=[quit_counts[0], quit_counts[1]],
                hole=0.4,
                marker_colors=self.colors[:2]
            )
        ])

        fig.update_layout(
            title='Distribution of Driver Status',
            annotations=[{
                'text': f'Total: {len(self.data)}',
                'x': 0.5, 'y': 0.5,
                'font_size': 14,
                'showarrow': False
            }]
        )

        return fig

    def plot_numerical_distributions(self) -> go.Figure:
        """
        Plot distributions of numerical features with comparison between quit and active drivers.
        """
        numerical_cols = [
            'age', 'experience', 'number_of_complaints',
            'avg_inter_complaint_time', 'avg_inter_trip_time',
            'time_since_last_trip'
        ]

        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=numerical_cols
        )

        for idx, col in enumerate(numerical_cols, 1):
            row = (idx - 1) // 3 + 1
            col_idx = (idx - 1) % 3 + 1

            # Add histogram for active drivers
            fig.add_trace(
                go.Histogram(
                    x=self.data[self.data['has_quit'] == 0][col],
                    name='Active',
                    opacity=0.7,
                    marker_color=self.colors[0]
                ),
                row=row, col=col_idx
            )

            # Add histogram for quit drivers
            fig.add_trace(
                go.Histogram(
                    x=self.data[self.data['has_quit'] == 1][col],
                    name='Quit',
                    opacity=0.7,
                    marker_color=self.colors[1]
                ),
                row=row, col=col_idx
            )

        fig.update_layout(
            height=800,
            showlegend=True,
            title='Distribution of Numerical Features by Driver Status',
            template='plotly_white'
        )

        return fig

    def plot_kaplan_meier_curves(self) -> dict:
        """
        Plot Kaplan-Meier survival curves with different stratifications.
        """
        kmf = KaplanMeierFitter()
        figures = {}

        # Overall survival curve
        fig_overall = go.Figure()
        kmf.fit(
            self.data['experience'],
            self.data['has_quit'],
            label='Overall'
        )

        fig_overall.add_trace(go.Scatter(
            x=kmf.timeline,
            y=kmf.survival_function_.values.flatten(),
            name='Overall',
            line=dict(color=self.colors[0])
        ))

        fig_overall.update_layout(
            title='Overall Survival Curve',
            xaxis_title='Experience (Time)',
            yaxis_title='Survival Probability',
            template='plotly_white'
        )

        figures['overall'] = fig_overall

        # Survival curves by sex
        fig_sex = go.Figure()
        for sex in self.data['sex'].unique():
            mask = self.data['sex'] == sex
            kmf.fit(
                self.data[mask]['experience'],
                self.data[mask]['has_quit'],
                label=f'Sex: {sex}'
            )

            fig_sex.add_trace(go.Scatter(
                x=kmf.timeline,
                y=kmf.survival_function_.values.flatten(),
                name=f'Sex: {sex}'
            ))

        fig_sex.update_layout(
            title='Survival Curves by Sex',
            xaxis_title='Experience (Time)',
            yaxis_title='Survival Probability',
            template='plotly_white'
        )

        figures['by_sex'] = fig_sex

        # Survival curves by complaint frequency
        self.data['complaint_group'] = pd.qcut(
            self.data['number_of_complaints'],
            q=3,
            labels=['Low', 'Medium', 'High']
        )

        fig_complaints = go.Figure()
        for group in self.data['complaint_group'].unique():
            mask = self.data['complaint_group'] == group
            kmf.fit(
                self.data[mask]['experience'],
                self.data[mask]['has_quit'],
                label=f'Complaints: {group}'
            )

            fig_complaints.add_trace(go.Scatter(
                x=kmf.timeline,
                y=kmf.survival_function_.values.flatten(),
                name=f'Complaints: {group}'
            ))

        fig_complaints.update_layout(
            title='Survival Curves by Complaint Frequency',
            xaxis_title='Experience (Time)',
            yaxis_title='Survival Probability',
            template='plotly_white'
        )

        figures['by_complaints'] = fig_complaints

        return figures

    def plot_correlation_matrix(self) -> go.Figure:
        """
        Plot correlation matrix of numerical features.
        """
        numerical_cols = [
            'age', 'experience', 'number_of_complaints',
            'avg_inter_complaint_time', 'avg_inter_trip_time',
            'time_since_last_trip', 'has_quit'
        ]

        corr_matrix = self.data[numerical_cols].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1
        ))

        fig.update_layout(
            title='Correlation Matrix of Numerical Features',
            template='plotly_white'
        )

        return fig

    def create_summary_dashboard(self, output_dir: str = '.') -> None:
        """
        Create and save all visualizations as HTML files.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Generate all plots
        quit_dist = self.plot_quit_distribution()
        numerical_dist = self.plot_numerical_distributions()
        survival_curves = self.plot_kaplan_meier_curves()
        corr_matrix = self.plot_correlation_matrix()

        # Save plots
        quit_dist.write_html(f"{output_dir}/quit_distribution.html")
        numerical_dist.write_html(f"{output_dir}/numerical_distributions.html")
        for name, fig in survival_curves.items():
            fig.write_html(f"{output_dir}/survival_curve_{name}.html")
        corr_matrix.write_html(f"{output_dir}/correlation_matrix.html")
