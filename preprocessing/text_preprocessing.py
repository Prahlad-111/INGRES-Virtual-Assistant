import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# Initialize tools
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))


def preprocess_text(text):
    """
    Clean and preprocess user input.
    """

    # Convert text to lowercase
    text = text.lower()

    # Remove special characters and numbers
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # Tokenize text
    words = text.split()

    # Remove stopwords and apply lemmatization
    processed_words = []

    for word in words:
        if word not in stop_words:
            word = lemmatizer.lemmatize(word)
            processed_words.append(word)

    return " ".join(processed_words)


if __name__ == "__main__":
    sample_text = "Hello! Can you tell me about INGRES services?"

    result = preprocess_text(sample_text)

    print("Original Text:")
    print(sample_text)

    print("\nProcessed Text:")
    print(result)