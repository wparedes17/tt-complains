import os
import re
import pandas as pd
from typing import List, Tuple, Dict

import gensim
from gensim import corpora, models
from gensim.models import CoherenceModel

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')


class CSVComplaintAnalyzer:
    def __init__(self, num_topics: int = 2):
        self.num_topics = num_topics
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # Add domain-specific stop words
        self.stop_words.update(['driver', 'truck', 'trailer', 'delivery'])

        # Initialize model attributes
        self.dictionary = None
        self.lda_model = None
        self.corpus = None
        self.data_df = None

    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text data for LDA modeling.
        Returns list of tokens instead of joined string.
        """
        if not isinstance(text, str):
            return []

        # Convert to lowercase
        text = text.lower()

        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)

        # Tokenization
        tokens = word_tokenize(text)

        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens
                  if token not in self.stop_words and len(token) > 2]

        return tokens

    def load_data(self, complaints_file: str) -> pd.DataFrame:
        """
        Load complaints data from CSV file.
        """
        try:
            self.data_df = pd.read_csv(complaints_file, sep='|')
            required_columns = ['complain_id', 'comment']
            missing_columns = [col for col in required_columns if col not in self.data_df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            return self.data_df

        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")

    def train_model(self, complaints_file: str) -> Tuple[float, Dict, pd.DataFrame]:
        """
        Train the LDA topic model using data from CSV.
        Returns coherence score, topic keywords, and enriched DataFrame.
        """
        # Load and prepare data
        self.load_data(complaints_file)

        # Preprocess comments
        processed_docs = [self.preprocess_text(comment) for comment in self.data_df['comment']]

        # Create dictionary
        self.dictionary = corpora.Dictionary(processed_docs)

        # Filter out extreme frequencies
        self.dictionary.filter_extremes(no_below=2, no_above=0.9)

        # Create corpus
        self.corpus = [self.dictionary.doc2bow(doc) for doc in processed_docs]

        # Train LDA model
        self.lda_model = models.LdaModel(
            corpus=self.corpus,
            id2word=self.dictionary,
            num_topics=self.num_topics,
            random_state=42,
            update_every=1,
            chunksize=100,
            passes=10,
            alpha='auto',
            per_word_topics=True
        )

        # Calculate model coherence
        coherence_model = CoherenceModel(
            model=self.lda_model,
            texts=processed_docs,
            dictionary=self.dictionary,
            coherence='c_v'
        )
        coherence_score = coherence_model.get_coherence()

        # Get topic keywords
        topic_keywords = {}
        for idx, topic in self.lda_model.show_topics(formatted=False):
            topic_keywords[idx] = [(w, round(p, 4)) for w, p in topic]

        # Add predicted topics to DataFrame
        topic_predictions = self.predict_topics(self.data_df['comment'].tolist())
        self.data_df['predicted_topic'] = topic_predictions

        # Add topic distributions
        topic_distributions = [self.get_topic_distribution(comment)
                               for comment in self.data_df['comment']]

        # Add probability for each topic
        for topic_idx in range(self.num_topics):
            self.data_df[f'topic_{topic_idx}_prob'] = [
                dict(dist).get(topic_idx, 0.0) for dist in topic_distributions
            ]

        return coherence_score, topic_keywords, self.data_df

    def predict_topics(self, comments: List[str]) -> List[int]:
        """
        Predict dominant topic for each comment.
        """
        if not self.lda_model or not self.dictionary:
            raise ValueError("Model not trained. Call train_model() first.")

        predictions = []
        for comment in comments:
            # Preprocess comment
            tokens = self.preprocess_text(comment)
            bow = self.dictionary.doc2bow(tokens)

            # Get topic distribution
            topic_dist = self.lda_model.get_document_topics(bow)

            # Get dominant topic
            dominant_topic = max(topic_dist, key=lambda x: x[1])[0] if topic_dist else 0
            predictions.append(dominant_topic)

        return predictions

    def get_topic_distribution(self, comment: str) -> List[Tuple[int, float]]:
        """
        Get complete topic distribution for a single comment.
        """
        if not self.lda_model or not self.dictionary:
            raise ValueError("Model not trained. Call train_model() first.")

        tokens = self.preprocess_text(comment)
        bow = self.dictionary.doc2bow(tokens)
        topic_dist = self.lda_model.get_document_topics(bow)

        return [(topic_id, float(prob)) for topic_id, prob in topic_dist]

    def save_results(self, output_file: str) -> None:
        """
        Save enriched data back to CSV.
        """
        if self.data_df is None:
            raise ValueError("No data to save. Run train_model() first.")

        self.data_df.to_csv(output_file, index=False, sep='|')

    def save_model(self, model_dir: str) -> None:
        """
        Save trained model and dictionary for later use.
        """
        if not self.lda_model or not self.dictionary:
            raise ValueError("Model not trained. Call train_model() first.")

        os.makedirs(model_dir, exist_ok=True)
        self.lda_model.save(os.path.join(model_dir, 'lda_model'))
        self.dictionary.save(os.path.join(model_dir, 'dictionary'))

    def load_model(self, model_dir: str) -> None:
        """
        Load previously trained model and dictionary.
        """
        model_path = os.path.join(model_dir, 'lda_model')
        dict_path = os.path.join(model_dir, 'dictionary')

        if not (os.path.exists(model_path) and os.path.exists(dict_path)):
            raise ValueError("Model files not found in specified directory")

        self.lda_model = models.LdaModel.load(model_path)
        self.dictionary = corpora.Dictionary.load(dict_path)
