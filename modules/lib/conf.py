from config import config as base_config

class Config:
    """
    Обёртка над config, которая автоматически добавляет
    префикс к переменным.
    """
    prefix = "Triumvirate"
    def getint(self, key):
        return base_config.getint(f"{self.prefix}.{key}")

    def get(self, key):
        return base_config.get(f"{self.prefix}.{key}")

    def set(self, key, val):
        base_config.set(f"{self.prefix}.{key}", val)

config = Config()
