from abc import ABC, abstractmethod

class DbConnection(ABC):
    @abstractmethod
    def fetch_one(self, sql: str, params: tuple = None):
        pass
    
    @abstractmethod
    def fetch_all(self, sql: str, params: tuple = None):
        pass
    
    @abstractmethod
    def execute_and_commit(self, sql: str, params: tuple = None):
        pass