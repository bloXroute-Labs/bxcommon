from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional

from bxcommon import constants
from bxcommon.models.bdn_account_model_base import BdnAccountModelBase
from bxcommon.models.bdn_service_model_base import FeedServiceModelBase, BdnServiceModelBase
from bxcommon.models.bdn_service_model_config_base import BdnServiceModelConfigBase, BdnFeedServiceModelConfigBase, \
    BdnQuotaServiceModelConfigBase, BdnBasicServiceModel
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import model_loader
from bxutils.encoding import json_encoder


@dataclass
class BdnOldAccountModelBase:
    account_id: str
    logical_account_name: str
    certificate: str
    # TODO change expire_date to datetime type
    expire_date: str = constants.EPOCH_DATE
    tx_free: Optional[BdnServiceModelConfigBase] = None
    tx_paid: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    cloud_api: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    new_transaction_streaming: BdnServiceModelConfigBase = BdnServiceModelConfigBase()
    blockchain_protocol: Optional[str] = None
    blockchain_network: Optional[str] = None

    def is_account_valid(self) -> bool:
        today = datetime.utcnow().date()
        try:
            expire_date = date.fromisoformat(self.expire_date)
        except (KeyError, ValueError):
            return False

        return expire_date >= today


class TestAccountModelCompatibility(AbstractTestCase):
    def setUp(self) -> None:
        pass

    def test_new_transaction_streaming_account_setting(self):
        new_account_model = BdnAccountModelBase(
            "fake_id",
            "fake_name",
            "fake_cert",
            tx_paid=BdnQuotaServiceModelConfigBase(),
            cloud_api=BdnBasicServiceModel(),
            new_transaction_streaming=BdnFeedServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
                feed=FeedServiceModelBase(allow_filtering=True)
            )
        )
        new_account_model_json = json_encoder.to_json(new_account_model)
        old_account_model = model_loader.load_model_from_json(
            BdnOldAccountModelBase, new_account_model_json
        )
        self.assertTrue(new_account_model.new_transaction_streaming.is_service_valid())
        self.assertTrue(new_account_model.new_transaction_streaming.feed.allow_filtering)
        self.assertTrue(old_account_model.new_transaction_streaming.is_service_valid())
        self.assertFalse(old_account_model.cloud_api.is_service_valid())

    def test_cloud_api_account_setting(self):
        new_account_model = BdnAccountModelBase(
            "fake_id",
            "fake_name",
            "fake_cert",
            tx_paid=BdnQuotaServiceModelConfigBase(),
            cloud_api=BdnFeedServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
            ),
            new_transaction_streaming=BdnFeedServiceModelConfigBase()
        )
        new_account_model_json = json_encoder.to_json(new_account_model)
        old_account_model = model_loader.load_model_from_json(
            BdnOldAccountModelBase, new_account_model_json
        )
        self.assertTrue(new_account_model.cloud_api.is_service_valid())
        self.assertTrue(old_account_model.cloud_api.is_service_valid())
        self.assertFalse(old_account_model.new_transaction_streaming.is_service_valid())

    def test_quota_account_setting(self):
        new_account_model = BdnAccountModelBase(
            "fake_id",
            "fake_name",
            "fake_cert",
            tx_paid=BdnQuotaServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
                msg_quota=BdnServiceModelBase(limit=100)
            ),
            cloud_api=BdnFeedServiceModelConfigBase(),
            new_transaction_streaming=BdnFeedServiceModelConfigBase()
        )
        new_account_model_json = json_encoder.to_json(new_account_model)
        old_account_model = model_loader.load_model_from_json(
            BdnOldAccountModelBase, new_account_model_json
        )
        self.assertTrue(new_account_model.tx_paid.is_service_valid())
        self.assertTrue(old_account_model.tx_paid.is_service_valid())
        self.assertEqual(
            old_account_model.tx_paid.msg_quota.limit, new_account_model.tx_paid.msg_quota.limit
        )

    def test_old_account_model_to_new(self):
        old_account_model = BdnOldAccountModelBase(
            "fake_id",
            "fake_name",
            "fake_cert",
            tx_paid=BdnServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
                msg_quota=BdnServiceModelBase(limit=100)
            ),
            new_transaction_streaming=BdnServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
                permit=BdnServiceModelBase()
            ),
            cloud_api=BdnServiceModelConfigBase(
                expire_date=str(date.today() + timedelta(days=100)),
                permit=BdnServiceModelBase()
            )
        )
        old_account_model_json = json_encoder.to_json(old_account_model)
        new_account_model = model_loader.load_model_from_json(
            BdnAccountModelBase, old_account_model_json
        )
        self.assertEqual(
            old_account_model.tx_paid.is_service_valid(),
            new_account_model.tx_paid.is_service_valid(),
        )
        self.assertEqual(
            old_account_model.tx_paid.msg_quota.limit,
            new_account_model.tx_paid.msg_quota.limit,
        )
        self.assertEqual(
            old_account_model.cloud_api.is_service_valid(),
            new_account_model.cloud_api.is_service_valid(),
        )
        self.assertEqual(
            old_account_model.new_transaction_streaming.is_service_valid(),
            new_account_model.new_transaction_streaming.is_service_valid(),
        )

        # new account settings are not being set to default values, the SDN most verify that the payload is valid
        self.assertIsNone(new_account_model.new_transaction_streaming.feed)
        # self.assertTrue(new_account_model.new_transaction_streaming.feed.allow_filtering)
        # self.assertEqual(new_account_model.new_transaction_streaming.feed.available_fields, [])
