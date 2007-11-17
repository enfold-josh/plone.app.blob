from zope.interface import implements
from Products.CMFPlone import PloneMessageFactory as _
from Products.Archetypes.atapi import FileWidget
from Products.validation import V_REQUIRED
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.field import ExtensionField
from plone.app.blob.field import BlobField


class ExtensionBlobField(ExtensionField, BlobField):
    """ derivative of blobfield for extending schemas """


class SchemaExtender(object):
    implements(ISchemaExtender)

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return [
            ExtensionBlobField('blob',
                required = True,
                primary = True,
                searchable = True,
                languageIndependent = True,
                validators = (('isNonEmptyFile', V_REQUIRED),
                              ('checkFileMaxSize', V_REQUIRED)),
                widget = FileWidget(label = _(u'label_file', default=u'File'),
                                    description=_(u''),
                                    show_content_type = False,))
        ]
