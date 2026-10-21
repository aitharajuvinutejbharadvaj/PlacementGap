from dataclasses import dataclass


@dataclass
class RunBudget:
    max_usd: float = 1.0
    max_tokens: int = 30000
    spent_usd: float = 0.0
    tokens: int = 0
    degraded: bool = False

    def charge(self, cost: float, tokens: int) -> bool:
        if self.spent_usd + cost > self.max_usd or self.tokens + tokens > self.max_tokens:
            self.degraded = True
            return False
        self.spent_usd += cost
        self.tokens += tokens
        return True
