import six
import hashlib


class DropboxContentHasher(object):
    BLOCK_SIZE = 4 * 1024 * 1024

    def __init__(self):
        self._overall_hasher = hashlib.sha256()
        self._block_hasher = hashlib.sha256()
        self._block_pos = 0

        self.digest_size = self._overall_hasher.digest_size
        # hashlib classes also define 'block_size', but I don't know how people use that value

    def update(self, new_data):
        if self._overall_hasher is None:
            raise AssertionError(
                "can't use this object anymore; you already called digest()")

        assert isinstance(new_data, six.binary_type), (
            "Expecting a byte string, got {!r}".format(new_data))

        new_data_pos = 0
        while new_data_pos < len(new_data):
            if self._block_pos == self.BLOCK_SIZE:
                self._overall_hasher.update(self._block_hasher.digest())
                self._block_hasher = hashlib.sha256()
                self._block_pos = 0

            space_in_block = self.BLOCK_SIZE - self._block_pos
            part = new_data[new_data_pos:(new_data_pos + space_in_block)]
            self._block_hasher.update(part)

            self._block_pos += len(part)
            new_data_pos += len(part)

    def _finish(self):
        if self._overall_hasher is None:
            raise AssertionError(
                "can't use this object anymore; you already called digest() or hexdigest()")

        if self._block_pos > 0:
            self._overall_hasher.update(self._block_hasher.digest())
            self._block_hasher = None
        h = self._overall_hasher
        self._overall_hasher = None  # Make sure we can't use this object anymore.
        return h

    def digest(self):
        return self._finish().digest()

    def hexdigest(self):
        return self._finish().hexdigest()

    def copy(self):
        c = DropboxContentHasher.__new__(DropboxContentHasher)
        c._overall_hasher = self._overall_hasher.copy()
        c._block_hasher = self._block_hasher.copy()
        c._block_pos = self._block_pos
        return c
