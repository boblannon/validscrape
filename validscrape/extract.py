import logging

from io import IOBase, StringIO, BytesIO
from copy import deepcopy

from lxml import etree


class Extractor(object):

    def __init__(self, target_class):

        # logging convenience methods
        self.logger = logging.getLogger("extractor")
        self.info = self.logger.info
        self.debug = self.logger.debug
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical

        # the class of Target that this Extractor will extract
        self._target_class = target_class

    def do_extract(self, document, **kwargs):
        for obj in self.extract(document, **kwargs) or []:
            self.debug('{o}'.format(o=obj))
            if hasattr(obj, '__iter__'):
                for iterobj in obj:
                    yield obj
            else:
                yield obj

    def extract(self, document, **kwargs):
        raise NotImplementedError(self.__class__.__name__ +
                                  ' must provide a parse() method')


class SchemaExtractor(Extractor):

    def __init__(self, target_class):

        super().__init__(target_class)

        if self._target_class.schema['type'] != 'object':
            raise NotImplementedError('Sorry, only implemented for schemas'
                                      'where top level is object')

    def extract_location(self, container, path, prop, expect_array=False,
                         missing_okay=False):
        raise NotImplementedError(self.__class__.__name__ +
                                  ' must provide a method for extracting' +
                                  ' from path location')

    def extract_schema_node(self, schema_node, container, prop_name):
        # initial container is just the root node of the lxml etree
        if schema_node['type'] == 'array':
            return self.extract_array(
                deepcopy(schema_node),
                container,
                prop_name
            )

        elif schema_node['type'] == 'object':
            result = {}
            for subprop, subnode in schema_node['properties'].items():
                result[subprop] = self.extract_schema_node(
                    deepcopy(subnode),
                    container,
                    subprop
                )
            return result
        else:
            _parse_fct = schema_node['parser']
            e = self.extract_location(
                container,
                schema_node['path'],
                prop_name,
                missing_okay=schema_node.get('missing', False)
            )

            if e is not None:
                if e in ([], ''):
                    return _parse_fct(e)
                return _parse_fct(e)
            else:
                # TODO: should this return null if blank=True?
                return None

    def extract_array(self, schema_node, container, prop):
        result_array = []

        array_container = self.extract_location(
            container,
            schema_node['path'],
            prop,
            missing_okay=schema_node.get('missing', False)
        )

        items_schema = schema_node['items']
        even_odd = schema_node.get('even_odd', False)

        items = self.extract_location(
            array_container,
            items_schema['path'],
            prop,
            expect_array=True,
            missing_okay=items_schema.get('missing', False)
        )

        if even_odd:
            evens = items[::2]
            odds = items[1::2]
            all_props = items_schema['properties']
            even_props = [(p, s) for p, s in all_props.items()
                          if s['even_odd'] == 'even']
            odd_props = [(p, s) for p, s in all_props.items()
                         if s['even_odd'] == 'odd']
            for even, odd in zip(evens, odds):
                result = {}
                for prop_name, prop_node in even_props:
                    result.update({prop_name: self.extract_schema_node(
                        prop_node, even, prop_name)})
                for prop_name, prop_node in odd_props:
                    result.update({prop_name: self.extract_schema_node(
                        prop_node, odd, prop_name)})
                result_array.append(result)
        else:
            for item in items:
                result = self.extract_schema_node(items_schema, item, prop)
                if result:
                    result_array.append(result)
        return result_array

    def extract(self, document, **kwargs):

        target = self._target_class(**kwargs)
        for prop, schema_node in self._target_class.schema['properties'].items():
            if prop == "_meta":
                continue
            else:
                target.record[prop] = self.extract_schema_node(schema_node,
                                                               document,
                                                               prop)
        yield target


class XMLSchemaExtractor(SchemaExtractor):

    def ensure_filelike(self, document):
        if isinstance(document, str):
            _document = StringIO(document[:])
        if isinstance(document, bytes):
            _document = BytesIO(document[:])
        elif not isinstance(document, IOBase):
            raise Exception('document must be a string or file-like object')
        else:
            _document = document
        return _document

    def do_extract(self, document, **kwargs):
        _document = self.ensure_filelike(document)
        return super().do_extract(_document, **kwargs)

    def extract(self, document, parser=None, **kwargs):

        etree_root = etree.parse(document, parser=parser)

        try:
            object_path = self._target_class.schema['object_path']
        except KeyError:
            self.warning(
                'no object_path specified for {tm} schema, assuming doc root'.format(
                    tm=self._target_class.name)
            )
            object_path = '.'

        for object_root in etree_root.xpath(object_path):
            yield from super().extract(object_root)

    def extract_location(self, container, path, prop, expect_array=False,
                         missing_okay=False):
        found = container.xpath(path)
        if not found:
            if missing_okay:
                if expect_array:
                    return []
                else:
                    return None
            else:
                container_loc = container.getroottree().getpath(container)
                self.error("\n    ".join(
                           ["no match for property {n}",
                            "container: {c}",
                            "path: {p}\n"]
                           ).format(n=prop,
                                    c=container_loc,
                                    p=path)
                           )
        else:
            self.debug("\n    ".join(
                       ["match found for property {n}",
                        "container: {c}",
                        "path: {p}\n",
                        "found: {f}"]
                       ).format(n=prop,
                                c=container.getroottree().getpath(container),
                                p=path,
                                f=found)
                       )

            if expect_array:
                return found
            else:
                if len(found) > 1:
                    self.warning("\n    ".join(
                                 ["more than one result for {n}",
                                  "container: {c}",
                                  "path: {p}\n"]
                                 ).format(n=prop,
                                          c=container.getroottree().getpath(container),
                                          p=path)
                                 )
                    return found[0]
                else:
                    return found[0]


class HTMLSchemaExtractor(XMLSchemaExtractor):

    def extract(self, document, **kwargs):
        from lxml.html import HTMLParser
        html_parser = HTMLParser()

        yield from super().extract(document, parser=html_parser)
