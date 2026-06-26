from config.settings import Settings
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.repositories.user_postgres_repository import UserPostgresRepository
from infrastructure.repositories.tenant_postgres_repository import TenantPostgresRepository
from infrastructure.repositories.role_postgres_repository import RolePostgresRepository
from infrastructure.repositories.membership_postgres_repository import MembershipPostgresRepository


class RepositoryType:
    USER       = "USER"
    TENANT     = "TENANT"
    ROLE       = "ROLE"
    MEMBERSHIP = "MEMBERSHIP"


class DependencyContainer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sql_session_manager = SQLSessionManager(settings)

    def create_repository(self, repository_name: str):
        if repository_name == RepositoryType.USER:
            return UserPostgresRepository(sql_session=self.sql_session_manager)
        if repository_name == RepositoryType.TENANT:
            return TenantPostgresRepository(sql_session=self.sql_session_manager)
        if repository_name == RepositoryType.ROLE:
            return RolePostgresRepository(sql_session=self.sql_session_manager)
        if repository_name == RepositoryType.MEMBERSHIP:
            return MembershipPostgresRepository(sql_session=self.sql_session_manager)
        raise ValueError(f"Repository '{repository_name}' not found in registry.")

    def close(self):
        self.sql_session_manager.close()
