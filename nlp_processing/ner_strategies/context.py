from .strategies import NERStrategy, RegexStrategy, TransformerStrategy

class NERProcessor:
    """
    Contextul din Strategy Pattern.
    Acesta menține o referință către o strategie și o poate schimba din mers.
    """
    def __init__(self, strategy_type="regex"):
        # Setăm strategia inițială
        if strategy_type == "transformer":
            self._strategy = TransformerStrategy()
        else:
            self._strategy = RegexStrategy()

    def set_strategy(self, strategy: NERStrategy):
        """Permite schimbarea strategiei la runtime (ex: de la Regex la AI)."""
        print(f" [NER Engine] Schimbare strategie pe: {type(strategy).__name__}")
        self._strategy = strategy

    def process_text(self, text):
        """Deleagă execuția către strategia curentă."""
        return self._strategy.extract(text)
