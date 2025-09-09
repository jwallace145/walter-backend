from src.database.transactions.models import TransactionType
from src.plaid.models import PersonalFinanceCategories

PERSONAL_FINANCE_CATEGORY_TO_TRANSACTION_TYPE = {
    PersonalFinanceCategories.ENTERTAINMENT: TransactionType.BANKING,
    PersonalFinanceCategories.FOOD_AND_DRINK: TransactionType.BANKING,
    PersonalFinanceCategories.GENERAL_MERCHANDISE: TransactionType.BANKING,
    PersonalFinanceCategories.GENERAL_SERVICES: TransactionType.BANKING,
    PersonalFinanceCategories.INCOME: TransactionType.BANKING,
    PersonalFinanceCategories.LOAN_PAYMENTS: TransactionType.BANKING,
    PersonalFinanceCategories.PERSONAL_CARE: TransactionType.BANKING,
    PersonalFinanceCategories.TRANSPORTATION: TransactionType.BANKING,
    PersonalFinanceCategories.TRAVEL: TransactionType.BANKING,
}


def get_transaction_type_from_plaid_category(
    category: str,
) -> TransactionType:
    # this method marshals the personal finance category string into a PersonalFinanceCategories enum
    # throws an exception if the string is not valid
    personal_finance_category = PersonalFinanceCategories.from_string(category)

    # attempt to map the enum to a TransactionType enum
    try:
        transaction_type = PERSONAL_FINANCE_CATEGORY_TO_TRANSACTION_TYPE[
            personal_finance_category
        ]
    except KeyError:
        raise ValueError(f"Invalid personal finance category '{category}'!")

    return transaction_type
