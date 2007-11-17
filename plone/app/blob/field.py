from Acquisition import Implicit
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from ZPublisher.Iterators import filestream_iterator
from ZODB.blob import Blob
from persistent import Persistent

from Products.CMFCore.permissions import View
from Products.Archetypes.atapi import ObjectField, FileWidget
from Products.Archetypes.atapi import PrimaryFieldMarshaller
from Products.Archetypes.Registry import registerField
from Products.Archetypes.utils import contentDispositionHeader

from plone.i18n.normalizer.interfaces import IUserPreferredFileNameNormalizer
from plone.app.blob.interfaces import IBlobbable


class BlobMarshaller(PrimaryFieldMarshaller):

     def demarshall(self, instance, data, **kwargs):
         p = instance.getPrimaryField()
         file = kwargs.get('blob')
         mutator = p.getMutator(instance)
         mutator(file, **kwargs)


class BlobWrapper(Implicit, Persistent):
    """ persistent wrapper for a zodb blob, also holding some metadata """

    security  = ClassSecurityInfo()

    def __init__(self):
        self.blob = Blob()
        self.content_type = 'application/octet-stream'
        self.filename = None

    security.declarePrivate('getBlob')
    def getBlob(self):
        """ return the contained blob object """
        return self.blob

    security.declarePrivate('getIterator')
    def getIterator(self):
        """ return a filestream iterator object from the blob """
        return filestream_iterator(self.blob._current_filename(), 'rb')

    security.declareProtected(View, 'get_size')
    def get_size(self):
        """ return the size of the blob """
        f = self.blob.open('r') # XXX will barf if it's already open for "w"
        f.seek(0, 2)
        result = f.tell()
        f.close()
        return result

    security.declarePrivate('setContentType')
    def setContentType(self, value):
        """ set mimetype for this blob """
        self.content_type = value

    security.declarePublic('getContentType')
    def getContentType(self):
        """ return mimetype for this blob """
        return self.content_type

    security.declarePrivate('setFilename')
    def setFilename(self, value):
        """ set filename for this blob """
        self.filename = value

    security.declarePrivate('getFilename')
    def getFilename(self):
        """ return filename for this blob """
        return self.filename

InitializeClass(BlobWrapper)


class BlobField(ObjectField):
    """ file field implementation based on zodb blobs """

    _properties = ObjectField._properties.copy()
    _properties.update({
        'type' : 'blob',
        'default' : None,
        'primary' : False,
        'widget' : FileWidget,
        'default_content_type' : 'application/octet-stream',
    })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """ use input value to populate the blob and set the associated
            file name and mimetype """
        if value == "DELETE_FILE":
            super(BlobField, self).unset(instance, **kwargs)
            return
        if value is None:
            return
        # create a new blob instead of modifying the old one to
        # achieve copy-on-write semantics.
        blob = BlobWrapper()
        blobbable = IBlobbable(value)
        blobbable.feed(blob.getBlob())
        blob.setContentType(blobbable.mimetype())
        blob.setFilename(blobbable.filename())
        super(BlobField, self).set(instance, blob, **kwargs)

    security.declareProtected(View, 'download')
    def download(self, instance, REQUEST=None, RESPONSE=None):
        """ download the file (use default index_html) """
        return self.index_html(instance, REQUEST, RESPONSE, disposition='attachment')

    security.declareProtected(View, 'index_html')
    def index_html(self, instance, REQUEST=None, RESPONSE=None, disposition='inline'):
        """ make it directly viewable when entering the objects URL """
        if REQUEST is None:
            REQUEST = instance.REQUEST
        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE
        filename = self.getFilename(instance)
        if filename is not None:
            filename = IUserPreferredFileNameNormalizer(REQUEST).normalize(
                unicode(filename, instance.getCharset()))
            header_value = contentDispositionHeader(
                disposition=disposition,
                filename=filename)
            RESPONSE.setHeader("Content-disposition", header_value)
        blob = self.get(instance, raw=True)     # TODO: why 'raw'?
        RESPONSE.setHeader("Content-Length", blob.get_size())
        return blob.getIterator()

    security.declarePublic('get_size')
    def get_size(self, instance):
        """ return the size of the blob used for get_size in BaseObject """
        blob = self.get(instance)
        if blob is not None:
            return blob.get_size()
        else:
            return 0

    security.declarePublic('getContentType')
    def getContentType(self, instance, fromBaseUnit=True):
        """ return the mimetype associated with the blob data """
        blob = self.get(instance)
        if blob is not None:
            return blob.getContentType()
        else:
            return 'application/octet-stream'

    security.declarePrivate('getFilename')
    def getFilename(self, instance, fromBaseUnit=True):
        """ return the file name associated with the blob data """
        blob = self.get(instance)
        if blob is not None:
            return blob.getFilename()
        else:
            return None


registerField(BlobField, title='Blob',
              description='Used for storing files in blobs')
