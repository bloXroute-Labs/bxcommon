from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxutils.encoding.json_encoder import Case


class JsonRpcRequestTest(AbstractTestCase):

    def test_serialize_camelCase(self):
        dict_request = JsonRpcRequest(
            "1",
            "methodname",
            {
                "param_name": "foo",
                "param2_name": "bar",
                "nested_param": {
                    "nested_param_name": "baz"
                },
                "normal_param": "qux"
            }
        )
        dict_json = dict_request.to_json(Case.CAMEL)
        self.assertEqual("foo", dict_json["params"]["paramName"])
        self.assertEqual("bar", dict_json["params"]["param2Name"])
        self.assertEqual("baz", dict_json["params"]["nestedParam"]["nestedParamName"])
        self.assertEqual("qux", dict_json["params"]["normalParam"])

        list_request = JsonRpcRequest(
            "1",
            "methodname",
            ["1", "2", "3"]
        )
        list_json = list_request.to_json(Case.CAMEL)
        self.assertEqual(["1", "2", "3"], list_json["params"])

        str_request = JsonRpcRequest(
            "1",
            "methodname",
            "str_stuff",
        )
        str_json = str_request.to_json(Case.CAMEL)
        self.assertEqual("strStuff", str_json["params"])
