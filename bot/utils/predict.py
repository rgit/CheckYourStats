import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.ensemble import RandomForestClassifier
import string
from nltk.corpus import stopwords
from bot.config import Config


class Model:
    def __init__(self):
        self._initialize()

    def _initialize(self):
        self.data = pd.read_csv(Config.DATASET_PATH, skiprows=1, names=["user_id", "chat_id", "message", "spam"],
                                sep=",", error_bad_lines=False, encoding="utf-8", quoting=1)
        self.train = self._train()

    @staticmethod
    def _process_text(text: str):
        no_punctuation = "".join([character for character in text if character not in string.punctuation])
        stopwords_list = [stopword for stopword in stopwords.words("russian") if
                          stopword not in ["я", "вы", "ты", "они", "мы", "она", ]]
        return [word for word in no_punctuation.split() if word.lower() not in stopwords_list]

    def _train(self):
        transformer = CountVectorizer(analyzer=self._process_text).fit(self.data["message"].astype("U"))
        messages = transformer.transform(self.data["message"].astype("U"))
        tfidf_transformer = TfidfTransformer().fit(messages)
        tfidf = tfidf_transformer.transform(messages)

        classifier = RandomForestClassifier(n_estimators=10, criterion="entropy", random_state=0)
        classifier = classifier.fit(tfidf, self.data["spam"])
        accuracy = accuracy_score(self.data["spam"], classifier.predict(messages))
        return classifier, transformer, accuracy

    def predict(self, text: str):
        classifier, transformer, _ = self.train
        vector = transformer.transform([text]).toarray()
        if classifier.predict(vector)[0]:
            return True
        else:
            return False

    def add_to_dataset(self, user_id: int, chat_id: int, text: str, prediction: bool):
        spam = 1 if prediction else 0
        frame = pd.DataFrame([{"user_id": user_id, "chat_id": chat_id, "message": text, "spam": spam}],
                             index=[len(self.data["user_id"]) + 1])
        frame = pd.concat([self.data, frame], ignore_index=False)
        frame.to_csv(Config.DATASET_PATH, sep=",", encoding="utf-8")
        self._initialize()
        return True

    def set_spam_mark(self, text: str, spam: bool):
        spam = 1 if spam else 0
        self.data["spam"] = np.where(self.data["message"] == text, spam, self.data["spam"])
        self.data.to_csv(Config.DATASET_PATH, sep=",", encoding="utf-8")
        self._initialize()
        return True

    def get_random_row(self):
        return self.data["message"][np.random.choice(self.data.shape[0], 1)].values[0]

    def get_info(self, user_id: int = None):
        if user_id:
            total_count = len(self.data.query(f"user_id == '{user_id}'"))
            total_spam = len(self.data.query(f"user_id == '{user_id}' and spam == 1"))
            total_not_spam = total_count - total_spam
            return [total_count, total_spam, total_not_spam]
        else:
            total_count = len(self.data)
            total_spam = len(self.data.query("spam == 1"))
            return [total_count, total_spam, self.train[2]]
