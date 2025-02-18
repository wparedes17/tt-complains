import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
from ml_models.lda_modeller import CSVComplaintAnalyzer

class TopicVisualizer:
    def __init__(self, analyzer: CSVComplaintAnalyzer):
        self.analyzer = analyzer
        self.colors = px.colors.qualitative.Set3

    def plot_topic_distribution(self) -> None:
        """
        Plot overall topic distribution in the dataset.
        """
        if self.analyzer.data_df is None:
            raise ValueError("No data available. Run train_model() first.")

        topic_counts = self.analyzer.data_df['predicted_topic'].value_counts()

        # Create figure
        fig = go.Figure(data=[
            go.Bar(
                x=[f'Topic {i}' for i in range(self.analyzer.num_topics)],
                y=[topic_counts.get(i, 0) for i in range(self.analyzer.num_topics)],
                marker_color=self.colors[:self.analyzer.num_topics]
            )
        ])

        fig.update_layout(
            title='Distribution of Topics in Complaints',
            xaxis_title='Topic',
            yaxis_title='Number of Complaints',
            template='plotly_white'
        )

        return fig

    def plot_topic_wordcloud(self, topic_id: int, figsize=(10, 6)) -> None:
        """
        Generate word cloud for a specific topic.
        """
        if self.analyzer.lda_model is None:
            raise ValueError("Model not trained. Run train_model() first.")

        # Get word weights for the topic
        word_weights = dict(self.analyzer.lda_model.show_topic(topic_id, topn=50))

        # Generate word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis'
        ).generate_from_frequencies(word_weights)

        # Create figure
        plt.figure(figsize=figsize)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Cloud for Topic {topic_id}')

        return plt.gcf()

    def plot_topic_keywords(self, top_n: int = 10) -> go.Figure:
        """
        Plot top keywords for each topic with their probabilities.
        """
        if self.analyzer.lda_model is None:
            raise ValueError("Model not trained. Run train_model() first.")

        # Prepare data for visualization
        topics_data = []
        for topic_id in range(self.analyzer.num_topics):
            top_words = self.analyzer.lda_model.show_topic(topic_id, topn=top_n)
            for word, prob in top_words:
                topics_data.append({
                    'Topic': f'Topic {topic_id}',
                    'Word': word,
                    'Probability': prob
                })

        df = pd.DataFrame(topics_data)

        # Create figure
        fig = px.bar(
            df,
            x='Probability',
            y='Word',
            color='Topic',
            orientation='h',
            barmode='group',
            color_discrete_sequence=self.colors,
            title=f'Top {top_n} Keywords per Topic'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True,
            template='plotly_white'
        )

        return fig

    def plot_topic_evolution(self) -> go.Figure:
        """
        Plot topic probability evolution over time if datetime is available.
        """
        if self.analyzer.data_df is None:
            raise ValueError("No data available. Run train_model() first.")

        if 'datetime' not in self.analyzer.data_df.columns:
            raise ValueError("Datetime column not found in data")

        # Convert datetime column
        df = self.analyzer.data_df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')

        # Calculate rolling averages for each topic
        topic_probs = [f'topic_{i}_prob' for i in range(self.analyzer.num_topics)]
        rolling_avg = df[topic_probs].rolling(window=10, min_periods=1).mean()

        # Create figure
        fig = go.Figure()

        for i, col in enumerate(topic_probs):
            fig.add_trace(
                go.Scatter(
                    x=df['datetime'],
                    y=rolling_avg[col],
                    name=f'Topic {i}',
                    line=dict(color=self.colors[i])
                )
            )

        fig.update_layout(
            title='Topic Evolution Over Time (10-point Rolling Average)',
            xaxis_title='Date',
            yaxis_title='Topic Probability',
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def plot_topic_severity_correlation(self) -> go.Figure:
        """
        Plot correlation between topics and complaint severity.
        """
        if self.analyzer.data_df is None or 'severity' not in self.analyzer.data_df.columns:
            raise ValueError("Severity data not available")

        # Calculate average severity for each topic
        severity_by_topic = self.analyzer.data_df.groupby('predicted_topic')['severity'].agg(
            ['mean', 'std', 'count']
        ).reset_index()

        # Create figure
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=[f'Topic {i}' for i in severity_by_topic['predicted_topic']],
            y=severity_by_topic['mean'],
            error_y=dict(
                type='data',
                array=severity_by_topic['std'],
                visible=True
            ),
            marker_color=self.colors[:len(severity_by_topic)]
        ))

        fig.update_layout(
            title='Average Complaint Severity by Topic',
            xaxis_title='Topic',
            yaxis_title='Average Severity',
            template='plotly_white'
        )

        return fig

    def create_topic_summary_dashboard(self) -> None:
        """
        Create a comprehensive dashboard with all visualizations.
        """
        # Create all visualizations
        dist_fig = self.plot_topic_distribution()
        keywords_fig = self.plot_topic_keywords()
        severity_fig = self.plot_topic_severity_correlation()

        # Try to create time evolution plot if datetime is available
        try:
            evolution_fig = self.plot_topic_evolution()
            has_evolution = True
        except ValueError:
            has_evolution = False

        # Create word clouds
        wordcloud_figs = []
        for topic_id in range(self.analyzer.num_topics):
            wordcloud_fig = self.plot_topic_wordcloud(topic_id)
            wordcloud_figs.append(wordcloud_fig)

        # Save all figures
        dist_fig.write_html("topic_distribution.html")
        keywords_fig.write_html("topic_keywords.html")
        severity_fig.write_html("topic_severity.html")
        if has_evolution:
            evolution_fig.write_html("topic_evolution.html")

        for i, fig in enumerate(wordcloud_figs):
            fig.savefig(f"wordcloud_topic_{i}.png")
            plt.close(fig)


