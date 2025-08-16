from dataclasses import dataclass
from typing import List

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from src.config import CONFIG
from src.database.transactions.models import TransactionCategory
from src.utils.log import Logger

log = Logger(__name__).get_logger()

# TODO: Rename to TransactionsCategorizerMLP


@dataclass
class ExpenseCategorizerMLP:
    """
    WalterAI: Expense Categorizer Multilayer Perceptron (MLP)

    This class is responsible for categorizing user expenses
    as they are added to WalterDB. The expense categorization
    logic is powered by a multilayer perceptron model trained
    on user expense data. The model is trained ahead of time
    and lazily loaded during categorization.
    """

    HIDDEN_LAYER_SIZES = CONFIG.expense_categorization.num_hidden_layers
    LABEL_ENCODER_FILE_NAME = "expense_category_encoder.pkl"
    PIPELINE_FILE_NAME = "expense_categorization_pipeline.pkl"

    expense_category_encoder: LabelEncoder = None  # lazy init
    expense_categorization_pipeline: Pipeline = None  # lazy init

    def __post_init__(self) -> None:
        log.debug("Creating ExpenseCategorizer...")

    def categorize(self, vendor: str, amount: float) -> TransactionCategory:
        """
        Categorize the user expense by vendor and amount.

        This method categorizes the user expense with the
        multilayer perceptron model contained within this
        class. The MLP model is pretrained and therefore
        only invoked during categorization to ensure speed.
        The required encoder and pipeline are lazily loaded
        from the Expenses bucket before categorization.

        Args:
            vendor: The name of the vendor.
            amount: The amount of the expense.

        Returns:
            The expense category of the expense.
        """
        log.info(f"Categorizing expense vendor: '{vendor}' amount: '{amount}'...")

        self._init_label_encoder()
        self._init_pipeline()

        features = np.array([[amount, vendor]], dtype=object)
        expense_category_encoded = self.expense_categorization_pipeline.predict(
            features
        )
        expense_category = self.expense_category_encoder.inverse_transform(
            expense_category_encoded
        )[0]
        expense_category = TransactionCategory.from_string(expense_category)

        log.info(f"Expense categorized as '{expense_category}'!")

        return expense_category

    def train(
        self, vendors: List[str], amounts: List[float], categories: List[str]
    ) -> None:
        log.info("Training expense categorizer...")
        features = np.array(list(zip(amounts, vendors)), dtype=object)
        targets = np.array(categories)
        label_encoder = LabelEncoder()
        targets_encoded = label_encoder.fit_transform(targets)
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), [0]),  # 'amount'
                ("cat", OneHotEncoder(handle_unknown="ignore"), [1]),  # 'vendor'
            ]
        )
        pipeline = Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "mlp",
                    MLPClassifier(
                        hidden_layer_sizes=(ExpenseCategorizerMLP.HIDDEN_LAYER_SIZES,),
                        max_iter=300,
                        solver="adam",
                        random_state=1,
                    ),
                ),
            ]
        )
        features_train, features_test, targets_train, targets_test = train_test_split(
            features, targets_encoded, test_size=0.2, random_state=42
        )
        pipeline.fit(features_train, targets_train)
        joblib.dump(label_encoder, ExpenseCategorizerMLP.LABEL_ENCODER_FILE_NAME)
        joblib.dump(pipeline, ExpenseCategorizerMLP.PIPELINE_FILE_NAME)

    def _init_label_encoder(self) -> None:
        """Lazily initialize the expense category encoder."""
        if self.expense_category_encoder is None:
            log.debug("Loading expense category encoder...")
            self.expense_category_encoder = joblib.load(
                ExpenseCategorizerMLP.LABEL_ENCODER_FILE_NAME
            )

    def _init_pipeline(self) -> None:
        """Lazily initialize the expense categorization pipeline."""
        if self.expense_categorization_pipeline is None:
            log.debug("Loading expense categorization pipeline...")
            self.expense_categorization_pipeline = joblib.load(
                ExpenseCategorizerMLP.PIPELINE_FILE_NAME
            )
