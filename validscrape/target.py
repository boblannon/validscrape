from . import utils
from validictory.validator import ValidationError


class Target(object):
    schema = {'title': 'Basic Target Class',
              'description': 'This should be replaced when subclassing'}

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.record = {'_meta': {}}

    def as_dict(self):
        return self.record

    def pre_save(self):
        pass

    def validate(self):
        validator = utils.DatetimeValidator(required_by_default=False)

        try:
            validator.validate(self.as_dict(), self.schema)
        except ValidationError as ve:
            raise ValidationError('validation of {} {} failed: {}'.format(
                self.__class__.__name__, self._form_jurisdiction, ve)
            )

    def __getitem__(self, key):
        return self.as_dict()[key]

    @property
    def document_id(self):
        return self.record['_meta'].get('document_id', 'N/A')

    @document_id.setter
    def document_id(self, document_id):
        if not self.record['_meta']:
            self.record['_meta'] = {}
        self.record['_meta']['document_id'] = document_id

    def __str__(self):
        return '{} id: {}'.format(self.name, self.document_id)

    @property
    def name(self):
        return self.schema['title']

    @property
    def description(self):
        return self.schema['description']
