import logging

import requests
from pylons import config

import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.lib.datapreview as datapreview

log = logging.getLogger(__name__)


def is_resource_to_large(url):
    url = h.url_for_static_or_external(url)
    try:
        resp = requests.head(url)
    except requests.exceptions.RequestException as e:
        print e
        return False
    length = int(resp.headers.get('content-length', 0))
    if not length:
        range = resp.headers.get('content-range')
        if not range:
            # unable to identify resource's size
            return False
        try:
            from_, to_ = range.split().pop().split('/').pop(0).split('-')
            length = int(to_) - int(from_)
        except Exception:
            return False
    size = length / 1024 / 1024
    max_size = int(config.get('pdf_view.max_preview_size', 1024))
    return size > max_size


class PdfView(p.SingletonPlugin):
    '''This extension views PDFs. '''

    if not p.toolkit.check_ckan_version('2.3'):
        raise p.toolkit.CkanVersionException(
            'This extension requires CKAN >= 2.3. If you are using a ' +
            'previous CKAN version the PDF viewer is included in the main ' +
            'CKAN repository.')

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.ITemplateHelpers)

    PDF = ['pdf', 'x-pdf', 'acrobat', 'vnd.pdf']
    proxy_is_enabled = False

    def info(self):
        return {'name': 'pdf_view',
                'title': 'PDF',
                'icon': 'file-text',
                'default_title': 'PDF',
                }

    def update_config(self, config):

        p.toolkit.add_public_directory(config, 'theme/public')
        p.toolkit.add_template_directory(config, 'theme/templates')
        p.toolkit.add_resource('theme/public', 'ckanext-pdfview')

    def configure(self, config):
        enabled = config.get('ckan.resource_proxy_enabled', False)
        self.proxy_is_enabled = enabled

    def can_view(self, data_dict):
        resource = data_dict['resource']
        format_lower = resource.get('format', '').lower()

        proxy_enabled = p.plugin_loaded('resource_proxy')
        same_domain = datapreview.on_same_domain(data_dict)

        if format_lower in self.PDF:
            return same_domain or proxy_enabled
        return False

    def view_template(self, context, data_dict):
        return 'pdf.html'

    # ITemplateHelpers

    def get_helpers(self):
        return dict(
            is_resource_to_large=is_resource_to_large
        )
