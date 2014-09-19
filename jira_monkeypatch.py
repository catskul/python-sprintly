import jira
import requests
import json

def jira_get_users_monkeypatch(self, proj_key):
    api_call = 'user/permission/search?permissions=COMMENT_ISSUE&projectKey=%s&username='%proj_key
    rq = requests.get( self._get_url( api_call ), auth=self._session.auth )
    jir_users  = [ jira.client.User( self._options, self._session, data ) for data in json.loads( rq.content ) ]

    return jir_users


def jira_get_all_users_monkeypatch(self,projects=None):
    jir_users = set()
    projects = projects or self.projects()
    for proj in projects:
        jir_users.update( set(self.get_users(proj.key)) )

    return list(jir_users)


def jira_user__hash__monkeypatch(self):
    return hash(self.key)


def jira_user__eq__monkeypatch(self,other):
    return self.__hash__() == other.__hash__()

def monkeypatch_jira():
    print "Warning monkeypatching jira!"
    jira.client.JIRA.get_users     = jira_get_users_monkeypatch
    jira.client.JIRA.get_all_users = jira_get_all_users_monkeypatch
    jira.client.User.__hash__      = jira_user__hash__monkeypatch
    jira.client.User.__eq__        = jira_user__eq__monkeypatch
