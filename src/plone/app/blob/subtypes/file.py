from zope.interface import implements
from Products.CMFPlone import PloneMessageFactory as _
from Products.Archetypes.atapi import AnnotationStorage
from Products.Archetypes.atapi import FileWidget
from Products.validation import V_REQUIRED
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.field import ExtensionField
from plone.app.blob.field import BlobField, IndexMethodFix


class ExtensionBlobField(IndexMethodFix, ExtensionField, BlobField):
    """ derivative of blobfield for extending schemas """

    def set(self, instance, value, **kwargs):
        super(ExtensionBlobField, self).set(instance, value, **kwargs)
        self.fixAutoId(instance)


class SchemaExtender(object):
    implements(ISchemaExtender)

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return [
            ExtensionBlobField('file',
                required = True,
                primary = True,
                default = '',
                accessor = 'getFile',
                mutator = 'setFile',
                index_method = 'getIndexValue',
                languageIndependent = True,
                storage = AnnotationStorage(migrate=True),
                validators = (('isNonEmptyFile', V_REQUIRED),
                              ('checkFileMaxSize', V_REQUIRED)),
                widget = FileWidget(label = _(u'label_file', default=u'File'),
                                    description=_(u''),
                                    show_content_type = False,))
        ]

