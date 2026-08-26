import sys
import os
import json
import pickle

# --------------------------------------------------
# Project root
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# --------------------------------------------------
# Libraries
# --------------------------------------------------

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from preprocessing.text_preprocessing import preprocess_text


# --------------------------------------------------
# Paths
# --------------------------------------------------

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "intents.json"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "chatbot_model.pkl"
)

VECTORIZER_PATH = os.path.join(
    MODEL_DIR,
    "tfidf_vectorizer.pkl"
)


# --------------------------------------------------
# Create model directory
# --------------------------------------------------

os.makedirs(MODEL_DIR, exist_ok=True)


# --------------------------------------------------
# Load dataset
# --------------------------------------------------

print("\nLoading INGRES chatbot dataset...")

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    data = json.load(file)


# --------------------------------------------------
# Prepare training data
# --------------------------------------------------

training_sentences = []
training_labels = []

for intent in data["intents"]:

    tag = intent["tag"]

    for pattern in intent["patterns"]:

        processed_text = preprocess_text(pattern)

        if processed_text.strip():

            training_sentences.append(processed_text)
            training_labels.append(tag)


print("Dataset loaded successfully!")
print("Total training examples:", len(training_sentences))
print("Total intents:", len(set(training_labels)))


# --------------------------------------------------
# TF-IDF
# --------------------------------------------------

print("\nCreating TF-IDF vectorizer...")

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    sublinear_tf=True
)

X = vectorizer.fit_transform(training_sentences)

print("TF-IDF vectorization completed!")


# --------------------------------------------------
# Train model
# --------------------------------------------------

print("\nTraining chatbot model...")

model = LogisticRegression(
    max_iter=2000,
    C=5.0
)

model.fit(X, training_labels)

print("Model training completed!")


# --------------------------------------------------
# Save model
# --------------------------------------------------

print("\nSaving model...")

with open(MODEL_PATH, "wb") as file:
    pickle.dump(model, file)


# --------------------------------------------------
# Save vectorizer
# --------------------------------------------------

with open(VECTORIZER_PATH, "wb") as file:
    pickle.dump(vectorizer, file)


# --------------------------------------------------
# Finished
# --------------------------------------------------

print("\n========================================")
print(" INGRES CHATBOT TRAINING COMPLETED")
print("========================================")

print("\nModel saved:")
print(MODEL_PATH)

print("\nVectorizer saved:")
print(VECTORIZER_PATH)

print("\nTraining is ready.")