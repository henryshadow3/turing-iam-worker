from config.settings import Settings
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.repositories.user_postgres_repository import UserPostgresRepository
from infrastructure.repositories.tenant_postgres_repository import TenantPostgresRepository
from infrastructure.repositories.role_postgres_repository import RolePostgresRepository
from infrastructure.repositories.membership_postgres_repository import MembershipPostgresRepository
from infrastructure.repositories.access_request_postgres_repository import AccessRequestPostgresRepository
from infrastructure.repositories.application_postgres_repository import ApplicationPostgresRepository
from infrastructure.repositories.tenant_application_postgres_repository import TenantApplicationPostgresRepository
from infrastructure.repositories.application_membership_postgres_repository import ApplicationMembershipPostgresRepository
from infrastructure.repositories.tenant_application_route_postgres_repository import TenantApplicationRoutePostgresRepository
from infrastructure.repositories.membership_suspension_postgres_repository import MembershipSuspensionPostgresRepository


class RepositoryType:
    USER                     = "USER"
    TENANT                   = "TENANT"
    ROLE                     = "ROLE"
    MEMBERSHIP               = "MEMBERSHIP"
    ACCESS_REQUEST           = "ACCESS_REQUEST"
    APPLICATION              = "APPLICATION"
    TENANT_APPLICATION       = "TENANT_APPLICATION"
    APPLICATION_MEMBERSHIP   = "APPLICATION_MEMBERSHIP"
    TENANT_APPLICATION_ROUTE = "TENANT_APPLICATION_ROUTE"
    MEMBERSHIP_SUSPENSION    = "MEMBERSHIP_SUSPENSION"


class DependencyContainer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_sql_session_manager(self) -> SQLSessionManager:
        return SQLSessionManager(self.settings)

    def create_repository(self, repository_name: str, sql_session: SQLSessionManager):
        if repository_name == RepositoryType.USER:
            return UserPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.TENANT:
            return TenantPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.ROLE:
            return RolePostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.MEMBERSHIP:
            return MembershipPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.ACCESS_REQUEST:
            return AccessRequestPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.APPLICATION:
            return ApplicationPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.TENANT_APPLICATION:
            return TenantApplicationPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.APPLICATION_MEMBERSHIP:
            return ApplicationMembershipPostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.TENANT_APPLICATION_ROUTE:
            return TenantApplicationRoutePostgresRepository(sql_session=sql_session)
        if repository_name == RepositoryType.MEMBERSHIP_SUSPENSION:
            return MembershipSuspensionPostgresRepository(sql_session=sql_session)
        raise ValueError(f"Repository '{repository_name}' not found in registry.")

    def close(self):
        pass
