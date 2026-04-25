from dataclasses import dataclass

DEFAULT_TENANT = "northwind-public"

ROLE_LEVELS = {
    "public": ["public"],
    "internal": ["public", "internal"],
    "restricted": ["public", "internal", "restricted"],
}


@dataclass(frozen=True)
class UserContext:
    user_id: str
    tenant_id: str = DEFAULT_TENANT
    roles: tuple[str, ...] = ("public",)

    def allowed_classifications(self) -> list[str]:
        levels = set()
        for r in self.roles:
            levels.update(ROLE_LEVELS.get(r, ["public"]))
        return sorted(levels)

    def can_see(self, tenant_id: str, classification: str) -> bool:
        return tenant_id == self.tenant_id and classification in self.allowed_classifications()


def anonymous_context() -> UserContext:
    return UserContext(user_id="anonymous")
