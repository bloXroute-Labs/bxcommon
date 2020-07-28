import struct

from bxutils import logging

logger = logging.get_logger(__name__)


class PayloadElement:
    """payload element

    name (str): element block name
    structure (str): python struct packing format

    optionally provide decode,encode functions to be applied
    """
    def __init__(self, name, structure, default=None, decode=None, encode=None) -> None:
        self.name = name
        self.structure = structure
        self.default = default
        self.size = struct.calcsize(self.structure)
        self.decode = decode or (lambda x: x)
        self.encode = encode or (lambda x: x)
        self.block_name = None
        self.block_version = None
        self.offset = None


class PayloadBlock:
    """PayloadBlock element use to create a message block template from PayloadElements and PayloadBlocks

        Args:
            off (int): block offset
            name (str): block name
            version (int): block version
            * (PayloadElement/PayloadBlock)
    """
    def __init__(self, off, name, version, *args) -> None:
        elements = []
        self.name = name
        self.version = version
        self.start_offset = off
        self.off = off
        self.size = 0
        self.structure = ""
        self.elements = self._iter_input(elements, args, name, version)

    def _iter_input(self, elements, iterator, name, version):
        for item in iterator:
            if isinstance(item, PayloadElement):
                elements.append(item)
                # add context metadata for block element
                item.block_name = name
                item.block_version = version
                item.offset = self.off

                self.off += item.size
                self.size += item.size
            elif isinstance(item, PayloadBlock):
                self._iter_input(elements, item.elements, name=item.name, version=item.version)
            else:
                raise Exception("unknown input")
        return elements

    def build(self, buf, **kwargs):
        """build message buffer from kwargs"""
        for element in self.elements:
            s = kwargs.get(element.name, element.default)
            if element.offset + element.size > len(buf) and s is not None:
                logger.trace("cannot pack {},{} for {}.{} buffer too small {} {} {}",
                             s, element.name, element.block_name, element.block_version, len(buf), self.name,
                             self.version)
                continue
            if not s:
                continue
            if element.encode:
                s = element.encode(s)
            try:
                struct.pack_into(element.structure, buf, element.offset, s)
            except Exception as e:
                logger.debug("{} cannot pack {} into {} for {} {} {} {}",
                             repr(e), [s], element.structure, element.name, element.offset, len(buf),
                             [w.name for w in self.elements])
                raise Exception
        return buf

    def read(self, buf):
        """unpacks buffer contents into dictionary"""
        contents = dict()
        for element in self.elements:
            if element.offset + element.size > len(buf):
                logger.trace("cannot unpack {} for {}.{} buffer too small {}",
                             element.name, element.block_name, element.block_version, len(buf))
                contents[element.name] = None
                continue
            s, = struct.unpack_from(element.structure, buf, element.offset)
            if element.decode:
                s = element.decode(s)
            contents[element.name] = s
        return contents

    def __iter__(self):
        for item in self.elements:
            yield item
