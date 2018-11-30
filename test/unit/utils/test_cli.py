from bxcommon.utils import cli
import unittest
import json
import os


"""
Create temporary files in current directory for testing than remove them.
"""


class CliTest(unittest.TestCase):

    def test_read_valid_manifest_file(self):
        data = {"source_version": "v1.2.3.4"}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)
        self.assertEqual(cli.read_manifest(manifest_file.name), data)
        os.remove(manifest_file.name)

    def test_read_file_not_exist(self):
        with self.assertRaises(IOError):
            cli.read_manifest("manifest")

    def test_read_empty_manifest_file(self):
        manifest_file = open("MANIFEST.MF", "w+")
        with self.assertRaises(ValueError):
            cli.read_manifest(manifest_file.name)
        os.remove(manifest_file.name)

    def test_read_invalid_json_syntax_manifest_file(self):
        data = {"source_version": "dev0.0.0.1",}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)
            manifest_file.write(",")

        with self.assertRaises(ValueError):
            cli.read_manifest(manifest_file.name)

        os.remove(manifest_file.name)

    def test_read_missing_args_manifest_file(self):
        data = {"protocol_version": "1.2", "log_path": "../test.log"}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)

        with self.assertRaises(KeyError):
            cli.read_manifest(manifest_file.name)

        os.remove(manifest_file.name)

    def test_read_invalid_version_manifest_file(self):
        data = {"source_version": "v123.r.3.", "protocol_version": "1.2", "log_path": "../test.log"}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)

        with self.assertRaises(ValueError):
            cli.read_manifest(manifest_file.name)

        os.remove(manifest_file.name)

    def test_read_invalid_version_manifest_file2(self):
        data = {"source_version": "dev1.2..22", "protocol_version": "1.2", "log_path": "../test.log"}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)

        with self.assertRaises(ValueError):
            cli.read_manifest(manifest_file.name)

        os.remove(manifest_file.name)

    def test_read_invalid_version_manifest_file3(self):
        data = {"source_version": "source_version", "protocol_version": "1.2", "log_path": "../test.log"}
        with open("MANIFEST.MF", "w+") as manifest_file:
            json.dump(data, manifest_file)

        with self.assertRaises(ValueError):
            cli.read_manifest(manifest_file.name)

        os.remove(manifest_file.name)
