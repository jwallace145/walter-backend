import json

from src.api.common.methods import HTTPStatus, Status
from src.api.common.models import Response

###############
# TEST EVENTS #
###############

EVENT = json.load(open("tst/api/data/event.json"))


def get_auth_user_event(email: str, password: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "password": password})
    return EVENT


def get_get_stock_event(symbol: str) -> dict:
    EVENT["queryStringParameters"] = {"symbol": symbol}
    return EVENT


def get_add_stock_event(stock: str, quantity: float, token: str) -> dict:
    EVENT["body"] = json.dumps({"stock": stock, "quantity": quantity})
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    return EVENT


def get_delete_stock_event(stock: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"stock": stock})
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    return EVENT


def get_get_prices_event(symbol: str, start_date: str, end_date: str) -> dict:
    EVENT["queryStringParameters"] = {
        "stock": symbol,
        "start_date": start_date,
        "end_date": end_date,
    }
    return EVENT


def get_portfolio_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_news_summary_event(symbol: str) -> dict:
    EVENT["queryStringParameters"] = {"symbol": symbol}
    return EVENT


def get_create_user_event(
    email: str, first_name: str, last_name: str, password: str
) -> dict:
    EVENT["body"] = json.dumps(
        {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        }
    )
    EVENT["headers"] = {"content-type": "application/json"}
    return EVENT


def get_get_user_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_get_newsletter_event(token: str, date: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    EVENT["queryStringParameters"] = {"date": date}
    return EVENT


def get_send_newsletter_event(token: str, page: int) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    EVENT["queryStringParameters"] = {"page": page}
    return EVENT


def get_verify_email_event(email_token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {email_token}"}
    return EVENT


def get_send_verify_email_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_change_password_event(token: str, new_password: str) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps({"new_password": new_password})
    return EVENT


def get_update_password_event(
    token: str, current_password: str, new_password: str
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {"current_password": current_password, "new_password": new_password}
    )
    return EVENT


def get_send_change_password_email_event(email: str) -> dict:
    EVENT["queryStringParameters"] = {"email": email}
    return EVENT


def get_subscribe_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_unsubscribe_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_search_stocks_event(stock: str) -> dict:
    EVENT["queryStringParameters"] = {"symbol": stock}
    return EVENT


def get_purchase_newsletter_subscription_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_verify_purchase_newsletter_subscription_event(
    token: str, session_id: str
) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    EVENT["queryStringParameters"] = {"sessionId": session_id}
    return EVENT


def get_add_transaction_event(
    token: str, account_id: str, date: str, vendor: str, amount: float
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {"account_id": account_id, "date": date, "vendor": vendor, "amount": amount}
    )
    return EVENT


def get_edit_transaction_event(
    token: str,
    transaction_date: str,
    transaction_id: str,
    date: str,
    vendor: str,
    amount: float,
    category: str,
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {
            "transaction_date": transaction_date,
            "transaction_id": transaction_id,
            "updated_date": date,
            "updated_vendor": vendor,
            "updated_amount": amount,
            "updated_category": category,
        }
    )
    return EVENT


def get_get_cash_accounts_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_create_cash_account_event(
    token: str,
    bank_name: str,
    account_name: str,
    account_type: str,
    account_last_four_numbers: str,
    account_balance: float,
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {
            "bank_name": bank_name,
            "account_name": account_name,
            "account_type": account_type,
            "account_last_four_numbers": account_last_four_numbers,
            "balance": account_balance,
        }
    )
    return EVENT


def get_update_cash_account_event(
    token: str,
    account_id: str,
    bank_name: str,
    account_name: str,
    account_last_four_numbers: str,
    account_balance: float,
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {
            "account_id": account_id,
            "bank_name": bank_name,
            "account_name": account_name,
            "account_last_four_numbers": account_last_four_numbers,
            "balance": account_balance,
        }
    )
    return EVENT


def get_delete_cash_account_event(token: str, account_id: str) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {
            "account_id": account_id,
        }
    )
    return EVENT


def get_get_transactions_event(token: str, start_date: str, end_date: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    EVENT["queryStringParameters"] = {"start_date": start_date, "end_date": end_date}
    return EVENT


def get_delete_transaction_event(token: str, date: str, transaction_id: str) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps({"date": date, "transaction_id": transaction_id})
    return EVENT


def get_create_link_token_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_exchange_public_token_event(
    token: str,
    public_token: str,
    institution_id: str,
    institution_name: str,
    accounts: [],
) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {
            "public_token": public_token,
            "institution_id": institution_id,
            "institution_name": institution_name,
            "accounts": accounts,
        }
    )
    return EVENT


def get_sync_transactions_event(access_token: str, webhook_code: str) -> dict:
    EVENT["headers"] = {
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps(
        {"access_token": access_token, "webhook_code": webhook_code}
    )
    return EVENT


def get_refresh_transactions_event(token: str) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
    }
    return EVENT


#####################
# EXPECTED RESPONSE #
#####################


def get_expected_response(
    api_name: str,
    status_code: HTTPStatus,
    status: Status,
    message: str,
    data: str = None,
) -> Response:
    return Response(
        api_name=api_name,
        http_status=status_code,
        status=status,
        message=message,
        data=data,
    )
