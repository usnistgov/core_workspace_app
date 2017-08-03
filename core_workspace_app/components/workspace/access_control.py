"""
    Workspace access control
"""
from core_main_app.utils.access_control.exceptions import AccessControlError


def can_delete_workspace(func, workspace, user):
    """ Can user delete a workspace.

    Args:
        func:
        workspace:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(workspace, user)

    _check_is_owner_workspace(workspace, user)
    return func(workspace, user)


def _check_is_owner_workspace(workspace, user):
    """ Check that user is the owner of the workspace.

    Args:
        workspace:
        user:

    Returns:

    """
    if workspace.owner != str(user.id):
        raise AccessControlError("The user does not have the permission. The user is not the owner of this workspace.")