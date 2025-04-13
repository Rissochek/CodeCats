import pandas as pd
import numpy as np
from lightgbm import Booster
import os
import re
import json
import spacy
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sentence_transformers import SentenceTransformer
import pickle


def load_preprocessor(name, input_dir='models'):
    """
    Загружает предобработчик из указанной директории.
    
    Args:
        name (str): Имя предобработчика
        input_dir (str): Директория, откуда загружать
        
    Returns:
        object: Загруженный предобработчик
    """
    file_path = os.path.join(input_dir, f"{name}.pkl")
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    else:
        return None

import pandas as pd
import numpy as np
from lightgbm import Booster
import os
import re
import json
import spacy
import pickle
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sentence_transformers import SentenceTransformer

class NewsPredictor:
    def __init__(self, model_path, sphere='sphere_Финансы', preprocessors_dir='src/models'):
        """
        Initialize the predictor with a model path.
        
        Args:
            model_path (str): Path to the LGBM model file (.txt)
            sphere (str): The sphere for which the model was trained
            preprocessors_dir (str): Directory where preprocessors are saved
        """
        # Load the model
        self.model = Booster(model_file=model_path)
        self.sphere = sphere
        
        # Load model feature names
        model_sphere = os.path.basename(model_path).replace('_model.txt', '')
        features_file = os.path.join(os.path.dirname(model_path), f"{model_sphere}_features.json")
        if os.path.exists(features_file):
            with open(features_file, 'r') as f:
                self.feature_names = json.load(f)['feature_names']
        else:
            self.feature_names = None
        
        # Initialize spaCy
        self.nlp = spacy.load("ru_core_news_sm")
        
        # Load preprocessors
        self.load_preprocessors(preprocessors_dir)
        
        # Initialize sentence transformer for embeddings
        self.sentence_transformer = SentenceTransformer("sergeyzh/rubert-mini-frida")
        
    def load_preprocessors(self, preprocessors_dir):
        """
        Load pre-fitted preprocessors.
        
        Args:
            preprocessors_dir (str): Directory where preprocessors are saved
        """
        # Load each preprocessor
        self.sphere_encoder = self.load_preprocessor('sphere_encoder', preprocessors_dir)
        self.tfidf_unigram = self.load_preprocessor('tfidf_unigram', preprocessors_dir)
        self.tfidf_bigram = self.load_preprocessor('tfidf_bigram', preprocessors_dir)
        self.count_vec = self.load_preprocessor('count_vec', preprocessors_dir)
        self.lda = self.load_preprocessor('lda', preprocessors_dir)
        self.nmf = self.load_preprocessor('nmf', preprocessors_dir)
        
        # If any preprocessor is missing, initialize it (but it won't be trained)
        if self.sphere_encoder is None:
            self.sphere_encoder = OneHotEncoder(handle_unknown='ignore')
            self.sphere_encoder.fit([['Финансы'], ['Энергетика'], ['Финансы/Энергетика']])
            
        if self.tfidf_unigram is None:
            self.tfidf_unigram = TfidfVectorizer(max_features=3000, ngram_range=(1, 1))
            
        if self.tfidf_bigram is None:
            self.tfidf_bigram = TfidfVectorizer(max_features=2000, ngram_range=(2, 2))
            
        if self.count_vec is None:
            self.count_vec = CountVectorizer(max_features=1000)
            
        if self.lda is None:
            self.lda = LatentDirichletAllocation(n_components=10, random_state=42)
            
        if self.nmf is None:
            self.nmf = NMF(n_components=10, random_state=42)
        
        # Set number of topics
        self.n_topics = self.lda.n_components
        
    def load_preprocessor(self, name, input_dir):
        """
        Load a single preprocessor.
        
        Args:
            name (str): Name of the preprocessor
            input_dir (str): Directory where preprocessors are saved
            
        Returns:
            object: Loaded preprocessor or None if not found
        """
        file_path = os.path.join(input_dir, f"{name}.pkl")
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            print(f"Warning: {name} not found at {file_path}")
            return None
        
    def clean_text(self, text):
        """Clean the text by lowercasing and removing punctuation and numbers."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        return text
    
    def lemmatize(self, text):
        """Lemmatize text using spaCy."""
        doc = self.nlp(text)
        lemmas = [token.lemma_ for token in doc if token.pos_ not in ["ADP", "CCONJ", "PART", "SCONJ", "PUNCT", "SYM"]]
        return ' '.join(lemmas)
    
    def preprocess_text(self, text):
        """Preprocess text using cleaning and lemmatization."""
        cleaned_text = self.clean_text(text)
        lemmatized_text = self.lemmatize(cleaned_text)
        return lemmatized_text
    
    def extract_features(self, text, sphere="Финансы"):
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Create sphere one-hot encoding
        sphere_data = np.array([[sphere]]) 
        encoded_sphere = self.sphere_encoder.transform(sphere_data)
        
        # Initialize features dictionary with sphere features
        features_dict = {name: value for name, value in 
                        zip(self.sphere_encoder.get_feature_names_out(['sphere']), 
                            encoded_sphere.toarray()[0])}
        
        # Add text statistics features
        tokens = processed_text.split()
        features_dict['avg_word_length'] = sum(len(word) for word in tokens) / len(tokens) if len(tokens) > 0 else 0
        features_dict['unique_words_ratio'] = len(set(tokens)) / len(tokens) if len(tokens) > 0 else 0
        
        # Add topic features if models are trained
        if hasattr(self.tfidf_unigram, 'vocabulary_') and hasattr(self.count_vec, 'vocabulary_'):
            try:
                # Transform with pre-fitted vectorizers
                unigram_features = self.tfidf_unigram.transform([processed_text])
                count_features = self.count_vec.transform([processed_text])
                
                # Generate topic features
                lda_features = self.lda.transform(count_features)
                nmf_features = self.nmf.transform(unigram_features)
                
                # Add topic features to dictionary
                for i in range(self.n_topics):
                    features_dict[f'topic_lda_{i}'] = lda_features[0][i]
                    features_dict[f'topic_nmf_{i}'] = nmf_features[0][i]
            except Exception as e:
                print(f"Warning: Error generating topic features: {e}")
        
        # Add sentence embeddings
        embeddings = self.sentence_transformer.encode([processed_text])[0]
        for i in range(len(embeddings)):
            features_dict[f'embedding_{i}'] = embeddings[i]
        
        # Create DataFrame from complete dictionary
        features_df = pd.DataFrame([features_dict])
        
        return features_df
    
    def predict(self, text, sphere="Финансы"):
        """
        Predict the sentiment/impact of a news text.
        
        Args:
            text (str): News text
            sphere (str): News sphere category
            
        Returns:
            float: Prediction value
        """
        # Extract features
        features = self.extract_features(text, sphere)
        
        # Ensure features match what the model expects
        model_features = self.model.feature_name()
        
        # Align feature columns with what the model expects
        aligned_features = pd.DataFrame(0, index=[0], columns=model_features)
        for col in features.columns:
            if col in model_features:
                aligned_features[col] = features[col].values
        
        # Make prediction
        prediction = self.model.predict(aligned_features)
        
        return prediction[0]

predictor = NewsPredictor('src/models/sphere_Финансы_model.txt')
print('predictor is loaded fully')
sentiment = predictor.predict("""Сбербанк объявил о дефолте и закрытии всего акционерного трека""", sphere="Финансы")
print(f"Predicted sentiment: {sentiment}")