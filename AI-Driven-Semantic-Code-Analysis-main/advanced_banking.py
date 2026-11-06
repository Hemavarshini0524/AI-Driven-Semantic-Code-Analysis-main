{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
from abc import ABC, abstractmethod\
from dataclasses import dataclass, field\
from datetime import datetime, timedelta\
from collections import defaultdict\
from threading import Lock\
from typing import Dict, List, Optional\
from functools import wraps\
import logging\
import uuid\
\
\
logging.basicConfig(level=logging.INFO)\
\
\
# Custom exceptions\
class BankingError(Exception):\
    pass\
\
\
class InsufficientFundsError(BankingError):\
    pass\
\
\
class FraudDetectedError(BankingError):\
    pass\
\
\
# Decorator for transaction logging\
def audit_transaction(func):\
    @wraps(func)\
    def wrapper(*args, **kwargs):\
        logging.info("Transaction started")\
        result = func(*args, **kwargs)\
        logging.info("Transaction completed")\
        return result\
    return wrapper\
\
\
# Transaction data model\
@dataclass\
class Transaction:\
    transaction_id: str\
    sender_id: str\
    receiver_id: str\
    amount: float\
    timestamp: datetime = field(default_factory=datetime.now)\
    status: str = "PENDING"\
\
\
# Abstract account\
class BankAccount(ABC):\
\
    def __init__(self, account_id: str, balance: float):\
        self.account_id = account_id\
        self.balance = balance\
        self.transactions: List[Transaction] = []\
        self.lock = Lock()\
\
    @abstractmethod\
    def calculate_interest(self) -> float:\
        pass\
\
    def deposit(self, amount: float):\
        if amount <= 0:\
            raise BankingError("Invalid deposit amount")\
\
        with self.lock:\
            self.balance += amount\
\
    def withdraw(self, amount: float):\
        with self.lock:\
            if amount > self.balance:\
                raise InsufficientFundsError("Insufficient balance")\
\
            self.balance -= amount\
\
\
class SavingsAccount(BankAccount):\
\
    def calculate_interest(self) -> float:\
        return self.balance * 0.04\
\
\
class CurrentAccount(BankAccount):\
\
    def calculate_interest(self) -> float:\
        return 0.0\
\
\
# Customer entity\
@dataclass\
class Customer:\
    customer_id: str\
    name: str\
    email: str\
    accounts: List[BankAccount] = field(default_factory=list)\
\
    def add_account(self, account: BankAccount):\
        self.accounts.append(account)\
\
\
# Fraud detection engine\
class FraudDetector:\
\
    def __init__(self, transaction_limit: float):\
        self.transaction_limit = transaction_limit\
        self.transaction_history = defaultdict(list)\
\
    def detect_fraud(self, transaction: Transaction) -> bool:\
\
        if transaction.amount > self.transaction_limit:\
            return True\
\
        recent_transactions = self.transaction_history[\
            transaction.sender_id\
        ]\
\
        recent_count = sum(\
            1 for item in recent_transactions\
            if item.timestamp > datetime.now() - timedelta(minutes=5)\
        )\
\
        if recent_count >= 5:\
            return True\
\
        recent_transactions.append(transaction)\
        return False\
\
\
# Transaction processor\
class TransactionProcessor:\
\
    def __init__(self, fraud_detector: FraudDetector):\
        self.fraud_detector = fraud_detector\
        self.transaction_lock = Lock()\
\
    @audit_transaction\
    def transfer(\
        self,\
        sender: BankAccount,\
        receiver: BankAccount,\
        amount: float\
    ) -> Transaction:\
\
        transaction = Transaction(\
            transaction_id=str(uuid.uuid4()),\
            sender_id=sender.account_id,\
            receiver_id=receiver.account_id,\
            amount=amount\
        )\
\
        with self.transaction_lock:\
\
            if self.fraud_detector.detect_fraud(transaction):\
                transaction.status = "REJECTED"\
                raise FraudDetectedError("Suspicious transaction detected")\
\
            sender.withdraw(amount)\
\
            try:\
                receiver.deposit(amount)\
            except Exception:\
                sender.deposit(amount)\
                raise\
\
            transaction.status = "SUCCESS"\
\
            sender.transactions.append(transaction)\
            receiver.transactions.append(transaction)\
\
        return transaction\
\
\
# Generic repository\
class Repository[T]:\
\
    def __init__(self):\
        self.records: Dict[str, T] = \{\}\
\
    def save(self, key: str, value: T):\
        self.records[key] = value\
\
    def find(self, key: str) -> Optional[T]:\
        return self.records.get(key)\
\
    def find_all(self) -> List[T]:\
        return list(self.records.values())\
\
\
# Banking service\
class BankingService:\
\
    def __init__(self):\
        self.customers = Repository[Customer]()\
        self.accounts = Repository[BankAccount]()\
\
        self.fraud_detector = FraudDetector(100000)\
        self.processor = TransactionProcessor(self.fraud_detector)\
\
    def register_customer(self, customer: Customer):\
        self.customers.save(customer.customer_id, customer)\
\
        for account in customer.accounts:\
            self.accounts.save(account.account_id, account)\
\
    def transfer_money(\
        self,\
        sender_id: str,\
        receiver_id: str,\
        amount: float\
    ):\
\
        sender = self.accounts.find(sender_id)\
        receiver = self.accounts.find(receiver_id)\
\
        if sender is None or receiver is None:\
            raise BankingError("Account not found")\
\
        return self.processor.transfer(\
            sender,\
            receiver,\
            amount\
        )\
\
    def generate_bank_report(self):\
\
        report = \{\
            "total_customers": len(self.customers.find_all()),\
            "total_accounts": len(self.accounts.find_all()),\
            "total_balance": sum(\
                account.balance\
                for account in self.accounts.find_all()\
            )\
        \}\
\
        return report\
\
\
# Main application\
class BankingApplication:\
\
    def __init__(self):\
        self.service = BankingService()\
\
    def setup(self):\
\
        customer1 = Customer(\
            "C001",\
            "Rahul",\
            "rahul@example.com"\
        )\
\
        customer2 = Customer(\
            "C002",\
            "Anita",\
            "anita@example.com"\
        )\
\
        account1 = SavingsAccount("A101", 50000)\
        account2 = CurrentAccount("A102", 25000)\
\
        customer1.add_account(account1)\
        customer2.add_account(account2)\
\
        self.service.register_customer(customer1)\
        self.service.register_customer(customer2)\
\
    def run(self):\
\
        self.setup()\
\
        try:\
            transaction = self.service.transfer_money(\
                "A101",\
                "A102",\
                5000\
            )\
\
            print("Transaction:", transaction.status)\
\
        except BankingError as error:\
            logging.error("Banking error: %s", error)\
\
        print("\\nBANK REPORT")\
        print(self.service.generate_bank_report())\
\
\
if __name__ == "__main__":\
    application = BankingApplication()\
    application.run()\
}