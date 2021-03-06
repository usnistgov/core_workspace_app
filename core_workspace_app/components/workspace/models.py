"""
Workspace model
"""
from django_mongoengine import fields, Document
from mongoengine import errors as mongoengine_errors
from mongoengine.queryset.visitor import Q

from core_main_app.commons import exceptions
from core_main_app.commons.regex import NOT_EMPTY_OR_WHITESPACES


class Workspace(Document):
    """
        Workspace class.
    """

    title = fields.StringField(unique=True, blank=False, regex=NOT_EMPTY_OR_WHITESPACES)
    owner = fields.StringField(blank=False)
    read_perm_id = fields.StringField(blank=False)
    write_perm_id = fields.StringField(blank=False)

    @staticmethod
    def check_if_workspace_already_exists(title):
        """ Check if a workspace with the same title exists (case insensitive).

        Args:
            title

        Returns:
        """
        return Workspace.objects.filter(title__iexact=title).exists()

    @staticmethod
    def get_all():
        """ Get all workspaces.

        Returns:

        """
        return Workspace.objects.all()

    @staticmethod
    def get_all_by_owner(user_id):
        """ Get all workspaces created by the given user id.

        Args:
            user_id

        Returns:

        """
        return Workspace.objects(owner=str(user_id)).all()

    @staticmethod
    def get_by_id(workspace_id):
        """ Return the workspace with the given id.

        Args:
            workspace_id

        Returns:
            Workspace (obj): Workspace object with the given id

        """
        try:
            return Workspace.objects.get(pk=str(workspace_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all_workspaces_with_read_access_by_user_id(user_id, read_permissions):
        """ Get all workspaces with read access for the given user id.

        Args:
            user_id
            read_permissions

        Returns:

        """
        return Workspace.objects(Q(owner=str(user_id)) | Q(read_perm_id__in=read_permissions)).all()

    @staticmethod
    def get_all_workspaces_with_write_access_by_user_id(user_id, write_permissions):
        """ Get all workspaces with write access for the given user id.

        Args:
            user_id
            write_permissions

        Returns:

        """
        return Workspace.objects(Q(owner=str(user_id)) | Q(write_perm_id__in=write_permissions)).all()

    @staticmethod
    def get_all_workspaces_with_read_access_not_owned_by_user_id(user_id, read_permissions):
        """ Get all workspaces with read access not owned by the given user id.

        Args:
            user_id
            read_permissions

        Returns:

        """

        return Workspace.objects(owner__ne=str(user_id), read_perm_id__in=read_permissions).all()

    @staticmethod
    def get_all_workspaces_with_write_access_not_owned_by_user_id(user_id, write_permissions):
        """ Get all workspaces with write access not owned by the given user id.

        Args:
            user_id
            write_permissions

        Returns:

        """
        return Workspace.objects(owner__ne=str(user_id), write_perm_id__in=write_permissions).all()

    @staticmethod
    def get_all_other_public_workspaces(user_id, public_permissions):
        """ Get all other public workspaces.

        Args:
            user_id
            public_permissions

        Returns:

        """
        return Workspace.objects(owner__ne=str(user_id), read_perm_id__in=public_permissions).all()

    @staticmethod
    def get_non_public_workspace_owned_by_user_id(user_id, public_permissions):
        """ Get the non public workspaces owned by the given user id.

        Args:
            user_id
            public_permissions

        Returns:

        """
        return Workspace.objects(owner=str(user_id), read_perm_id__nin=public_permissions).all()

    @staticmethod
    def get_public_workspaces_owned_by_user_id(user_id, public_permissions):
        """ Get the public workspaces owned the given user id.

        Args:
            user_id
            public_permissions

        Returns:

        """
        return Workspace.objects(owner=str(user_id), read_perm_id__in=public_permissions).all()
