from application.actions.users.list import user_list_action
from application.actions.users.get import user_get_action
from application.actions.users.create import user_create_action
from application.actions.users.update import user_update_action
from application.actions.users.disable import user_disable_action
from application.actions.tenants.list import tenant_list_action
from application.actions.tenants.create import tenant_create_action
from application.actions.roles.list import role_list_action
from application.actions.roles.create import role_create_action
from application.actions.roles.toggle import role_toggle_action
from application.actions.memberships.list import membership_list_action
from application.actions.memberships.create import membership_create_action
from application.actions.memberships.delete import membership_delete_action
from application.actions.memberships.update import membership_update_action
from application.actions.memberships.toggle import membership_toggle_action
from application.actions.requests.list import request_list_action
from application.actions.requests.approve import request_approve_action
from application.actions.requests.reject import request_reject_action
from application.actions.members.list import member_list_action
from application.actions.members.update_role import member_update_role_action
from application.actions.members.toggle import member_toggle_action
from application.actions.applications.list import application_list_action
from application.actions.applications.toggle import application_toggle_action
from application.actions.tenant_applications.list import tenant_application_list_action
from application.actions.tenant_applications.create import tenant_application_create_action
from application.actions.tenant_applications.toggle import tenant_application_toggle_action
from application.actions.application_memberships.list import application_membership_list_action
from application.actions.application_memberships.create import application_membership_create_action
from application.actions.application_memberships.update import application_membership_update_action
from application.actions.application_memberships.toggle import application_membership_toggle_action
from application.actions.tenant_application_routes.list import tenant_application_route_list_action
from application.actions.tenant_application_routes.create import tenant_application_route_create_action
from application.actions.tenant_application_routes.update import tenant_application_route_update_action
from application.actions.tenant_application_routes.toggle import tenant_application_route_toggle_action

ACTIONS = {
    "iam.user.list.in":             user_list_action,
    "iam.user.get.in":              user_get_action,
    "iam.user.create.in":           user_create_action,
    "iam.user.update.in":           user_update_action,
    "iam.user.disable.in":          user_disable_action,
    "iam.tenant.list.in":           tenant_list_action,
    "iam.tenant.create.in":         tenant_create_action,
    "iam.role.list.in":             role_list_action,
    "iam.role.create.in":           role_create_action,
    "iam.role.toggle.in":           role_toggle_action,
    "iam.membership.list.in":       membership_list_action,
    "iam.membership.create.in":     membership_create_action,
    "iam.membership.delete.in":     membership_delete_action,
    "iam.membership.update.in":     membership_update_action,
    "iam.membership.toggle.in":     membership_toggle_action,
    "iam.request.list.in":          request_list_action,
    "iam.request.approve.in":       request_approve_action,
    "iam.request.reject.in":        request_reject_action,
    # Gestión de miembros del PROPIO tenant (admin del tenant, no superadmin).
    "iam.member.list.in":           member_list_action,
    "iam.member.update_role.in":    member_update_role_action,
    "iam.member.toggle.in":         member_toggle_action,
    # ─────────────────────────────────────────────────────────────────
    # T-SP4-T2-I1-W5 — Aplicaciones, tenant-aplicaciones, application
    # memberships (acceso real) y rutas. Familia SEPARADA de
    # iam.membership.* (afiliación pura) -- ver ADR 0001 y
    # docs/sp4-t2-i1-w5-contratos-test-report.md.
    # ─────────────────────────────────────────────────────────────────
    "iam.application.list.in":              application_list_action,
    "iam.application.toggle.in":            application_toggle_action,
    "iam.tenant_application.list.in":       tenant_application_list_action,
    "iam.tenant_application.create.in":     tenant_application_create_action,
    "iam.tenant_application.toggle.in":     tenant_application_toggle_action,
    "iam.application_membership.list.in":   application_membership_list_action,
    "iam.application_membership.create.in": application_membership_create_action,
    "iam.application_membership.update.in": application_membership_update_action,
    "iam.application_membership.toggle.in": application_membership_toggle_action,
    "iam.tenant_application_route.list.in":   tenant_application_route_list_action,
    "iam.tenant_application_route.create.in": tenant_application_route_create_action,
    "iam.tenant_application_route.update.in": tenant_application_route_update_action,
    "iam.tenant_application_route.toggle.in": tenant_application_route_toggle_action,
}

DOMAIN_EVENTS = {
    "iam.user.list.in":             [],
    "iam.user.get.in":              [],
    "iam.user.create.in":           ["iam.user.created"],
    "iam.user.update.in":           ["iam.user.updated"],
    "iam.user.disable.in":          ["iam.user.disabled"],
    "iam.tenant.list.in":           [],
    "iam.tenant.create.in":         ["iam.tenant.created"],
    "iam.role.list.in":             [],
    "iam.role.create.in":           ["iam.role.created"],
    "iam.role.toggle.in":           ["iam.role.toggled"],
    "iam.membership.list.in":       [],
    "iam.membership.create.in":     ["iam.membership.created"],
    "iam.membership.delete.in":     ["iam.membership.deleted"],
    "iam.membership.update.in":     ["iam.membership.updated"],
    "iam.membership.toggle.in":     ["iam.membership.toggled"],
    "iam.request.list.in":          [],
    "iam.request.approve.in":       ["iam.request.approved", "iam.membership.created"],
    "iam.request.reject.in":        ["iam.request.rejected"],
    # Sin eventos de dominio: la respuesta se serializa como .out y así el
    # front recibe data (los domain events la reemplazarían por un nombre
    # que turing-api no puede deserializar).
    "iam.member.list.in":           [],
    "iam.member.update_role.in":    [],
    "iam.member.toggle.in":         [],
    # Igual que el resto de la familia iam.*: sin domain events propios, la
    # respuesta se serializa como "<event>.out" (ver IAMWorkerService.HandleAction).
    "iam.application.list.in":              [],
    "iam.application.toggle.in":            ["iam.application.toggled"],
    "iam.tenant_application.list.in":       [],
    "iam.tenant_application.create.in":     ["iam.tenant_application.created"],
    "iam.tenant_application.toggle.in":     ["iam.tenant_application.toggled"],
    "iam.application_membership.list.in":   [],
    "iam.application_membership.create.in": ["iam.application_membership.created"],
    "iam.application_membership.update.in": ["iam.application_membership.updated"],
    "iam.application_membership.toggle.in": ["iam.application_membership.toggled"],
    "iam.tenant_application_route.list.in":   [],
    "iam.tenant_application_route.create.in": ["iam.tenant_application_route.created"],
    "iam.tenant_application_route.update.in": ["iam.tenant_application_route.updated"],
    "iam.tenant_application_route.toggle.in": ["iam.tenant_application_route.toggled"],
}
