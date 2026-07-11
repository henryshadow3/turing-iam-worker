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
}
