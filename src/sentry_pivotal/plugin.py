"""
sentry_pivotal.plugin
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django import forms
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.bases.issue import IssuePlugin

import pyvotal
import sentry_pivotal


class PivotalTrackerOptionsForm(forms.Form):
    token = forms.CharField(label=_('API Token'),
        widget=forms.TextInput(attrs={'class': 'span3', 'placeholder': 'e.g. a9877d72b6d13b23410a7109b35e88bc'}),
        help_text=mark_safe(_('Enter your API Token (found on %s).') % ('<a href="https://www.pivotaltracker.com/profile">pivotaltracker.com/profile</a>',)))
    project = forms.IntegerField(label=_('Project ID'),
        widget=forms.TextInput(attrs={'class': 'span3', 'placeholder': 'e.g. 639281'}),
        help_text=_('Enter your project numerical ID.'))


class PivotalTrackerPlugin(IssuePlugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry-pivotal'
    version = sentry_pivotal.VERSION
    description = "Integrate Pivotal Tracker stories by linking a project and account."
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-pivotal/issues'),
        ('Source', 'https://github.com/getsentry/sentry-pivotal'),
    ]

    slug = 'pivotal'
    title = _('Pivotal Tracker')
    conf_title = title
    conf_key = 'pivotal'
    project_conf_form = PivotalTrackerOptionsForm

    def is_configured(self, request, project, **kwargs):
        return all(self.get_option(k, project) for k in ('token', 'project'))

    def get_new_issue_title(self, **kwargs):
        return 'Add Story'

    def get_api_client(self, project):
        return pyvotal.PTracker(token=self.get_option('token', project))

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_api_client(group.project)

        story = client.Story()
        story.story_type = "bug"
        story.name = form_data['title']
        story.description = form_data['description']
        story.labels = "sentry"

        try:
            project = client.projects.get(self.get_option('project', group.project))
            story = project.stories.add(story)
        except Exception, e:
            raise forms.ValidationError(_('Error communicating with Pivotal Tracker: %s') % (unicode(e),))

        return story.id

    def get_issue_label(self, group, issue_id, **kwargs):
        return '#%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        project = self.get_option('project', group.project)

        return 'https://www.pivotaltracker.com/projects/%s#!/stories/%s' % (project, issue_id)
