# Import resources as needed to avoid circular dependencies
from .auth_resource import (
    LoginResource,
    LogoutResource,
    RefreshToken,
    SessionRotationResource,
    SessionCleanupResource,
    SessionActivityResource,
    SessionManagementResource,
    UserStatusResource as AuthUserStatusResource,
    EndAllSessionsResource
)

from .user_resource import (
    UserResource,
    UserListResource,
    UserSessionResource,
    SingleUserSessionResource,
    PasswordUpdateResource,
    AllUserSessionsResource,
    UserStatusResource,
    UserActivityResource,
    RoleHierarchyResource,
    RoleValidationResource,
    UserPermissionsResource,
    CheckPermissionResource,
    ExpiredSessionsResource,
    SessionAnalyticsResource,
    SessionActivityResource,
    UserTimelineResource
)

from .access_resource import (
    AccessResource,
    SingleAccessResource,
    AccessPermissionsResource,
    CheckPermissionsResource,
    RolePermissionsResource,
    AccessTemplatesResource,
    BulkAccessUpdateResource
)

from .role_resource import (
    RolesResource,
    RoleByIdResource,
    RoleHierarchyResource,
    RoleAnalyticsResource,
    RoleValidationResource,
    RoleStatusResource
)

# Other resources
from .admin_resource import AdminResource
from .audit_trail_resource import AuditTrailResource
from .bank_resource import BankResource
from .branch_resource import BranchResource
from .dropdown_resource import DropdownResource
from .help_resource import HelpStepResource
from .impact_product_resource import ImpactProductResource
from .inception_resource import InceptionResource
from .log_resource import LogResource
from .manager_resource import ManagerSalesExecutiveResource
from .paypoint_resource import PaypointResource
from .query_resource import QueryResource
from .query_response_resource import QueryResponseResource
from .report_resource import ReportResource
from .retention_resource import RetentionPolicyResource
from .sales_executive_resource import SalesExecutiveResource
from .sales_performance_resource import SalesPerformanceResource
from .sales_resource import SaleListResource
from .sales_target_resource import SalesTargetResource
from .sla_resource import SLAResource
from .under_inv_resource import UnderInvestigationResource

__all__ = [
    # Auth resources
    'LoginResource', 'LogoutResource', 'RefreshToken', 'SessionRotationResource',
    'SessionCleanupResource', 'SessionActivityResource', 'SessionManagementResource',
    'AuthUserStatusResource', 'EndAllSessionsResource',

    # User resources
    'UserResource', 'UserListResource', 'UserSessionResource',
    'SingleUserSessionResource', 'PasswordUpdateResource', 'AllUserSessionsResource',
    'UserStatusResource', 'UserActivityResource', 'RoleHierarchyResource',
    'RoleValidationResource', 'UserPermissionsResource', 'CheckPermissionResource',
    'ExpiredSessionsResource', 'SessionAnalyticsResource', 'SessionActivityResource',
    'UserTimelineResource',

    # Access resources
    'AccessResource', 'SingleAccessResource', 'AccessPermissionsResource',
    'CheckPermissionsResource', 'RolePermissionsResource', 'AccessTemplatesResource',
    'BulkAccessUpdateResource',

    # Role resources
    'RolesResource', 'RoleByIdResource', 'RoleHierarchyResource',
    'RoleAnalyticsResource', 'RoleValidationResource', 'RoleStatusResource',

    # Other resources
    'AdminResource', 'AuditTrailResource', 'BankResource', 'BranchResource',
    'DropdownResource', 'HelpStepResource', 'ImpactProductResource',
    'InceptionResource', 'LogResource', 'ManagerSalesExecutiveResource',
    'PaypointResource', 'QueryResource', 'QueryResponseResource',
    'ReportResource', 'RetentionPolicyResource', 'SalesExecutiveResource',
    'SalesPerformanceResource', 'SaleListResource', 'SalesTargetResource',
    'SLAResource', 'UnderInvestigationResource'
]
