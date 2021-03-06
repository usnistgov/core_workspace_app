""" Ajax API
"""
import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader

import core_workspace_app.constants as workspace_constants
from core_main_app.commons.exceptions import DoesNotExist, NotUniqueError
from core_main_app.components.data import api as data_api
from core_main_app.components.group import api as group_api
from core_main_app.components.user import api as user_api
from core_main_app.utils.access_control.exceptions import AccessControlError
from core_workspace_app import constants
from core_workspace_app.utils import group as group_utils
from core_workspace_app.components.data import api as data_workspace_api
from core_workspace_app.components.workspace import api as workspace_api
from core_workspace_app.forms import ChangeWorkspaceForm, UserRightForm, GroupRightForm


def set_public_workspace(request):
    """ Set a workspace public.

    Args:
        request:

    Returns:
    """
    workspace_id_list = request.POST.getlist('workspace_id[]', [])
    try:
        list_workspace = workspace_api.get_by_id_list(workspace_id_list)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    try:
        for workspace in list_workspace:
            workspace_api.set_workspace_public(workspace)
    except:
        return HttpResponseBadRequest("Something wrong happened.")

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def assign_workspace(request):
    """ Assign the record to a workspace.

    Args:
        request:

    Returns:
    """
    document_ids = request.POST.getlist('document_id[]', [])
    workspace_id = request.POST.get('workspace_id', None)

    for data_id in document_ids:
        try:
            data_workspace_api.assign(data_api.get_by_id(data_id, request.user),
                                      workspace_api.get_by_id(str(workspace_id)),
                                      request.user)
        except Exception, exc:
            return HttpResponseBadRequest(exc.message)

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def load_form_change_workspace(request):
    """ Load the form to list the workspaces.

    Args:
        request:

    Returns:
    """
    document_ids = request.POST.getlist('document_id[]', [])
    list_workspace = set()
    try:
        list_data = data_api.get_by_id_list(document_ids, request.user)
        for data in list_data:
            if hasattr(data, 'workspace') and data.workspace is not None:
                list_workspace.add(data.workspace)
    except:
       pass

    try:
        form = ChangeWorkspaceForm(request.user, list(list_workspace))
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except:
        return HttpResponseBadRequest("Something wrong happened.")

    context = {
        "assign_workspace_form": form
    }

    return HttpResponse(json.dumps({'form': loader.render_to_string(constants.MODAL_ASSIGN_WORKSPACE_FORM, context)}),
                        'application/javascript')


def create_workspace(request):
    """ Create a workspace.

    Args:
        request

    Returns:
    """
    name_workspace = request.POST.get('name_workspace', None)
    try:
        workspace_api.create_and_save(request.user.id, name_workspace)
    except NotUniqueError:
        return HttpResponseBadRequest("A workspace called "
                                      + name_workspace +
                                      " already exists. Please change the name and try again.")
    except Exception:
        return HttpResponseBadRequest("A problem occurred while creating the workspace.")
    return HttpResponse(json.dumps({}), content_type='application/javascript')


def load_add_user_form(request):
    """ Load the form to list the users with no access to the workspace.

    Args:
        request:

    Returns:
    """
    workspace_id = request.POST.get('workspace_id', None)
    try:
        workspace = workspace_api.get_by_id(str(workspace_id))
    except Exception, exc:
        return HttpResponseBadRequest(exc.message)

    try:
        # We retrieve all users with no access
        users_with_no_access = list(workspace_api.get_list_user_with_no_access_workspace(workspace, request.user))

        # We remove the owner of the workspace
        users_with_no_access.remove(user_api.get_user_by_id(workspace.owner))

        if len(users_with_no_access) == 0:
            return HttpResponseBadRequest("There is no users that can be added.")

        form = UserRightForm(users_with_no_access)
    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except:
        return HttpResponseBadRequest("Something wrong happened.")

    context = {
        "add_user_form": form
    }

    return HttpResponse(json.dumps({'form': loader.render_to_string(constants.MODAL_ADD_USER_FORM, context)}),
                        'application/javascript')


def add_user_right_to_workspace(request):
    """ Add rights to user for the workspace.

    Args:
        request

    Returns
    """
    workspace_id = request.POST.get('workspace_id', None)
    users_ids = request.POST.getlist('users_id[]', [])
    is_read_checked = request.POST.get('read', None) == 'true'
    is_write_checked = request.POST.get('write', None) == 'true'

    if len(users_ids) == 0:
        return HttpResponseBadRequest("You need to select at least one user.")
    if not is_read_checked and not is_write_checked:
        return HttpResponseBadRequest("You need to select at least one permission (read and/or write).")

    try:
        workspace = workspace_api.get_by_id(str(workspace_id))
        for user in user_api.get_all_users_by_list_id(users_ids):
            if is_read_checked:
                workspace_api.add_user_read_access_to_workspace(workspace, user, request.user)
            if is_write_checked:
                workspace_api.add_user_write_access_to_workspace(workspace, user, request.user)
    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except Exception, exc:
        return HttpResponseBadRequest('Something wrong happened.')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def switch_right(request):
    """ Switch user's right for the workspace.

    Args:
        request

    Returns
    """

    workspace_id = request.POST.get('workspace_id', None)
    object_id = request.POST.get('object_id', None)
    group_or_user = request.POST.get('group_or_user', None)
    action = request.POST.get('action', None)
    value = request.POST.get('value', None) == 'true'

    try:
        workspace = workspace_api.get_by_id(str(workspace_id))

        if group_or_user == constants.USER:
            _switch_user_right(object_id, action, value, workspace, request.user)
        if group_or_user == constants.GROUP:
            _switch_group_right(object_id, action, value, workspace, request.user)

    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except Exception, exc:
        return HttpResponseBadRequest('Something wrong happened.')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def _switch_user_right(user_id, action, value, workspace, request_user):
    """ Change the user rights to the workspace.

    Args:
        user_id:
        action:
        value:
        workspace:
        request_user:

    Returns:
    """
    user = user_api.get_user_by_id(user_id)

    if action == workspace_constants.ACTION_READ:
        if value:
            workspace_api.add_user_read_access_to_workspace(workspace, user, request_user)
        else:
            workspace_api.remove_user_read_access_to_workspace(workspace, user, request_user)
    elif action == workspace_constants.ACTION_WRITE:
        if value:
            workspace_api.add_user_write_access_to_workspace(workspace, user, request_user)
        else:
            workspace_api.remove_user_write_access_to_workspace(workspace, user, request_user)


def _switch_group_right(group_id, action, value, workspace, request_user):
    """ Change the group rights to the workspace.

    Args:
        group_id:
        action:
        value:
        workspace:
        request_user:

    Returns:
    """
    group = group_api.get_group_by_id(group_id)

    if action == workspace_constants.ACTION_READ:
        if value:
            workspace_api.add_group_read_access_to_workspace(workspace, group, request_user)
        else:
            workspace_api.remove_group_read_access_to_workspace(workspace, group, request_user)
    elif action == workspace_constants.ACTION_WRITE:
        if value:
            workspace_api.add_group_write_access_to_workspace(workspace, group, request_user)
        else:
            workspace_api.remove_group_write_access_to_workspace(workspace, group, request_user)


def remove_user_or_group_rights(request):
    """ Remove user's right for the workspace.

    Args:
        request

    Returns
    """

    workspace_id = request.POST.get('workspace_id', None)
    object_id = request.POST.get('object_id', None)
    group_or_user = request.POST.get('group_or_user', None)

    try:
        workspace = workspace_api.get_by_id(str(workspace_id))
        if group_or_user == workspace_constants.USER:
            _remove_user_rights(object_id, workspace, request.user)
        if group_or_user == workspace_constants.GROUP:
            _remove_group_rights(object_id, workspace, request.user)

    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except Exception, exc:
        return HttpResponseBadRequest('Something wrong happened.')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def _remove_user_rights(object_id, workspace, request_user):
    """ Remove all user rights on the workspace.

    Args:
        object_id:
        workspace:
        request_user:

    Returns:
    """
    user = user_api.get_user_by_id(object_id)
    workspace_api.remove_user_read_access_to_workspace(workspace, user, request_user)
    workspace_api.remove_user_write_access_to_workspace(workspace, user, request_user)


def _remove_group_rights(object_id, workspace, request_user):
    """ Remove all group rights on the workspace.

    Args:
        object_id:
        workspace:
        request_user:

    Returns:
    """
    group = group_api.get_group_by_id(object_id)
    workspace_api.remove_group_read_access_to_workspace(workspace, group, request_user)
    workspace_api.remove_group_write_access_to_workspace(workspace, group, request_user)


def load_add_group_form(request):
    """ Load the form to list the groups with no access to the workspace.

    Args:
        request:

    Returns:
    """
    workspace_id = request.POST.get('workspace_id', None)
    try:
        workspace = workspace_api.get_by_id(str(workspace_id))
    except Exception, exc:
        return HttpResponseBadRequest(exc.message)

    try:
        # We retrieve all groups with no access
        groups_with_no_access = list(workspace_api.get_list_group_with_no_access_workspace(workspace, request.user))

        group_utils.remove_list_object_from_list(groups_with_no_access,
                                                 [group_api.get_anonymous_group(), group_api.get_default_group()])
        if len(groups_with_no_access) == 0:
            return HttpResponseBadRequest("There is no groups that can be added.")

        form = GroupRightForm(groups_with_no_access)
    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except:
        return HttpResponseBadRequest("Something wrong happened.")

    context = {
        "add_group_form": form
    }

    return HttpResponse(json.dumps({'form': loader.render_to_string(constants.MODAL_ADD_GROUP_FORM, context)}),
                        'application/javascript')


def add_group_right_to_workspace(request):
    """ Add rights to group for the workspace.

    Args:
        request

    Returns
    """
    workspace_id = request.POST.get('workspace_id', None)
    groups_ids = request.POST.getlist('groups_id[]', [])
    is_read_checked = request.POST.get('read', None) == 'true'
    is_write_checked = request.POST.get('write', None) == 'true'

    if len(groups_ids) == 0:
        return HttpResponseBadRequest("You need to select at least one group.")
    if not is_read_checked and not is_write_checked:
        return HttpResponseBadRequest("You need to select at least one permission (read and/or write).")

    try:
        workspace = workspace_api.get_by_id(str(workspace_id))
        for group in group_api.get_all_groups_by_list_id(groups_ids):
            if is_read_checked:
                workspace_api.add_group_read_access_to_workspace(workspace, group, request.user)
            if is_write_checked:
                workspace_api.add_group_write_access_to_workspace(workspace, group, request.user)
    except AccessControlError, ace:
        return HttpResponseBadRequest(ace.message)
    except DoesNotExist, dne:
        return HttpResponseBadRequest(dne.message)
    except Exception, exc:
        return HttpResponseBadRequest('Something wrong happened.')

    return HttpResponse(json.dumps({}), content_type='application/javascript')
