#!/usr/bin/env python

import logging
log = logging.getLogger('git_repo.github')

from .base import register_target, RepositoryService
from ..exceptions import ResourceError, ResourceExistsError, ResourceNotFoundError

import github3

@register_target('hub', 'github')
class GithubService(RepositoryService):
    fqdn = 'github.com'

    def connect(self):
        self.gh = github3.login(token=self._privatekey)

    def create(self, user, repo):
        try:
            self.gh.create_repo(repo)
        except github3.models.GitHubError as err:
            if err.message == 'name already exists on this account':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error.") from err
        self.add(user=user, repo=repo, default=True)

    def fork(self, user, repo, branch='master'):
        log.info("Forking repository {}/{}…".format(user, repo))
        try:
            fork = self.gh.repository(user, repo).create_fork()
        except github3.models.GitHubError as err:
            if err.message == 'name already exists on this account':
                raise ResourceExistsError("Project already exists.") from err
            else:
                raise ResourceError("Unhandled error: {}".format(err)) from err
        self.add(user=user, repo=repo, name='upstream', alone=True)
        remote = self.add(repo=repo, user=self.gh.user().name, default=True)
        self.pull(remote, branch)
        log.info("New forked repository available at {}/{}".format(self.url_ro,
                                                                   fork.full_name))

    def delete(self, repo, user=None):
        if not user:
            user = self.gh.user().name
        try:
            repository = self.gh.repository(user, repo)
            if repository:
                result = repository.delete()
            if not repository or not result:
                raise ResourceNotFoundError("Cannot delete: repository {}/{} does not exists.".format(user, repo))
        except github3.models.GitHubError as err:
            if err.code == 403:
                raise ResourcePermissionError("You don't have enough permissions for deleting the repository. Check the namespace or the private token's privileges") from err
            raise ResourceError("Unhandled exception: {}".format(err)) from err

